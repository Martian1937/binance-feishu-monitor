# binance-feishu-monitor

监控 Binance U 本位永续合约 K 线，捕捉瞬间拉升 + 趋势上涨 + 成交量异常，通过飞书机器人推送告警。

## 功能

- **1 分钟 K 线**，30 秒轮询，快速发现异动
- **三维告警**：单 K 线拉升 / 多 K 线趋势 / 成交量放大
- **同方向冷却**，避免刷屏
- **飞书卡片消息**，不同颜色区分告警类型

## 使用

```bash
pip install requests
LARK_WEBHOOK="https://..." python3 main.py
```

## 配置

编辑 `config.py`:

| 变量 | 说明 | 默认值 |
|---|---|---|
| `SYMBOLS` | 监控币种列表 (小写+usdt) | `["vvvusdt", "labusdt", ...]` |
| `INTERVAL` | K 线周期 | `1m` |
| `THRESHOLD` | 单 K 线拉升阈值 | 0.02 (2%) |
| `CHECK_INTERVAL` | 轮询间隔 (秒) | 30 |
| `ALERT_COOLDOWN` | 同方向告警冷却 (秒) | 120 |
| `TREND_KLINES` | 趋势判断 K 线数量 | 5 |
| `TREND_THRESHOLD` | 趋势累计涨幅阈值 | 0.04 (4%) |
| `VOLUME_WINDOW` | 成交量均值窗口 | 10 |
| `VOLUME_MULTIPLIER` | 成交量放大倍数 | 2.0 |
| `LARK_WEBHOOK` | 飞书机器人 Webhook | — |

## 项目结构

```
binance-feishu-monitor/
├── config.py       # 配置常量
├── util.py         # 通用工具 (log)
├── lark.py         # 飞书消息推送
├── api.py          # Binance REST API
├── monitor.py      # 调度引擎 (K线 + 多策略)
├── main.py         # 入口
└── strategies/     # 策略目录
    ├── __init__.py # 策略注册
    ├── base.py     # 基类
    └── surge.py    # 放量拉升 + 放量下跌
```
