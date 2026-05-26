import os
import time
import threading

from util import log
from api import fetch_kline, fetch_klines
from lark import send_lark
from strategies.ma_alignment import (
    check_alignment,
    check_ema_above_sma,
    build_ma_fields,
    CASE_LABELS,
    CASE_TEMPLATES,
)

LARK_WEBHOOK = os.environ.get("LARK_WEBHOOK_MA") or ""
EMAIL_ADDR = os.environ.get("EMAIL_MA") or ""
SYMBOLS = ["btcusdt", "ethusdt"]
MAX_KLINES = 80
CHECK_INTERVAL = 60
CROSS_COOLDOWN = 600
URGENT_COOLDOWN = 1800

states = {}
lock = threading.Lock()


def init_states():
    for sym in SYMBOLS:
        s = {
            "15m": fetch_klines(sym, MAX_KLINES, "15m") or [],
            "1h": fetch_klines(sym, MAX_KLINES, "1h") or [],
            "last_1h_case": 0,
            "last_cross_time": 0,
            "last_urgent_time": 0,
        }
        states[sym] = s
        log(f"[{sym}] 初始化: 15m({len(s['15m'])}根) 1h({len(s['1h'])}根)")


def _upsert(sym, interval):
    k = fetch_kline(sym, interval)
    if k is None:
        return None
    with lock:
        ks = states[sym][interval]
        if ks and ks[-1]["open_time"] == k["open_time"]:
            ks[-1] = k
        else:
            ks.append(k)
            if len(ks) > MAX_KLINES:
                ks.pop(0)
    return k


def check():
    now = time.time()
    for sym in SYMBOLS:
        for iv in ("15m", "1h"):
            _upsert(sym, iv)

        with lock:
            k15 = list(states[sym]["15m"])
            k1h = list(states[sym]["1h"])

        tag = sym.upper().replace("USDT", "")
        price_15 = k15[-1]["close"] if k15 else 0
        price_1h = k1h[-1]["close"] if k1h else 0

        r1 = check_alignment(k1h)
        r15 = check_alignment(k15)

        if r1:
            case_1h, det_1h = r1
            last = states[sym]["last_1h_case"]
            if case_1h != last:
                states[sym]["last_1h_case"] = case_1h
                fields = build_ma_fields(case_1h, det_1h, price_1h)
                send_lark(
                    f"⚠️ 1小时场景提醒 - {tag}",
                    fields,
                    template=CASE_TEMPLATES[case_1h],
                    webhook=LARK_WEBHOOK,
                )
                log(f"[{tag}] 1小时场景: 级别{case_1h}")

        if r1 and r15:
            case_15m, det_15m = r15
            if now - states[sym]["last_cross_time"] >= CROSS_COOLDOWN:
                states[sym]["last_cross_time"] = now
                send_lark(
                    f"🚨 交叉场景提醒 - {tag}",
                    [
                        f"**15分钟**\n{CASE_LABELS[case_15m]}",
                        f"**1小时**\n{CASE_LABELS[r1[0]]}",
                        f"**15分钟MA5**\n{det_15m['ma5']:.6f}",
                        f"**15分钟MA10**\n{det_15m['ma10']:.6f}",
                        f"**15分钟价格**\n{price_15:.6f} USDT",
                        f"**1小时价格**\n{price_1h:.6f} USDT",
                    ],
                    template="red",
                    webhook=LARK_WEBHOOK,
                )
                log(f"[{tag}] 交叉场景提醒")

                ema15 = check_ema_above_sma(k15)
                ema1h = check_ema_above_sma(k1h)
                if ema15 and ema1h and now - states[sym]["last_urgent_time"] >= URGENT_COOLDOWN:
                    states[sym]["last_urgent_time"] = now
                    send_lark(
                        f"🚨🚨 加急 - 交叉场景 EMA20>MA20 - {tag}",
                        [
                            f"**15分钟**\n{CASE_LABELS[case_15m]}",
                            f"**1小时**\n{CASE_LABELS[r1[0]]}",
                            f"**15分钟EMA20**\n超过MA20 ✅",
                            f"**1小时EMA20**\n超过MA20 ✅",
                            f"**15分钟价格**\n{price_15:.6f} USDT",
                            f"**1小时价格**\n{price_1h:.6f} USDT",
                            f"**建议**\n趋势确认，强烈关注！",
                        ],
                        template="red",
                        webhook=LARK_WEBHOOK,
                    )
                    log(f"[{tag}] 加急交叉场景提醒 (EMA20>MA20)")
                    log(f"[!] 需发送邮件至 {EMAIL_ADDR}: {tag} 15m/1h EMA20 > MA20")


def timer_loop():
    while True:
        time.sleep(CHECK_INTERVAL)
        try:
            check()
        except Exception as e:
            log(f"检查异常: {e}")


def run():
    init_states()
    if not LARK_WEBHOOK:
        log("LARK_WEBHOOK_MA 未配置，启动中止")
        return
    send_lark(
        "🟢 BTC/ETH MA摆正监控已启动",
        [
            "**监控币种**\nBTC, ETH",
            "**时间周期**\n15分钟 / 1小时",
            "**均线**\nMA5 / MA10 / MA20 / MA60",
            "**检查间隔**\n60秒",
        ],
        template="green",
        webhook=LARK_WEBHOOK,
    )
    log("=" * 50)
    log("BTC/ETH MA摆正监控已启动")
    log("=" * 50)

    checker = threading.Thread(target=timer_loop, daemon=True)
    checker.start()

    while True:
        time.sleep(60)


if __name__ == "__main__":
    run()
