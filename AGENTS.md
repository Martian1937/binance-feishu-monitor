# AGENTS.md — py-script

## 运行

```bash
python3 main.py
```

## 依赖

```bash
pip install requests
```

## 项目结构

```
py/
├── config.py    # 配置常量 (币种、阈值、Webhook 等)
├── util.py      # 通用工具 (log)
├── lark.py      # 飞书机器人卡片消息推送
├── api.py       # Binance REST API K线数据获取
├── monitor.py   # 价格检查、告警逻辑、定时器
└── main.py      # 入口 (初始化、启动)
```

## 关键配置

编辑 `config.py`:

- `SYMBOLS` — 监控币种列表 (小写, e.g. `["vvvusdt", "labusdt"]`)
- `THRESHOLD` — 涨跌幅告警阈值 (默认 0.03 = 3%)
- `LARK_WEBHOOK` — 飞书机器人 Webhook URL
- `CHECK_INTERVAL` — 定时检查间隔秒数 (默认 300)
- `ALERT_COOLDOWN` — 同方向告警冷却秒数 (默认 1800)

## 架构

- 启动时 REST API 获取初始 K 线并推送飞书消息
- 后台线程每 `CHECK_INTERVAL` 秒轮询币安 API 并做阈值检查
- 飞书消息使用卡片消息格式 (`interactive`)
- 无框架、无测试、无 lint/typecheck 配置

## 注意事项

- 需要外网访问 `fapi.binance.com`
- 同方向 (涨/跌) 告警有冷却期，避免刷屏
