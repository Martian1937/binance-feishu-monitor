import time
import threading

from util import log


def run():
    from config import MANUAL_SYMBOLS, TOP_N
    from api import fetch_top_gainers

    import config

    top = fetch_top_gainers(TOP_N)
    log(f"涨幅榜 Top{TOP_N}: {', '.join(top)}")

    merged = list(set(top + MANUAL_SYMBOLS))
    merged.sort()
    config.SYMBOLS.clear()
    config.SYMBOLS.extend(merged)

    from monitor import init_states, timer_loop

    from lark import send_lark

    init_states()
    send_lark("🟢 监控已启动", [
        f"**监控币种**\n{len(merged)} 个 (Top{TOP_N}涨幅 + 配置)",
        f"**触发条件**\n涨跌{config.THRESHOLD*100:.0f}% + 量能{config.VOLUME_MULTIPLIER:.1f}x + 前K方向",
        f"**K线周期**\n{config.INTERVAL}",
        f"**检查间隔**\n{config.CHECK_INTERVAL}秒",
    ], template="green")
    log("=" * 50)
    log(f"多币种永续合约价格监控启动 (API轮询): {len(merged)} 个币种 (Top{TOP_N}涨幅 + 配置)")
    log("=" * 50)

    checker = threading.Thread(target=timer_loop, daemon=True)
    checker.start()

    while True:
        time.sleep(60)


if __name__ == "__main__":
    run()
