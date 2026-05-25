# 优化方案 — 追涨型监控

## 目标

抓 U 本位合约的瞬间猛涨币种，快速发现、确认趋势、通知追入。

## 改进方向

### 1. 缩短周期

| 参数 | 旧值 | 新值 |
|---|---|---|
| `INTERVAL` | `15m` | `1m` |
| `CHECK_INTERVAL` | `300` | `30` |
| `THRESHOLD` | `0.03` | `0.02` |

### 2. 数据增强（api.py）

- K线返回增加 `volume` 字段
- 新增 `fetch_klines(sym, limit)` 批量取最近 N 根 K 线

### 3. 三维告警（monitor.py）

| 告警类型 | 逻辑 | 用途 |
|---|---|---|
| **单K线涨幅** | 当前K线从低点涨超阈值 | 抓瞬间拉升 |
| **多K线趋势** | 过去 N 根 K 线累计涨幅超阈值 | 确认持续上涨趋势 |
| **成交量放大** | 当前成交量 > 过去 N 根均值 * 倍数 | pump 前置信号 |

### 4. 新增配置（config.py）

```python
TREND_KLINES = 5          # 趋势判断取几根K线
TREND_THRESHOLD = 0.04    # 累计涨幅阈值 (4%)
VOLUME_WINDOW = 10        # 成交量均值窗口
VOLUME_MULTIPLIER = 2.0   # 成交量放大倍数
```

### 5. 飞书卡片模板（lark.py）

- `blue` — 趋势上涨告警
- `purple` — 成交量异常告警

### 6. 不改的部分

- `main.py` 启动逻辑保留，只适配新字段
- 仍使用 REST 轮询（暂不上 WebSocket）
