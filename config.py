import os

SYMBOLS = ["vvvusdt", "labusdt", "litusdt", "opnusdt"]
INTERVAL = "1m"
THRESHOLD = 0.02
CHECK_INTERVAL = 30
ALERT_COOLDOWN = 120
TREND_KLINES = 5
TREND_THRESHOLD = 0.04
VOLUME_WINDOW = 10
VOLUME_MULTIPLIER = 2.0
LARK_WEBHOOK = os.environ.get("LARK_WEBHOOK") or ""
REST_URL = "https://fapi.binance.com/fapi/v1/klines"
