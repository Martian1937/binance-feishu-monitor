import os

SYMBOLS = ["vvvusdt", "labusdt", "litusdt", "opnusdt"]  # 手动监控的币种（小写+usdt）
INTERVAL = "1m"                                          # K线周期：1m / 3m / 5m / 15m 等
THRESHOLD = 0.01                                         # 单K线拉升阈值（1%）
CHECK_INTERVAL = 30                                      # API 轮询间隔（秒）
ALERT_COOLDOWN = 120                                     # 同维度告警冷却时间（秒）
TREND_KLINES = 5                                         # 趋势判断取几根 K 线
TREND_THRESHOLD = 0.02                                   # 趋势累计涨幅阈值（2%）
VOLUME_WINDOW = 10                                       # 成交量均值窗口（根）
VOLUME_MULTIPLIER = 2.0                                  # 成交量放大倍数
TOP_N = 50                                               # 涨幅榜取前 N 个币种
LARK_WEBHOOK = os.environ.get("LARK_WEBHOOK") or ""      # 飞书机器人 Webhook
REST_URL = "https://fapi.binance.com/fapi/v1/klines"     # Binance U本位合约 K线 API
