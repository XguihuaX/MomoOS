# agents/SearchAgent.py
from core.llm.qwen_api import call_qwen

class SearchAgent:
    def handle(self, message: dict) -> dict:
        query = message.get("payload", {}).get("query", "")
        print(f"[SearchAgent] 查询请求: {query}")

        try:
            reply = call_qwen(
                user_message=query,
                system_prompt="",      # 关键：不加任何角色设定
                model="qwen-plus"
            )
            return {
                "status": "success",
                "agent": "SearchAgent",
                "payload": {
                    "text": reply,
                    "tool_result": reply
                }
            }

        except Exception as e:
            return {
                "status": "error",
                "agent": "SearchAgent",
                "payload": {
                    "text": f"搜索失败: {e}",
                    "tool_result": ""
                }
            }
