""" 构建mcp消息 """
from typing import Literal
from ...type_hints.result_type import MCPResult

def build_message(
    status: Literal["success", "error"],
    mcp_type: Literal["chat", "search", "command"] = "chat",
    payload: dict = {},
) -> MCPResult:
    """
    构造一个标准的 MCP 消息结构。
    """
    return MCPResult(status=status, mcp_type=mcp_type, payload=payload)

def extract_text(message: MCPResult) -> str:
    """
    从消息中提取文本内容（如果存在）。
    """
    return message.get("payload", {}).get("text", "")

