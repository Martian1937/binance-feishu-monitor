import os

SYMBOLS = ["labusdt"]                                      # 运行时合并后的完整列表（会自动更新）
MANUAL_SYMBOLS = ["labusdt"]                               # 手动监控的币种（不会被覆盖）
INTERVAL = "15m"                                         # K线周期：1m / 3m / 5m / 15m 等
THRESHOLD = 0.05                                       # 单K线涨跌幅阈值（3%）
CHECK_INTERVAL = 60                                      # API 轮询间隔（秒）
ALERT_COOLDOWN = 300                                     # 告警冷却时间（秒）
VOLUME_WINDOW = 10                                       # 成交量均值窗口（根）
VOLUME_MULTIPLIER = 2                                # 成交量放大倍数
TOP_N = 50                                               # 涨幅榜取前 N 个币种
ENABLE_TOP_GAINERS = False                               # 是否从接口获取涨幅榜 TopN 并合并监控
REFRESH_INTERVAL = 1800                                  # 涨幅榜刷新间隔（秒，默认30分钟）
LARK_WEBHOOK = os.environ.get("LARK_WEBHOOK") or ""      # 飞书机器人 Webhook
REST_URL = "https://fapi.binance.com/fapi/v1/klines"     # Binance U本位合约 K线 API
