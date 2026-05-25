# binance-feishu-monitor

监控 Binance 永续合约 K 线价格波动，通过飞书机器人发送告警。

## 功能

- 实时监控多个币种 15 分钟 K 线
- 价格从 K 线最高点下跌 / 从最低点上涨超过阈值时触发告警
- 同方向告警有冷却时间，避免刷屏
- 飞书卡片消息推送

## 使用

```bash
pip install requests
python3 main.py
```

## 配置

编辑 `config.py`:

| 变量 | 说明 | 默认值 |
|---|---|---|
| `SYMBOLS` | 监控币种列表 (小写+usdt) | `["vvvusdt", "labusdt", ...]` |
| `THRESHOLD` | 涨跌幅告警阈值 | 0.03 (3%) |
| `CHECK_INTERVAL` | 轮询间隔 (秒) | 300 |
| `ALERT_COOLDOWN` | 同方向告警冷却 (秒) | 1800 |
| `LARK_WEBHOOK` | 飞书机器人 Webhook | — |

## 项目结构

```
binance-feishu-monitor/
├── config.py    # 配置常量
├── util.py      # 通用工具 (log)
├── lark.py      # 飞书消息推送
├── api.py       # Binance REST API
├── monitor.py   # 价格检查与告警逻辑
└── main.py      # 入口
```
