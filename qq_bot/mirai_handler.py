# mirai_handler.py

import requests
from ai_project.qq_bot.qq_config import VERIFY_KEY, QQ_ID, MIRAI_API_BASE

class MiraiClient:
    def __init__(self):
        self.session_key = self._init_session()

    def _init_session(self):
        # 1. 获取 sessionKey
        verify_url = f"{MIRAI_API_BASE}/verify"
        resp = requests.post(verify_url, json={"verifyKey": VERIFY_KEY})
        session = resp.json().get("session")
        if not session:
            raise RuntimeError(f"[❌] 获取 sessionKey 失败: {resp.text}")
        print(f"[✅] 获取 sessionKey 成功: {session}")

        # 2. 绑定 QQ 号
        bind_url = f"{MIRAI_API_BASE}/bind"
        bind_resp = requests.post(bind_url, json={"sessionKey": session, "qq": QQ_ID})
        if bind_resp.json().get("code") != 0:
            raise RuntimeError(f"[❌] 绑定 QQ 失败: {bind_resp.text}")
        print("[✅] QQ号绑定成功")

        return session

    def send_text_message(self, text):
        url = f"{MIRAI_API_BASE}/sendFriendMessage"
        payload = {
            "sessionKey": self.session_key,
            "target": QQ_ID,
            "messageChain": [
                {"type": "Plain", "text": text}
            ]
        }
        resp = requests.post(url, json=payload)
        if resp.status_code == 200:
            print("[✅] 消息发送成功:", text)
        else:
            print("[❌] 消息发送失败:", resp.text)
