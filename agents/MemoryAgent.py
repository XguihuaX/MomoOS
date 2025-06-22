from ..database.services import *
from ..type_hints.interfaces import IAgent
from ..type_hints.request_type import MCPInvokeRequest
from ..type_hints.result_type import MCPResult
from ..core.short_memory.memory_buffer import get_short_term, clear_short_term
from ..core.llm.deepseek_api import call_deepseek
from ..core.constants import MEM_AGENT_PROMPT
from ..core.logger import logger
from ..core.active_user import active_user_ids  # ✅ 维护活跃用户ID
import json

class MemoryAgent(IAgent):

    def handle(self, message: MCPInvokeRequest) -> MCPResult:
        payload = message.get("payload", {})
        function = payload.get("func")
        args = payload.get("args", {})
        user_id = args.get("user_id")
        if not user_id:
            return MCPResult(status="error", mcp_type="command", payload={"msg": "缺少参数user_id"})

        active_user_ids.add(user_id)  # ✅ 每次调用时加入活跃用户

        try:
            if function == "add_todo":
                todo = add_todo(**args)
                return MCPResult(status="success", mcp_type="command", payload={"msg": "Todo 添加成功", "id": todo.id})

            elif function == "delete_todo":
                success = delete_todo(args["id"], user_id)
                return MCPResult(status="success" if success else "error", mcp_type="command", payload={"msg": "Todo 删除成功" if success else "未找到对应id"})

            elif function == "search_todo":
                results = search_todo(**args)
                return MCPResult(status="success", mcp_type="command", payload={"msg": "查询成功", "results": results})

            elif function == "add_memory":
                memory = add_memory(**args)
                return MCPResult(status="success", mcp_type="command", payload={"msg": "Memory 添加成功", "id": memory.id})

            elif function == "delete_memory":
                success = delete_memory(args["memory_id"], user_id=user_id)
                return MCPResult(status="success" if success else "error", mcp_type="command", payload={"msg": "Memory 删除成功" if success else "未找到对应id"})

            elif function == "search_memory":
                results = search_memory(**args)
                return MCPResult(status="success", mcp_type="command", payload={
                    "msg": "Memory 查询成功",
                    "results": [
                        {
                            "id": r.id,
                            "user_id": r.user_id,
                            "role": r.role,
                            "type": r.type,
                            "content": r.content,
                            "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S")
                        } for r in results
                    ]
                })

            elif function == "add_personality":
                add_personality(**args)
                return MCPResult(status="success", mcp_type="command", payload={"msg": "Personality 添加或更新成功"})

            elif function == "delete_personality":
                success = delete_personality(**args)
                return MCPResult(status="success" if success else "error", mcp_type="command", payload={"msg": "Personality 删除成功" if success else "未找到对应记录"})

            elif function == "search_personality":
                results = search_personality(**args)
                return MCPResult(status="success", mcp_type="command", payload={
                    "msg": "Personality 查询成功",
                    "results": [
                        {
                            "user_id": r.user_id,
                            "type": r.type.value,
                            "tag": r.tag,
                            "content": r.content
                        } for r in results
                    ]
                })

            else:
                logger.warning(f"[MemoryAgent] 收到未知函数调用: {function}")
                return MCPResult(status="error", mcp_type="command", payload={"msg": f"未知函数: {function}"})

        except Exception as e:
            logger.error(f"[MemoryAgent] 执行 {function} 失败：{e}")
            return MCPResult(status="error", mcp_type="command", payload={"msg": f"MemoryAgent执行 {function}, 出错: {e} "})

    def write(self, item: dict):
        table = item.get("table", {})
        content = item.get("content", {})
        user_id = content.get("user_id")

        try:
            if table == "memory":
                add_memory(
                    user_id=user_id,
                    role=content["role"],
                    type=content["type"],
                    content=content["content"],
                )
            elif table == "personality":
                add_personality(
                    user_id=user_id,
                    type=content["type"],
                    tag=content["tag"],
                    content=content["content"],
                )
            else:
                logger.error(f"未识别的表名: {table}")
                return None

        except Exception as e:
            logger.error(f"写入失败: {e} | 数据: {item}")
            return None

    def read(self, table: str, **kwargs):
        try:
            if table == "memory":
                return search_memory(
                    role=kwargs.get("role"),
                    type=kwargs.get("type"),
                    user_id=kwargs.get("user_id", "")
                )
            elif table == "personality":
                return search_personality(
                    user_id=kwargs.get("user_id", "雪"),
                    type=kwargs.get("type"),
                    tag=kwargs.get("tag")
                )
            else:
                logger.error(f"未识别的表名: {table}")
                return None

        except Exception as e:
            logger.error(f"读取失败: {e} | 表: {table}, 参数: {kwargs}")
            return None

    def summarize_and_save(self):
        from ..server.flask_app import app
        with app.app_context():
            if not active_user_ids:
                logger.info("没有活跃用户，无需总结")
                return

            for user_id in list(active_user_ids):
                memory = get_short_term(user_id)
                if not memory:
                    logger.info(f" 用户 {user_id} 无短期记忆可总结")
                    continue

                dialogue = "\n".join([f"{m['role']}：{m['text']}" for m in memory])
                _prompt = MEM_AGENT_PROMPT.format(dialogue=dialogue)

                try:
                    summary_json = call_deepseek(_prompt).strip()
                    result = json.loads(summary_json) if isinstance(summary_json, str) else summary_json

                    for item in result:
                        item["user_id"] = user_id
                        self.write(item)

                    logger.success(f"总结完成并写入成功，用户 {user_id}")
                    clear_short_term(user_id=user_id)

                except Exception as e:
                    logger.error(f"总结失败: {e}，用户: {user_id}")

            active_user_ids.clear()
