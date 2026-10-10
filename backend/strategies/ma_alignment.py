def _sma(values, period):
    if len(values) < period:
        return None
    return sum(values[-period:]) / period


def _ema(values, period):
    if len(values) < period:
        return None
    multiplier = 2 / (period + 1)
    ema = sum(values[:period]) / period
    for v in values[period:]:
        ema = (v - ema) * multiplier + ema
    return ema


CASE_LABELS = {
    1: "第一级：MA5 刚站上 MA10，趋势可能变化 ⚠️",
    2: "第二级：MA5 > MA10 > MA20，趋势变化强化 🔵",
    3: "第三级：MA5 > MA10 > MA20 > MA60，趋势转变，强烈注意 🔴",
}

CASE_TEMPLATES = {1: "yellow", 2: "blue", 3: "red"}


def check_alignment(klines):
    closes = [k["close"] for k in klines]

    ma5 = _sma(closes, 5)
    ma10 = _sma(closes, 10)
    ma20 = _sma(closes, 20)
    ma60 = _sma(closes, 60)

    if any(v is None for v in [ma5, ma10]):
        return None

    c1 = ma5 > ma10
    c2 = c1 and (ma20 is not None and ma10 > ma20)
    c3 = c2 and (ma60 is not None and ma20 > ma60)

    if c3:
        return (3, {"ma5": ma5, "ma10": ma10, "ma20": ma20, "ma60": ma60})
    if c2:
        return (2, {"ma5": ma5, "ma10": ma10, "ma20": ma20, "ma60": ma60})
    if c1:
        return (1, {"ma5": ma5, "ma10": ma10, "ma20": ma20, "ma60": ma60})

    return None


def build_ma_fields(case, details, price):
    lines = [f"**级别**\n{CASE_LABELS[case]}"]
    lines.append(f"**MA5**\n{details['ma5']:.6f}")
    lines.append(f"**MA10**\n{details['ma10']:.6f}")
    if details["ma20"] is not None:
        lines.append(f"**MA20**\n{details['ma20']:.6f}")
    if details["ma60"] is not None:
        lines.append(f"**MA60**\n{details['ma60']:.6f}")
    lines.append(f"**当前价格**\n{price:.6f} USDT")
    return lines


def check_ema_above_sma(klines):
    closes = [k["close"] for k in klines]
    ema20 = _ema(closes, 20)
    ma20 = _sma(closes, 20)
    if ema20 is None or ma20 is None:
        return False
    return ema20 > ma20
