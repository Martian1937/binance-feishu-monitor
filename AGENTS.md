# AGENTS.md — py-script

## 运行

```bash
python3 backend/surge/main.py
```

均线摆正监控：

```bash
python3 backend/ma/main.py
```

点位提醒（HTTP 服务 + 轮询）：

```bash
python3 backend/price/main.py
```

点位提醒前端（Vue 3 + Vite，`/api` 代理到 `127.0.0.1:8090`）：

```bash
cd frontend && npm install && npm run dev
```

## 依赖

```bash
pip install -r backend/requirements.txt
```

环境变量示例见 `backend/.env.example`，真实 Webhook 不要写入仓库。

## 项目结构

```
binance-feishu-monitor/
├── backend/           # Python 后端
│   ├── surge/         # 放量监控入口 (原 main.py)
│   │   ├── main.py    # 主入口 (Top涨幅 + 手动币种监控)
│   │   └── monitor.py # K线状态维护、策略调度、定时器
│   ├── ma/            # 均线摆正监控入口
│   │   └── main.py    # BTC/ETH 均线摆正监控 (原 main_ma.py)
│   ├── price/         # 点位提醒入口
│   │   ├── main.py    # 点位提醒 HTTP 服务 + 轮询 (原 main_price.py)
│   │   ├── price_alerts.py   # 点位提醒核心 (价格源/配置存储/突破检测)
│   │   └── price_alerts.json # 点位提醒本地配置 (已 gitignore)
│   ├── common/        # 共享模块
│   │   ├── config.py  # 配置常量 (币种、阈值、Webhook 等)
│   │   ├── util.py    # 通用工具 (log)
│   │   ├── lark.py    # 飞书机器人卡片消息推送
│   │   └── api.py     # Binance REST API K线和涨幅榜获取
│   ├── strategies/    # 策略模块
│   │   ├── base.py    # 策略基类
│   │   ├── surge.py   # 放量拉升 + 放量下跌
│   │   ├── trend.py   # EMA20 / MA20 趋势策略（未注册）
│   │   └── ma_alignment.py # 均线摆正使用的场景逻辑
│   ├── requirements.txt
│   └── .env.example   # 环境变量示例（不含真实密钥）
└── frontend/          # 点位提醒前端 (Vue 3 + Vite)
```

## 关键配置

编辑 `backend/common/config.py`:

- `SYMBOLS` — 运行时合并后的完整监控币种列表
- `MANUAL_SYMBOLS` — 手动固定监控币种列表 (小写, e.g. `["vvvusdt", "labusdt"]`)
- `INTERVAL` — K 线周期 (默认 `15m`)
- `THRESHOLD` — 涨跌幅告警阈值 (默认 0.03 = 3%)
- `LARK_WEBHOOK` — 飞书机器人 Webhook URL
- `CHECK_INTERVAL` — 定时检查间隔秒数 (默认 60)
- `ALERT_COOLDOWN` — 告警冷却秒数 (默认 300)
- `TOP_N` — 涨幅榜取前 N 个币种 (默认 50)
- `ENABLE_TOP_GAINERS` — 是否从接口获取涨幅榜 TopN 并合并监控 (默认 `False`)
- `REFRESH_INTERVAL` — 涨幅榜刷新间隔秒数 (默认 1800)

## 架构

- 三个入口互相独立，各自是一个进程：`backend/surge/main.py`（放量监控）、`backend/ma/main.py`（均线摆正）、`backend/price/main.py`（点位提醒）
- 共享代码统一放在 `backend/common/`，导入形如 `from common.config import ...`；入口文件通过 `sys.path` 注入 `backend/` 目录，因此可以直接按路径运行
- 启动时根据 `ENABLE_TOP_GAINERS` 决定是否 REST API 获取涨幅榜 TopN，再与 `MANUAL_SYMBOLS` 合并后初始化 K 线并推送飞书消息
- 后台线程每 `CHECK_INTERVAL` 秒轮询币安 API；开启 `ENABLE_TOP_GAINERS` 后每 `REFRESH_INTERVAL` 秒刷新涨幅榜
- 当前主入口只注册 `SurgeStrategy`，检测放量拉升 / 放量下跌
- 飞书消息使用卡片消息格式 (`interactive`)
- 无框架、无测试、无 lint/typecheck 配置

## 注意事项

- 需要外网访问 `fapi.binance.com`
- 点位提醒默认使用 `data-api.binance.vision`（币安公共行情域名），在部分网络下比 `api.binance.com` 更稳定
- 告警有冷却期，避免刷屏
- `backend/ma/main.py` 使用 `LARK_WEBHOOK_MA`，与主入口 `LARK_WEBHOOK` 分开配置
- `backend/price/main.py` 使用 `LARK_WEBHOOK_PRICE`，未配置时回退到 `LARK_WEBHOOK`

## 验证

无测试框架。修改后至少运行：

```bash
python3 -m py_compile backend/surge/main.py backend/surge/monitor.py backend/ma/main.py backend/price/main.py backend/price/price_alerts.py backend/common/api.py backend/common/lark.py backend/common/util.py backend/common/config.py backend/strategies/base.py backend/strategies/surge.py backend/strategies/trend.py backend/strategies/ma_alignment.py backend/strategies/__init__.py
```

## 文件状态说明

- `PLAN.md` 是历史优化方案，不代表当前运行参数。
- `core.md` 记录当前主监控核心算法。
- `backend/strategies/trend.py` 当前未在 `backend/strategies/__init__.py` 注册，主入口不会执行。
