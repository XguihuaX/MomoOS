# agents/BaseAgent.py

from abc import ABC, abstractmethod

class BaseAgent(ABC):
    @abstractmethod


    @abstractmethod
    def handle(self, text: str) -> dict:
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
        raise NotImplementedError("handle() 必须由子类实现")
