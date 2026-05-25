import time
import threading

from config import SYMBOLS, THRESHOLD, CHECK_INTERVAL
from monitor import states, lock, init_states, timer_loop
from api import fetch_kline
from lark import send_lark
from util import log


def send_initial_status():
    for sym in SYMBOLS:
        try:
            kline = fetch_kline(sym)
            if kline is None:
                continue

            with lock:
                states[sym].update(kline)

            amplitude = (kline["high"] - kline["low"]) / kline["low"] * 100
            tag = sym.upper().replace("USDT", "")
            title = f"🟢 {tag}/USDT 监控已启动"
            fields = [
                f"**当前价格**\n{kline['close']:.6f} USDT",
                f"**当前K线最高价**\n{kline['high']:.6f} USDT",
                f"**当前K线最低价**\n{kline['low']:.6f} USDT",
                f"**当前K线振幅**\n{amplitude:.2f}%",
                f"**告警阈值**\n±{THRESHOLD*100:.0f}%",
                f"**检查间隔**\n{CHECK_INTERVAL}秒",
            ]
            send_lark(title, fields, template="green")
            log(f"[{tag}] 初始状态推送完成 | high: {kline['high']:.6f} | low: {kline['low']:.6f} | 振幅: {amplitude:.2f}%")
        except Exception as e:
            log(f"[{sym.upper()}] 初始状态推送失败: {e}")


def run():
    init_states()
    log("=" * 50)
    log(f"多币种永续合约价格监控启动 (API轮询): {', '.join(s.upper() for s in SYMBOLS)}")
    log("=" * 50)

    send_initial_status()

    checker = threading.Thread(target=timer_loop, daemon=True)
    checker.start()

    while True:
        time.sleep(60)


if __name__ == "__main__":
    run()
