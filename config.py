import os

SYMBOLS = ["vvvusdt", "labusdt", "litusdt", "opnusdt"]
INTERVAL = "15m"
THRESHOLD = 0.03
CHECK_INTERVAL = 300
ALERT_COOLDOWN = 1800
LARK_WEBHOOK = os.environ.get("LARK_WEBHOOK") or ""
REST_URL = "https://fapi.binance.com/fapi/v1/klines"
