""" 结果类型 """

from typing import TypedDict, Literal, Any

class MCPResult(TypedDict):
    """ MCP协议结果类型 """
    status: Literal["success", "error"]
    """ 状态 """
    mcp_type: Literal["chat", "command", "search"]
    """ 类型 """
    payload: dict[str, Any]
    """ 载荷 """