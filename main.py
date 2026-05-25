import time
import threading

from util import log


def run():
    from config import SYMBOLS, TOP_N
    from api import fetch_top_gainers

    top = fetch_top_gainers(TOP_N)
    log(f"涨幅榜 Top{TOP_N}: {', '.join(top)}")

    merged = list(set(top + SYMBOLS))
    merged.sort()

    import config
    config.SYMBOLS = merged

    from monitor import init_states, timer_loop

    init_states()
    log("=" * 50)
    log(f"多币种永续合约价格监控启动 (API轮询): {len(merged)} 个币种 (Top{TOP_N}涨幅 + 配置)")
    log("=" * 50)

    checker = threading.Thread(target=timer_loop, daemon=True)
    checker.start()

    while True:
        time.sleep(60)


if __name__ == "__main__":
    run()
