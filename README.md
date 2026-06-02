# binance-feishu-monitor

监控 Binance U 本位永续合约 K 线，捕捉放量拉升 / 放量下跌，通过飞书机器人推送告警。

## 功能

- **15 分钟 K 线**，60 秒轮询
- **Top 涨幅榜自动更新**：启动和定时刷新 Binance U 本位涨幅榜 Top50，并与手动币种合并
- **组合告警**：单 K 线涨跌幅 / 成交量放大 / 前一根 K 线方向
- **告警冷却**，避免刷屏
- **飞书卡片消息**，不同颜色区分告警类型

## 使用

```bash
pip install -r requirements.txt
LARK_WEBHOOK="https://..." python3 main.py
```

环境变量可以参考 `.env.example`，不要把真实 Webhook 提交到仓库。

## 配置

编辑 `config.py`:

| 变量 | 说明 | 默认值 |
|---|---|---|
| `SYMBOLS` | 运行时合并后的完整监控币种列表 | `["labusdt"]` |
| `MANUAL_SYMBOLS` | 手动固定监控币种列表 | `["labusdt"]` |
| `INTERVAL` | K 线周期 | `15m` |
| `THRESHOLD` | 单 K 线涨跌幅阈值 | 0.03 (3%) |
| `CHECK_INTERVAL` | 轮询间隔 (秒) | 60 |
| `ALERT_COOLDOWN` | 告警冷却 (秒) | 300 |
| `VOLUME_WINDOW` | 成交量均值窗口 | 10 |
| `VOLUME_MULTIPLIER` | 成交量放大倍数 | 2.0 |
| `TOP_N` | 涨幅榜取前 N 个币种 | 50 |
| `ENABLE_TOP_GAINERS` | 是否从接口获取涨幅榜 TopN 并合并监控 | False |
| `REFRESH_INTERVAL` | 涨幅榜刷新间隔 (秒) | 1800 |
| `LARK_WEBHOOK` | 飞书机器人 Webhook | — |

## 环境变量

| 变量 | 用途 |
|---|---|
| `LARK_WEBHOOK` | `main.py` 主监控飞书机器人 |
| `LARK_WEBHOOK_MA` | `main_ma.py` 均线监控飞书机器人 |
| `EMAIL_MA` | `main_ma.py` 加急提醒日志中的邮件地址 |

## 项目结构

```
binance-feishu-monitor/
├── config.py       # 配置常量
├── requirements.txt # Python 依赖
├── .env.example    # 环境变量示例（不含真实密钥）
├── util.py         # 通用工具 (log)
├── lark.py         # 飞书消息推送
├── api.py          # Binance REST API
├── monitor.py      # 调度引擎 (K线 + 多策略)
├── main.py         # 入口
├── main_ma.py      # BTC/ETH 均线摆正监控入口
└── strategies/     # 策略目录
    ├── __init__.py # 策略注册
    ├── base.py     # 基类
    ├── surge.py    # 放量拉升 + 放量下跌
    ├── trend.py    # EMA20 / MA20 趋势策略（未注册）
    └── ma_alignment.py # main_ma.py 使用的均线场景逻辑
```

`PLAN.md` 是历史优化方案；`core.md` 记录当前主监控核心算法；`NOTES.md` 记录敏感信息处理方式。

## 后台运行

```bash
source ~/.zshrc
nohup python3 main.py > py-script.log 2>&1 &
```

## 均线监控入口

`main_ma.py` 是独立入口，监控 BTC/ETH 的 15 分钟和 1 小时均线场景，使用单独的环境变量：

```bash
LARK_WEBHOOK_MA="https://..." python3 main_ma.py
```

## 验证

当前项目没有测试框架。修改后至少运行语法检查：

```bash
python3 -m py_compile main.py main_ma.py api.py lark.py monitor.py util.py config.py strategies/base.py strategies/surge.py strategies/trend.py strategies/ma_alignment.py strategies/__init__.py
```
