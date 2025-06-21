""" 接口类型 """

from abc import ABC, abstractmethod
from .result_type import MCPResult
from .request_type import MCPInvokeRequest

class IAgent(ABC):

    @abstractmethod
    def handle(self, message: MCPInvokeRequest) -> MCPResult:
        """
        执行实际处理逻辑，返回标准格式结果。
        返回格式应遵循 MCP 协议：
        {
            "status": "success" / "error",
            "type": "chat" / "command" / "search" 等，
            "payload": {
                "text": "文本回复",
                "audio": "base64音频（可选）"
            }
        }
        """
        ...
