import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.lark import send_lark
from common.util import log
from price.price_alerts import (
    PRICE_ALERT_COOLDOWN,
    PRICE_POLL_INTERVAL,
    PRICE_SERVER_HOST,
    PRICE_SERVER_PORT,
    PRICE_SOURCE,
    LARK_WEBHOOK_PRICE,
    PriceAlertStore,
    normalize_symbol,
    poll_loop,
)


class Handler(BaseHTTPRequestHandler):
    store = None

    def log_message(self, fmt, *args):
        pass

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _send_json(self, obj, status=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self._cors()
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b""
        if not raw:
            return {}
        return json.loads(raw.decode("utf-8"))

    def do_GET(self):
        if self.path == "/api/alerts":
            self._send_json({"alerts": self.store.snapshot(), "source": PRICE_SOURCE})
        elif self.path in ("/", "/index.html"):
            self._send_json({
                "service": "price-alerts-api",
                "endpoints": [
                    "GET /api/alerts",
                    "POST /api/alerts",
                    "DELETE /api/alerts/{symbol}",
                ],
                "source": PRICE_SOURCE,
            })
        else:
            self._send_json({"error": "not found"}, 404)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_POST(self):
        if self.path != "/api/alerts":
            self._send_json({"error": "not found"}, 404)
            return
        try:
            body = self._read_json()
        except Exception:
            self._send_json({"error": "invalid json"}, 400)
            return
        symbol = normalize_symbol(body.get("symbol", ""))
        if not symbol:
            self._send_json({"error": "invalid symbol"}, 400)
            return
        levels = body.get("levels")
        enabled = bool(body.get("enabled", True))
        item = self.store.upsert(symbol, levels, enabled)
        self._send_json({"alert": item, "alerts": self.store.snapshot()})

    def do_DELETE(self):
        parts = self.path.rstrip("/").split("/")
        if len(parts) == 4 and parts[1] == "api" and parts[2] == "alerts":
            ok = self.store.remove(parts[3])
            self._send_json({"ok": ok, "alerts": self.store.snapshot()})
        else:
            self._send_json({"error": "not found"}, 404)


def run():
    store = PriceAlertStore()
    Handler.store = store

    alerts = store.snapshot()
    total_levels = sum(len(a["levels"]) for a in alerts)
    send_lark(
        "🟢 点位提醒监控已启动",
        [
            f"**监控币种**\n{len(alerts)} 个 / 共 {total_levels} 个价位",
            f"**价格源**\n{PRICE_SOURCE}",
            f"**检查间隔**\n{PRICE_POLL_INTERVAL}秒",
            f"**告警冷却**\n{PRICE_ALERT_COOLDOWN}秒",
        ],
        template="green",
        webhook=LARK_WEBHOOK_PRICE,
    )

    poll = threading.Thread(target=poll_loop, args=(store,), daemon=True)
    poll.start()

    server = ThreadingHTTPServer((PRICE_SERVER_HOST, PRICE_SERVER_PORT), Handler)
    log(f"点位提醒页面: http://{PRICE_SERVER_HOST}:{PRICE_SERVER_PORT}")
    log(f"点位提醒配置: {store.data_file}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    run()
