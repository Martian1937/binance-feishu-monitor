import json
import os
import threading
import time
from datetime import datetime

import requests

from config import LARK_WEBHOOK
from lark import send_lark
from util import log


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 点位提醒使用独立的飞书 Webhook，未配置时回退到主监控的 LARK_WEBHOOK
LARK_WEBHOOK_PRICE = os.environ.get("LARK_WEBHOOK_PRICE") or LARK_WEBHOOK

# 价格源可选: binance_vision / binance / okx
PRICE_SOURCE = os.environ.get("PRICE_SOURCE", "binance_vision")
PRICE_POLL_INTERVAL = int(os.environ.get("PRICE_POLL_INTERVAL", "15"))
PRICE_ALERT_COOLDOWN = int(os.environ.get("PRICE_ALERT_COOLDOWN", "600"))
PRICE_DATA_FILE = os.environ.get("PRICE_DATA_FILE") or os.path.join(BASE_DIR, "price_alerts.json")
PRICE_SERVER_HOST = os.environ.get("PRICE_SERVER_HOST", "127.0.0.1")
PRICE_SERVER_PORT = int(os.environ.get("PRICE_SERVER_PORT", "8090"))

PRICE_SOURCES = {
    "binance_vision": {
        "kind": "binance",
        "url": "https://data-api.binance.vision/api/v3/ticker/price",
    },
    "binance": {
        "kind": "binance",
        "url": "https://api.binance.com/api/v3/ticker/price",
    },
    "okx": {
        "kind": "okx",
        "url": "https://www.okx.com/api/v5/market/ticker",
    },
}

_working_source = None


def normalize_symbol(raw):
    s = "".join((raw or "").split()).upper()
    s = s.replace("/", "").replace("-", "").replace("_", "")
    if not s:
        return ""
    if not s.endswith("USDT"):
        s += "USDT"
    return s


def _fetch_once(source, canonical):
    cfg = PRICE_SOURCES[source]
    try:
        if cfg["kind"] == "binance":
            resp = requests.get(cfg["url"], params={"symbol": canonical}, timeout=10)
            data = resp.json()
            return float(data["price"])

        inst_id = canonical[:-4] + "-USDT" if canonical.endswith("USDT") else canonical
        resp = requests.get(cfg["url"], params={"instId": inst_id}, timeout=10)
        data = resp.json()
        if str(data.get("code")) != "0" or not data.get("data"):
            return None
        return float(data["data"][0]["last"])
    except Exception:
        return None


def fetch_price(canonical):
    """按优先级尝试价格源，失败自动切换，成功后记住可用源。"""
    global _working_source
    order = [PRICE_SOURCE] + [s for s in PRICE_SOURCES if s != PRICE_SOURCE]
    if _working_source:
        order = [_working_source] + [s for s in order if s != _working_source]
    for source in order:
        price = _fetch_once(source, canonical)
        if price is not None:
            _working_source = source
            return price
    return None


def _sanitize_levels(raw_levels):
    levels = []
    for value in raw_levels or []:
        try:
            value = float(value)
        except (TypeError, ValueError):
            continue
        if value <= 0 or value in levels:
            continue
        levels.append(value)
    levels.sort()
    return levels


