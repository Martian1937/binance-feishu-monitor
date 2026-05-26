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

 source ~/.zshrc && nohup python3 main.py > py-script.log 2>&1 

帮我新增一个入口，主要是针对btc和eth的策略，给我推送到 这个lark机器人： https://open.feishu.cn/open-apis/bot/v2/hook/43d841e4-3000-47a3-b879-62eea6142804
策略如下：
 均线摆正上涨策略提醒，可能是15分钟K线，也可能是1小时K线，也可能是4小时K线的
我们主要监控15分钟和1小时的，当15分钟和1小时都走出了下面的场景：
5， 10， 20， 60 ，均线排布依次是5日在10日上面，10日在20日上面，20日在60日上面
1. 当只有5日刚站上10日上面，我们提示可能是注意，趋势在变化
2. 当只有5日刚站上10日上面，10日站在20日上面，我们提示可能是注意，趋势变化在强化
3. 当只有5日刚站上10日上面，10日站在20日上面，20日站在60日上面，我们提示可能是注意，趋势发生转变，强烈注意

提醒一：如果1小时达到了上面的3种case，分颜色提醒， 标题是1小时场景提醒

提醒2:  如果15分钟和1小时都至少都要各同时具备上面3种条件中的一种，我们就提醒，直接红色标题提示，标题是： 交叉场景提醒

提醒3： 如果在提醒2里面，发现15分钟和1小时都触发了均线ema20在ma20上面，加急提醒，不仅发消息，还给我发邮件