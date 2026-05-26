import requests
from config import LARK_WEBHOOK
from util import log


def send_lark(title, content_lines, template="red", webhook=None):
    url = webhook or LARK_WEBHOOK
    if not url:
        log("Lark webhook 未配置，跳过")
        return False
    try:
        payload = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {"tag": "plain_text", "content": title},
                    "template": template,
                },
                "elements": [
                    {
                        "tag": "div",
                        "fields": [
                            {"is_short": True, "text": {"tag": "lark_md", "content": line}}
                            for line in content_lines
                        ],
                    }
                ],
            },
        }
        resp = requests.post(url, json=payload, timeout=10)
        result = resp.json()
        if result.get("code") == 0:
            log("Lark 消息发送成功")
            return True
        log(f"Lark 发送失败: {result}")
        return False
    except Exception as e:
        log(f"Lark 发送异常: {e}")
        return False