class PriceAlertStore:
    def __init__(self, data_file=PRICE_DATA_FILE):
        self.data_file = data_file
        self.lock = threading.Lock()
        self.alerts = []
        self.runtime = {}
        self.load()

    def _defaults(self):
        return [
            {"symbol": "PYTHUSDT", "levels": [0.88, 1.0, 1.25], "enabled": True},
            {"symbol": "ASTERUSDT", "levels": [], "enabled": True},
        ]

    def _sanitize(self, raw):
        out = []
        seen = set()
        for item in raw or []:
            sym = normalize_symbol(item.get("symbol", ""))
            if not sym or sym in seen:
                continue
            seen.add(sym)
            out.append({
                "symbol": sym,
                "levels": _sanitize_levels(item.get("levels")),
                "enabled": bool(item.get("enabled", True)),
            })
        out.sort(key=lambda x: x["symbol"])
        return out

    def load(self):
        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.alerts = self._sanitize(data.get("alerts"))
        except FileNotFoundError:
            self.alerts = self._defaults()
            self.save()
        except Exception as e:
            log(f"点位提醒配置读取失败，使用默认配置: {e}")
            self.alerts = self._defaults()
        self._sync_runtime()

    def save(self):
        tmp = self.data_file + ".tmp"
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump({"alerts": self.alerts}, f, ensure_ascii=False, indent=2)
            os.replace(tmp, self.data_file)
        except Exception as e:
            log(f"点位提醒配置保存失败: {e}")

    def _sync_runtime(self):
        for alert in self.alerts:
            rt = self.runtime.setdefault(alert["symbol"], {"last_price": None, "level_state": {}})
            for level in alert["levels"]:
                rt["level_state"].setdefault(level, {"above": None, "last_alert": 0.0})

    def get(self, symbol):
        with self.lock:
            alert = next((x for x in self.alerts if x["symbol"] == symbol), None)
            if alert is None:
                return None
            rt = self.runtime.get(symbol, {})
            return {
                "symbol": alert["symbol"],
                "levels": list(alert["levels"]),
                "enabled": alert["enabled"],
                "last_price": rt.get("last_price"),
            }

    def snapshot(self):
        with self.lock:
            out = []
            for alert in self.alerts:
                rt = self.runtime.get(alert["symbol"], {})
                out.append({
                    "symbol": alert["symbol"],
                    "levels": list(alert["levels"]),
                    "enabled": alert["enabled"],
                    "last_price": rt.get("last_price"),
                })
            return out

    def upsert(self, symbol, levels=None, enabled=True):
        sym = normalize_symbol(symbol)
        if not sym:
            return None
        with self.lock:
            existing = next((x for x in self.alerts if x["symbol"] == sym), None)
            if levels is None:
                levels = existing["levels"] if existing else []
            levels = _sanitize_levels(levels)
            if existing:
                existing["levels"] = levels
                existing["enabled"] = bool(enabled)
            else:
                self.alerts.append({"symbol": sym, "levels": levels, "enabled": bool(enabled)})
            self.alerts.sort(key=lambda x: x["symbol"])
            self._sync_runtime()
            self.save()
            rt = self.runtime.get(sym, {})
            return {
                "symbol": sym,
                "levels": list(levels),
                "enabled": bool(enabled),
                "last_price": rt.get("last_price"),
            }

    def remove(self, symbol):
        sym = normalize_symbol(symbol)
        with self.lock:
            before = len(self.alerts)
            self.alerts = [x for x in self.alerts if x["symbol"] != sym]
            self.runtime.pop(sym, None)
            if len(self.alerts) == before:
                return False
            self.save()
            return True

    def check(self):
        now = time.time()
        with self.lock:
            symbols = [x["symbol"] for x in self.alerts if x["enabled"]]
        for sym in symbols:
            price = fetch_price(sym)
            if price is None:
                log(f"[{sym}] 点位行情获取失败，跳过本轮")
                continue
            self._on_price(sym, price, now)

    def _on_price(self, sym, price, now):
        with self.lock:
            alert = next((x for x in self.alerts if x["symbol"] == sym), None)
            if alert is None or not alert["enabled"]:
                return
            rt = self.runtime.setdefault(sym, {"last_price": None, "level_state": {}})
            tag = sym[:-4] if sym.endswith("USDT") else sym
            for level in alert["levels"]:
                st = rt["level_state"].setdefault(level, {"above": None, "last_alert": 0.0})
                new_above = price >= level
                if st["above"] is not None and new_above != st["above"]:
                    if now - st["last_alert"] >= PRICE_ALERT_COOLDOWN:
                        self._alert(tag, price, level, new_above)
                        st["last_alert"] = now
                st["above"] = new_above
            rt["last_price"] = price

    def _alert(self, tag, price, level, upward):
        pct = (price - level) / level * 100 if level else 0
        if upward:
            title = f"🚀 {tag} 向上突破 {level:g} USDT"
            template = "orange"
            direction = "向上突破"
        else:
            title = f"📉 {tag} 向下跌破 {level:g} USDT"
            template = "purple"
            direction = "向下跌破"
        send_lark(
            title,
            [
                f"**当前价格**\n{price:.6f} USDT",
                f"**触发价位**\n{level:g} USDT",
                f"**方向**\n{direction}",
                f"**偏离**\n{pct:+.2f}%",
                f"**检测时间**\n{datetime.now().strftime('%H:%M:%S')}",
            ],
            template=template,
            webhook=LARK_WEBHOOK_PRICE,
        )
        log(f"[{tag}] 点位提醒触发: {direction} {level:g} (当前 {price:.6f})")


def poll_loop(store):
    while True:
        try:
            store.check()
        except Exception as e:
            log(f"点位检查异常: {e}")
        time.sleep(PRICE_POLL_INTERVAL)
