# AGENTS.md — py-script

## 运行

```bash
python3 main.py
```

## 依赖

```bash
pip install -r requirements.txt
```

环境变量示例见 `.env.example`，真实 Webhook 不要写入仓库。

## 项目结构

```
binance-feishu-monitor/
├── config.py          # 配置常量 (币种、阈值、Webhook 等)
├── requirements.txt   # Python 依赖
├── .env.example       # 环境变量示例（不含真实密钥）
├── util.py            # 通用工具 (log)
├── lark.py            # 飞书机器人卡片消息推送
├── api.py             # Binance REST API K线和涨幅榜获取
├── monitor.py         # K线状态维护、策略调度、定时器
├── main.py            # 主入口 (Top涨幅 + 手动币种监控)
├── main_ma.py         # 独立入口 (BTC/ETH 均线摆正监控)
└── strategies/        # 策略模块
    ├── base.py        # 策略基类
    ├── surge.py       # 放量拉升 + 放量下跌
    ├── trend.py       # EMA20 / MA20 趋势策略（未注册）
    └── ma_alignment.py # main_ma.py 使用的均线场景逻辑
```

## 关键配置

编辑 `config.py`:

- `SYMBOLS` — 运行时合并后的完整监控币种列表
- `MANUAL_SYMBOLS` — 手动固定监控币种列表 (小写, e.g. `["vvvusdt", "labusdt"]`)
- `INTERVAL` — K 线周期 (默认 `15m`)
- `THRESHOLD` — 涨跌幅告警阈值 (默认 0.03 = 3%)
- `LARK_WEBHOOK` — 飞书机器人 Webhook URL
- `CHECK_INTERVAL` — 定时检查间隔秒数 (默认 60)
- `ALERT_COOLDOWN` — 告警冷却秒数 (默认 300)
- `TOP_N` — 涨幅榜取前 N 个币种 (默认 50)
- `REFRESH_INTERVAL` — 涨幅榜刷新间隔秒数 (默认 1800)

## 架构

- 启动时 REST API 获取涨幅榜 TopN，与 `MANUAL_SYMBOLS` 合并后初始化 K 线并推送飞书消息
- 后台线程每 `CHECK_INTERVAL` 秒轮询币安 API，并每 `REFRESH_INTERVAL` 秒刷新涨幅榜
- 当前主入口只注册 `SurgeStrategy`，检测放量拉升 / 放量下跌
- 飞书消息使用卡片消息格式 (`interactive`)
- 无框架、无测试、无 lint/typecheck 配置

## 注意事项

- 需要外网访问 `fapi.binance.com`
- 告警有冷却期，避免刷屏
- `main_ma.py` 使用 `LARK_WEBHOOK_MA`，与主入口 `LARK_WEBHOOK` 分开配置

## 验证

无测试框架。修改后至少运行：

```bash
python3 -m py_compile main.py main_ma.py api.py lark.py monitor.py util.py config.py strategies/base.py strategies/surge.py strategies/trend.py strategies/ma_alignment.py strategies/__init__.py
```

## 文件状态说明

- `PLAN.md` 是历史优化方案，不代表当前运行参数。
- `core.md` 记录当前主监控核心算法。
- `strategies/trend.py` 当前未在 `strategies/__init__.py` 注册，主入口不会执行。
