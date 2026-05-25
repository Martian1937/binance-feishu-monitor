import time
import threading
from datetime import datetime

from config import SYMBOLS, THRESHOLD, ALERT_COOLDOWN
from api import fetch_kline
from lark import send_lark
from util import log


states = {}
lock = threading.Lock()


def init_states():
    for sym in SYMBOLS:
        states[sym] = {
            "open": None,
            "close": None,
            "high": None,
            "low": None,
            "last_drop_alert": 0,
            "last_rise_alert": 0,
        }


def check_price():
    now = time.time()
    for sym in SYMBOLS:
        kline = fetch_kline(sym)
        if kline is None:
            continue

        with lock:
            s = states[sym]
            s["open"] = kline["open"]
            s["close"] = kline["close"]
            s["high"] = kline["high"]
            s["low"] = kline["low"]
            high_p = kline["high"]
            low_p = kline["low"]
            close_p = kline["close"]
            open_p = kline["open"]
            last_drop = s["last_drop_alert"]
            last_rise = s["last_rise_alert"]

        tag = sym.upper().replace("USDT", "")

        drop_pct = (high_p - close_p) / high_p
        rise_pct = (close_p - low_p) / low_p
        log(f"[{tag}] 定时检查 | 开盘: {open_p:.6f} | 最高: {high_p:.6f} | 最低: {low_p:.6f} | 当前: {close_p:.6f} | 从高点跌: {drop_pct*100:.2f}% | 从低点涨: {rise_pct*100:.2f}%")

        if drop_pct >= THRESHOLD:
            if now - last_drop < ALERT_COOLDOWN:
                log(f"[{tag}] 跌幅已触发，但在冷却期内，跳过发送")
            else:
                with lock:
                    states[sym]["last_drop_alert"] = now
                title = f"📉 {tag}/USDT 当前K线从最高点下跌 -{drop_pct*100:.2f}%"
                fields = [
                    f"**当前价格**\n{close_p:.6f} USDT",
                    f"**K线最高价**\n{high_p:.6f} USDT",
                    f"**K线最低价**\n{low_p:.6f} USDT",
                    f"**从最高点跌幅**\n-{drop_pct*100:.2f}%",
                    f"**检测时间**\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    f"**K线周期**\n15分钟",
                ]
                send_lark(title, fields, template="red")

        if rise_pct >= THRESHOLD:
            if now - last_rise < ALERT_COOLDOWN:
                log(f"[{tag}] 涨幅已触发，但在冷却期内，跳过发送")
            else:
                with lock:
                    states[sym]["last_rise_alert"] = now
                title = f"📈 {tag}/USDT 当前K线从最低点上涨 +{rise_pct*100:.2f}%"
                fields = [
                    f"**当前价格**\n{close_p:.6f} USDT",
                    f"**K线最低价**\n{low_p:.6f} USDT",
                    f"**K线最高价**\n{high_p:.6f} USDT",
                    f"**从最低点涨幅**\n+{rise_pct*100:.2f}%",
                    f"**检测时间**\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    f"**K线周期**\n15分钟",
                ]
                send_lark(title, fields, template="orange")


def timer_loop():
    from config import CHECK_INTERVAL
    while True:
        time.sleep(CHECK_INTERVAL)
        try:
            check_price()
        except Exception as e:
            log(f"检查异常: {e}")
