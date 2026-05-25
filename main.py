import time
import threading

from config import SYMBOLS
from monitor import init_states, timer_loop
from util import log


def run():
    init_states()
    log("=" * 50)
    log(f"多币种永续合约价格监控启动 (API轮询): {', '.join(s.upper() for s in SYMBOLS)}")
    log("=" * 50)

    checker = threading.Thread(target=timer_loop, daemon=True)
    checker.start()

    while True:
        time.sleep(60)


if __name__ == "__main__":
    run()
