
from ..type_hints.request_type import MCPInvokeRequest
from ..type_hints.interfaces import IAgent
from ..type_hints.result_type import MCPResult
from ..core.message.mcp_message import build_message
from ..utils import toolbox

class ToolAgent(IAgent):

    def handle(self, message: MCPInvokeRequest) -> MCPResult:
        payload = message.get("payload", {})
        func_name = payload.get("function")
        args = payload.get("args", {}) or {}

        # ✅ 优先从 args 中提取 user_id，确保透传到实际函数中
        user_id = args.get("user_id") or payload.get("user_id") or "default"
        args["user_id"] = user_id
        if not func_name:
            return build_message(
                status="error",
                mcp_type="command",
                payload={
                    "user_id": user_id,
                    "tool_result": "未提供 function 名称",
                }
            )

        try:
            # ✅ 动态获取工具函数
            func = getattr(toolbox, func_name)

            # ✅ 如果 toolbox 函数支持 user_id，就注入进去
            if "user_id" in func.__code__.co_varnames:
                args["user_id"] = user_id

            # ✅ 执行函数
            result = func(**args)

            return build_message(
                status="success",
                mcp_type="command",
                payload={
                    "user_id": user_id,
                    "tool_result": result,
                }
            )

        except AttributeError:
            return build_message(
                status="error",
                mcp_type="command",
                payload={
                    "user_id": user_id,
                    "tool_result": f"函数「{func_name}」不存在。",
                }
            )
        except Exception as e:
            return build_message(
                status="error",
                mcp_type='command',
                payload={
                    "user_id": user_id,
                    "tool_result": f"函数「{func_name}」执行出错：{str(e)}",
                }
            )
