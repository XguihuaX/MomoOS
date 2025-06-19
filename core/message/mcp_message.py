# utils/mcp_message.py

def build_message(
    payload: dict,
) -> dict:
    """
    构造一个标准的 MCP 消息结构。
    """
    return {
        "payload": payload
    }


def validate_message(message: dict) -> bool:
    """
    校验是否是符合 MCP 协议的结构化消息。
    """
    required_keys = {  "payload"}
    return isinstance(message, dict) and required_keys.issubset(message.keys())


def extract_text(message: dict) -> str:
    """
    从消息中提取文本内容（如果存在）。
    """
    return message.get("payload", {}).get("text", "")


