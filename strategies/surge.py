from datetime import datetime

from config import THRESHOLD, VOLUME_WINDOW, VOLUME_MULTIPLIER
from .base import BaseStrategy


def _fire(pct):
    n = 1 if pct < 0.05 else 2 if pct <= 0.10 else 3
    return "🔥" * n


def _avg_volume(klines, n):
    closed = [k for k in klines if k["close"] != k["open"]]
    recent = closed[-n:] if n <= len(closed) else closed
    if not recent:
        return 0
    return sum(k["volume"] for k in recent) / len(recent)


class SurgeStrategy(BaseStrategy):
    name = "surge"
    cooldown = 300

    def init_state(self):
        return {"last_rise_alert": 0, "last_drop_alert": 0}

    def check(self, sym, kline, klines, state, now):
        high_p = kline["high"]
        low_p = kline["low"]
        close_p = kline["close"]
        vol = kline["volume"]

        rise_pct = (close_p - low_p) / low_p if low_p else 0
        drop_pct = (high_p - close_p) / high_p if high_p else 0

        avg_vol = _avg_volume(klines, VOLUME_WINDOW)
        if avg_vol <= 0:
            return None
        vol_ok = vol >= avg_vol * VOLUME_MULTIPLIER
        prev_bull = len(klines) >= 2 and klines[-2]["close"] > klines[-2]["open"]
        prev_bear = len(klines) >= 2 and klines[-2]["close"] < klines[-2]["open"]

        rise_ok = rise_pct >= THRESHOLD and vol_ok and prev_bull
        drop_ok = drop_pct >= THRESHOLD and vol_ok and prev_bear

        if not rise_ok and not drop_ok:
            return None

        tag = sym.upper().replace("USDT", "")

        if rise_ok and now - state["last_rise_alert"] >= self.cooldown:
            state["last_rise_alert"] = now
            vol_ratio = vol / avg_vol
            return self.build_alert(
                tag=tag,
                title=f"{_fire(rise_pct)} {tag} 放量拉升 +{rise_pct*100:.2f}%",
                fields=[
                    f"**当前价格**\n{close_p:.6f} USDT",
                    f"**K线最低**\n{low_p:.6f} USDT",
                    f"**K线最高**\n{high_p:.6f} USDT",
                    f"**拉升幅度**\n+{rise_pct*100:.2f}%",
                    f"**成交量**\n{vol:.0f}（{vol_ratio:.1f}倍均值）",
                    f"**连续阳线**\n{len(klines) - 2}根+（含本根）",
                    f"**检测时间**\n{datetime.now().strftime('%H:%M:%S')}",
                    f"**K线周期**\n15分钟",
                ],
                template="orange",
            )

        if drop_ok and now - state["last_drop_alert"] >= self.cooldown:
            state["last_drop_alert"] = now
            vol_ratio = vol / avg_vol
            return self.build_alert(
                tag=tag,
                title=f"{_fire(drop_pct)} {tag} 放量下跌 -{drop_pct*100:.2f}%",
                fields=[
                    f"**当前价格**\n{close_p:.6f} USDT",
                    f"**K线最低**\n{low_p:.6f} USDT",
                    f"**K线最高**\n{high_p:.6f} USDT",
                    f"**下跌幅度**\n-{drop_pct*100:.2f}%",
                    f"**成交量**\n{vol:.0f}（{vol_ratio:.1f}倍均值）",
                    f"**连续阴线**\n{len(klines) - 2}根+（含本根）",
                    f"**检测时间**\n{datetime.now().strftime('%H:%M:%S')}",
                    f"**K线周期**\n15分钟",
                ],
                template="purple",
            )

        return None
