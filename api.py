import requests
from config import REST_URL, INTERVAL
from util import log


def fetch_kline(sym):
    try:
        resp = requests.get(REST_URL, params={
            "symbol": sym.upper(),
            "interval": INTERVAL,
            "limit": 1,
        }, timeout=10)
        data = resp.json()
        k = data[0]
        return {
            "open": float(k[1]),
            "high": float(k[2]),
            "low": float(k[3]),
            "close": float(k[4]),
        }
    except Exception as e:
        log(f"[{sym.upper()}] API 请求失败: {e}")
        return None
