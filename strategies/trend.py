from .base import BaseStrategy


def _ema(values, period):
    multiplier = 2 / (period + 1)
    ema = sum(values[:period]) / period
    for v in values[period:]:
        ema = (v - ema) * multiplier + ema
    return ema


def _sma(values, period):
    return sum(values[-period:]) / period


class TrendFilterStrategy(BaseStrategy):
    """
    20 EMA vs 20 SMA 趋势过滤。

    上涨趋势中，EMA > SMA（快线在慢线上方，多头排列）
    下跌趋势中，EMA < SMA（快线在慢线下方，空头排列）

    激活前需将 monitor.py 的 MAX_KLINES 改为 40（当前 20 不够，EMA 需至少 21 根）。
    """

    name = "trend"
    cooldown = 300

    def init_state(self):
        return {"last_alert": 0}

    def check(self, sym, kline, klines, state, now):
        if len(klines) < 21:
            return None

        closes = [k["close"] for k in klines]
        ema_20 = _ema(closes, 20)
        sma_20 = _sma(closes, 20)

        tag = sym.upper().replace("USDT", "")
        ema_above = ema_20 > sma_20
        curr = kline["close"]
        prev = klines[-2]["close"] if len(klines) >= 2 else curr
        rising = curr > prev

        if ema_above and rising:
            return self.build_alert(
                tag=tag,
                title=f"📈 {tag} 多头排列（EMA20 > MA20）",
                fields=[
                    f"**当前价格**\n{curr:.6f} USDT",
                    f"**EMA20**\n{ema_20:.6f}",
                    f"**MA20**\n{sma_20:.6f}",
                    f"**差值**\n+{((ema_20 - sma_20) / sma_20 * 100):.2f}%",
                    f"**方向**\n多头 🟢",
                ],
                template="green",
            )

        if not ema_above and not rising:
            return self.build_alert(
                tag=tag,
                title=f"📉 {tag} 空头排列（EMA20 < MA20）",
                fields=[
                    f"**当前价格**\n{curr:.6f} USDT",
                    f"**EMA20**\n{ema_20:.6f}",
                    f"**MA20**\n{sma_20:.6f}",
                    f"**差值**\n{((ema_20 - sma_20) / sma_20 * 100):.2f}%",
                    f"**方向**\n空头 🔴",
                ],
                template="red",
            )

        return None
