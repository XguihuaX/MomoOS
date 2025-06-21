""" 请求类型 """

from typing import TypedDict

class __MCPPayload(TypedDict):
    """ mcp负载 """
    func: str
    args: dict

class MCPInvokeRequest(TypedDict):
    """ mcp调用请求类型 """
    payload: __MCPPayload
    """ 负载 """