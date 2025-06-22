""" 请求类型 """

from typing import TypedDict, Any, Optional

class _MCPPayload(TypedDict):
    """ mcp负载 """
    func: Optional[str]
    args: dict[str, Any]

class MCPInvokeRequest(TypedDict):
    """ mcp调用请求类型 """
    payload: _MCPPayload
    """ 负载 """