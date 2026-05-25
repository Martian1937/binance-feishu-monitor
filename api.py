import requests
from config import REST_URL, INTERVAL
from util import log


def _parse_kline(k):
    return {
        "open_time": int(k[0]),
        "open": float(k[1]),
        "high": float(k[2]),
        "low": float(k[3]),
        "close": float(k[4]),
        "volume": float(k[5]),
    }


def fetch_kline(sym):
    try:
        resp = requests.get(REST_URL, params={
            "symbol": sym.upper(),
            "interval": INTERVAL,
            "limit": 1,
        }, timeout=10)
        return _parse_kline(resp.json()[0])
    except Exception as e:
        log(f"[{sym.upper()}] API 请求失败: {e}")
        return None


def fetch_klines(sym, limit):
    try:
        resp = requests.get(REST_URL, params={
            "symbol": sym.upper(),
            "interval": INTERVAL,
            "limit": limit,
        }, timeout=10)
        return [_parse_kline(k) for k in resp.json()]
    except Exception as e:
        log(f"[{sym.upper()}] 批量K线请求失败: {e}")
        return None
