""" 请求类型 """

from typing import TypedDict

class _MCPPayload(TypedDict):
    """ mcp负载 """
    func: str
    args: dict

class MCPInvokeRequest(TypedDict):
    """ mcp调用请求类型 """
    payload: _MCPPayload
    """ 负载 """