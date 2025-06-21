import requests
from ..constants import QWEN_API_KEY, QWEN_API_URL

def call_qwen(user_message, system_prompt="", model="qwen-plus", enable_search=True):
    """
    通义千问统一 API 调用函数（支持系统提示词 + 联网搜索）

    参数：
        user_message (str): 用户输入内容
        system_prompt (str): 系统提示词，可选
        model (str): 使用的模型，默认 "qwen-plus"
        enable_search (bool): 是否启用联网搜索，默认 False

    返回：
        str: 模型返回文本
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {QWEN_API_KEY}"
    }

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_message})

    # 主体参数
    payload = {
        "model": model,
        "messages": messages
    }

    # 如果需要启用联网功能，合并相关字段
    if enable_search:
        payload.update({
            "enable_search": True,
            "search_options": {
                "forced_search": True  # 可选，加上更稳定触发联网
            }
        })

    try:
        response = requests.post(QWEN_API_URL, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        reply = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        return reply or "很抱歉，我没有理解你的问题。"
    except Exception as e:
        print(f"[Qwen调用失败]: {e}")
        return "出现了一些问题，我暂时无法回答你的问题。"



