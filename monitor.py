import time
import threading
from datetime import datetime

from config import SYMBOLS, THRESHOLD, ALERT_COOLDOWN, TREND_KLINES, TREND_THRESHOLD, VOLUME_WINDOW, VOLUME_MULTIPLIER
from api import fetch_kline, fetch_klines
from lark import send_lark
from util import log


MAX_KLINES = max(TREND_KLINES, VOLUME_WINDOW) + 5
states = {}
lock = threading.Lock()


def init_states():
    for sym in SYMBOLS:
        klines = fetch_klines(sym, MAX_KLINES) or []
        states[sym] = {
            "klines": klines,
            "last_rise_alert": 0,
            "last_trend_alert": 0,
            "last_volume_alert": 0,
        }


def _upsert_latest(sym):
    k = fetch_kline(sym)
    if k is None:
        return None
    with lock:
        s = states[sym]
        ks = s["klines"]
        if ks and ks[-1]["open_time"] == k["open_time"]:
            ks[-1] = k
        else:
            ks.append(k)
            if len(ks) > MAX_KLINES:
                ks.pop(0)
    return k


def _avg_volume(klines, n):
    closed = [k for k in klines if k["close"] != k["open"]]
    recent = closed[-n:] if n <= len(closed) else closed
    if not recent:
        return 0
    return sum(k["volume"] for k in recent) / len(recent)


def check_price():
    now = time.time()
    for sym in SYMBOLS:
        kline = _upsert_latest(sym)
        if kline is None:
            continue

        with lock:
            s = states[sym]
            klines = s["klines"]
            last_rise = s["last_rise_alert"]
            last_trend = s["last_trend_alert"]
            last_vol = s["last_volume_alert"]

        tag = sym.upper().replace("USDT", "")
        open_p = kline["open"]
        high_p = kline["high"]
        low_p = kline["low"]
        close_p = kline["close"]
        vol = kline["volume"]

        drop_pct = (high_p - close_p) / high_p if high_p else 0
        rise_pct = (close_p - low_p) / low_p if low_p else 0
        log(f"[{tag}] 检查 | O:{open_p:.6f} H:{high_p:.6f} L:{low_p:.6f} C:{close_p:.6f} V:{vol:.2f} | 涨:{rise_pct*100:.2f}% 跌:{drop_pct*100:.2f}%")

        # --- 1) 单K线涨幅 ---
        if rise_pct >= THRESHOLD:
            if now - last_rise >= ALERT_COOLDOWN:
                with lock:
                    states[sym]["last_rise_alert"] = now
                title = f"📈 {tag} 单K线拉升 +{rise_pct*100:.2f}%"
                fields = [
                    f"**当前价格**\n{close_p:.6f} USDT",
                    f"**K线最低**\n{low_p:.6f} USDT",
                    f"**K线最高**\n{high_p:.6f} USDT",
                    f"**拉升幅度**\n+{rise_pct*100:.2f}%",
                    f"**检测时间**\n{datetime.now().strftime('%H:%M:%S')}",
                    f"**K线周期**\n1分钟",
                ]
                send_lark(title, fields, template="orange")
            else:
                log(f"[{tag}] 涨幅触发，冷却中")

        # --- 2) 多K线趋势 ---
        if len(klines) >= TREND_KLINES:
            trend_open = klines[-TREND_KLINES]["open"]
            trend_close = klines[-1]["close"]
            trend_pct = (trend_close - trend_open) / trend_open if trend_open else 0
            if trend_pct >= TREND_THRESHOLD:
                if now - last_trend >= ALERT_COOLDOWN:
                    with lock:
                        states[sym]["last_trend_alert"] = now
                    title = f"📊 {tag} 趋势上涨 +{trend_pct*100:.2f}%（{TREND_KLINES}根K线）"
                    fields = [
                        f"**当前价格**\n{trend_close:.6f} USDT",
                        f"**{TREND_KLINES}根前开盘**\n{trend_open:.6f} USDT",
                        f"**累计涨幅**\n+{trend_pct*100:.2f}%",
                        f"**检测时间**\n{datetime.now().strftime('%H:%M:%S')}",
                        f"**K线周期**\n1分钟",
                    ]
                    send_lark(title, fields, template="blue")
                else:
                    log(f"[{tag}] 趋势触发，冷却中")

        # --- 3) 成交量放大 ---
        avg_vol = _avg_volume(klines, VOLUME_WINDOW)
        if avg_vol > 0 and vol > avg_vol * VOLUME_MULTIPLIER:
            vol_ratio = vol / avg_vol
            if now - last_vol >= ALERT_COOLDOWN:
                with lock:
                    states[sym]["last_volume_alert"] = now
                title = f"🔊 {tag} 成交量异常（{vol_ratio:.1f}倍）"
                fields = [
                    f"**当前价格**\n{close_p:.6f} USDT",
                    f"**当前成交量**\n{vol:.2f}",
                    f"**近{VOLUME_WINDOW}根均值**\n{avg_vol:.2f}",
                    f"**放大倍数**\n{vol_ratio:.1f}x",
                    f"**检测时间**\n{datetime.now().strftime('%H:%M:%S')}",
                    f"**K线周期**\n1分钟",
                ]
                send_lark(title, fields, template="purple")
            else:
                log(f"[{tag}] 成交量触发，冷却中")


def timer_loop():
    from config import CHECK_INTERVAL
    while True:
        time.sleep(CHECK_INTERVAL)
        try:
            check_price()
        except Exception as e:
            log(f"检查异常: {e}")
