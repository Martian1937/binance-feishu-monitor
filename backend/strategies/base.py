class BaseStrategy:
    name = ""
    cooldown = 300

    def init_state(self):
        return {}

    def check(self, sym, kline, klines, state, now):
        raise NotImplementedError

    def build_alert(self, tag, title, fields, template):
        return {"tag": tag, "title": title, "fields": fields, "template": template}
