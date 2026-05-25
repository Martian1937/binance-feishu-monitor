import time
import threading
from datetime import datetime

from config import SYMBOLS, THRESHOLD, ALERT_COOLDOWN, VOLUME_WINDOW, VOLUME_MULTIPLIER
from api import fetch_kline, fetch_klines
from lark import send_lark
from util import log


MAX_KLINES = 20
states = {}
lock = threading.Lock()


def init_states():
    for sym in SYMBOLS:
        klines = fetch_klines(sym, MAX_KLINES) or []
        states[sym] = {
            "klines": klines,
            "last_rise_alert": 0,
            "last_drop_alert": 0,
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


def _send_alert(tag, direction, pct, kline, vol_ratio, klines):
    is_rise = direction == "rise"
    dir_cn = "拉升" if is_rise else "下跌"
    prefix = "+" if is_rise else "-"
    candle_cn = "阳" if is_rise else "阴"
    template = "orange" if is_rise else "purple"
    title = f"🔥 {tag} 放量{dir_cn} {prefix}{pct*100:.2f}%"
    fields = [
        f"**当前价格**\n{kline['close']:.6f} USDT",
        f"**K线最低**\n{kline['low']:.6f} USDT",
        f"**K线最高**\n{kline['high']:.6f} USDT",
        f"**{dir_cn}幅度**\n{prefix}{pct*100:.2f}%",
        f"**成交量**\n{kline['volume']:.0f}（{vol_ratio:.1f}倍均值）",
        f"**连续{candle_cn}线**\n{len(klines) - 2}根+（含本根）",
        f"**检测时间**\n{datetime.now().strftime('%H:%M:%S')}",
        f"**K线周期**\n15分钟",
    ]
    send_lark(title, fields, template=template)


def check_price():
    now = time.time()
    for sym in SYMBOLS:
        kline = _upsert_latest(sym)
        if kline is None:
            continue

        with lock:
            s = states[sym]
            klines = s["klines"]

        tag = sym.upper().replace("USDT", "")
        high_p = kline["high"]
        low_p = kline["low"]
        close_p = kline["close"]
        vol = kline["volume"]

        rise_pct = (close_p - low_p) / low_p if low_p else 0
        drop_pct = (high_p - close_p) / high_p if high_p else 0
        log(f"[{tag}] {close_p:.6f} V:{vol:.0f} | 涨:{rise_pct*100:.2f}% 跌:{drop_pct*100:.2f}%")

        avg_vol = _avg_volume(klines, VOLUME_WINDOW)
        if avg_vol <= 0:
            continue
        vol_ok = vol >= avg_vol * VOLUME_MULTIPLIER
        prev_bull = len(klines) >= 2 and klines[-2]["close"] > klines[-2]["open"]
        prev_bear = len(klines) >= 2 and klines[-2]["close"] < klines[-2]["open"]

        # --- 上涨检测 ---
        rise_ok = rise_pct >= THRESHOLD and vol_ok and prev_bull
        # --- 下跌检测 ---
        drop_ok = drop_pct >= THRESHOLD and vol_ok and prev_bear

        if not rise_ok and not drop_ok:
            continue

        with lock:
            s = states[sym]
            last_rise = s["last_rise_alert"]
            last_drop = s["last_drop_alert"]

        if rise_ok and now - last_rise >= ALERT_COOLDOWN:
            with lock:
                states[sym]["last_rise_alert"] = now
            _send_alert(tag, "rise", rise_pct, kline, vol / avg_vol, klines)
        elif rise_ok:
            log(f"[{tag}] 放量拉升已触发，冷却中")

        if drop_ok and now - last_drop >= ALERT_COOLDOWN:
            with lock:
                states[sym]["last_drop_alert"] = now
            _send_alert(tag, "drop", drop_pct, kline, vol / avg_vol, klines)
        elif drop_ok:
            log(f"[{tag}] 放量下跌已触发，冷却中")


def refresh_symbols():
    from config import SYMBOLS, MANUAL_SYMBOLS, TOP_N
    from api import fetch_top_gainers
    top = fetch_top_gainers(TOP_N)
    if not top:
        return
    merged = list(set(top + MANUAL_SYMBOLS))
    merged.sort()
    SYMBOLS[:] = merged
    with lock:
        for sym in SYMBOLS:
            if sym not in states:
                klines = fetch_klines(sym, MAX_KLINES) or []
                states[sym] = {"klines": klines, "last_rise_alert": 0, "last_drop_alert": 0}
        stale = [sym for sym in list(states) if sym not in SYMBOLS]
        for sym in stale:
            del states[sym]
    log(f"涨幅榜已刷新: {len(SYMBOLS)} 个币种")


def timer_loop():
    from config import CHECK_INTERVAL, REFRESH_INTERVAL
    last_refresh = 0
    while True:
        time.sleep(CHECK_INTERVAL)
        now = time.time()
        if now - last_refresh >= REFRESH_INTERVAL:
            refresh_symbols()
            last_refresh = now
        try:
            check_price()
        except Exception as e:
            log(f"检查异常: {e}")
