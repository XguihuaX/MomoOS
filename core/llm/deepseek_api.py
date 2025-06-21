# utils/deepseek_api.py

import requests
from ..constants import DEEPSEEK_API_KEY, DEEPSEEK_API_URL

def call_deepseek(user_message, system_prompt="", model="deepseek-chat"):
    """
    基础DeepSeek API调用工具。

    参数：
        user_message (str): 用户输入内容
        system_prompt (str): 系统提示词（可选）
        model (str): 使用的模型名称（可选）

    返回：
        str: 模型回复文本
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
    }

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_message})

    payload = {
        "model": model,
        "messages": messages
    }

    try:
        response = requests.post(DEEPSEEK_API_URL, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        reply = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        return reply or "很抱歉，我没有理解你的问题。"
    except Exception as e:
        print(f"[DeepSeek调用失败]: {e}")
        return "出现了一些问题，我暂时无法回答你的问题。"
