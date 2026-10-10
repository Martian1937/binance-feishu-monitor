import os
import sys
import time
import threading

# 让 backend/ 下的 common / strategies 可被导入
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.util import log


def run():
    from common.config import ENABLE_TOP_GAINERS, MANUAL_SYMBOLS, TOP_N

    import common.config as config

    top = []
    source_label = "手动配置"
    if ENABLE_TOP_GAINERS:
        from common.api import fetch_top_gainers

        top = fetch_top_gainers(TOP_N)
        log(f"涨幅榜 Top{TOP_N}: {', '.join(top)}")
        source_label = f"Top{TOP_N}涨幅 + 配置"
    else:
        log("已关闭涨幅榜接口获取，仅监控 MANUAL_SYMBOLS")

    merged = list(set(top + MANUAL_SYMBOLS))
    merged.sort()
    config.SYMBOLS.clear()
    config.SYMBOLS.extend(merged)

    from surge.monitor import init_states, timer_loop

    from common.lark import send_lark

    init_states()
    send_lark("🟢 监控已启动", [
        f"**监控币种**\n{len(merged)} 个 ({source_label})",
        f"**触发条件**\n涨跌{config.THRESHOLD*100:.0f}% + 量能{config.VOLUME_MULTIPLIER:.1f}x + 前K方向",
        f"**K线周期**\n{config.INTERVAL}",
        f"**检查间隔**\n{config.CHECK_INTERVAL}秒",
    ], template="green")
    log("=" * 50)
    log(f"多币种永续合约价格监控启动 (API轮询): {len(merged)} 个币种 ({source_label})")
    log("=" * 50)

    checker = threading.Thread(target=timer_loop, daemon=True)
    checker.start()

    while True:
        time.sleep(60)


if __name__ == "__main__":
    run()
