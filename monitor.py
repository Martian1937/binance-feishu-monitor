import time
import threading

from config import SYMBOLS
from api import fetch_kline, fetch_klines
from lark import send_lark
from util import log
from strategies import STRATEGIES


MAX_KLINES = 20
states = {}
lock = threading.Lock()


def init_states():
    for sym in SYMBOLS:
        klines = fetch_klines(sym, MAX_KLINES) or []
        state = {"klines": klines}
        for st in STRATEGIES:
            state[st.name] = st.init_state()
        states[sym] = state


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


def check_price():
    now = time.time()
    for sym in SYMBOLS:
        kline = _upsert_latest(sym)
        if kline is None:
            continue

        with lock:
            s = states[sym]
            klines = s["klines"]

        close_p = kline["close"]
        log(f"[{sym.upper().replace('USDT', '')}] {close_p:.6f}")

        for st in STRATEGIES:
            try:
                alert = st.check(sym, kline, klines, s[st.name], now)
            except Exception as e:
                log(f"策略 [{st.name}] 异常: {e}")
                continue

            if alert is None:
                continue

            send_lark(alert["title"], alert["fields"], template=alert["template"])
            log(f"[{alert['tag']}] 策略 [{st.name}] 触发: {alert['title']}")


def refresh_symbols():
    from config import ENABLE_TOP_GAINERS, SYMBOLS, MANUAL_SYMBOLS, TOP_N

    top = []
    if ENABLE_TOP_GAINERS:
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
                state = {"klines": klines}
                for st in STRATEGIES:
                    state[st.name] = st.init_state()
                states[sym] = state
        stale = [sym for sym in list(states) if sym not in SYMBOLS]
        for sym in stale:
            del states[sym]
    if ENABLE_TOP_GAINERS:
        log(f"涨幅榜已刷新: {len(SYMBOLS)} 个币种")
    else:
        log(f"手动监控币种已同步: {len(SYMBOLS)} 个币种")


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
