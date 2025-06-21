# agents/SearchAgent.py
from ..core.llm.qwen_api import call_qwen
from ..type_hints.request_type import MCPInvokeRequest
from ..type_hints.result_type import MCPResult
from ..type_hints.interfaces import IAgent
from ..core.logger import logger


class SearchAgent(IAgent):
    
    def handle(self, message: MCPInvokeRequest) -> MCPResult:
        query = message.get("payload", {}).get("query", "")
        logger(f"查询请求:{query}")

        try:
            reply = call_qwen(
                user_message=query,
                system_prompt="",      # 关键：不加任何角色设定
                model="qwen-plus"
            )
            return MCPResult(status="success", mcp_type="command", payload={"tool_result": reply})

        except Exception as e:
            return MCPResult(status="error", mcp_type="command", payload={"error": f"搜索失败，发生错误: {e}"})
