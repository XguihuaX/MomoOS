import json
from datetime import datetime
import re
from ..type_hints.interfaces import IAgent
from ..type_hints.request_type import MCPInvokeRequest
from ..type_hints.result_type import MCPResult
from ..core.llm.qwen_api import call_qwen
from ..core.message.mcp_message import build_message
from ..core.short_memory.memory_buffer import add_to_short_term
from ..core.logger import logger
from ..core.constants import PLANNER_AGENT_FEW_SHOT, PLANNER_AGENT_INST, PLANNER_AGENT_SYSPROMPT, NO_WAIT_FUNCTIONS
from flask import g
import concurrent.futures

class PlannerAgent(IAgent):
    def __init__(self, registry):
        self.registry = registry
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)

    def is_no_wait(self, agent_name, payload):
        func = payload.get("function")
        return func in NO_WAIT_FUNCTIONS


    def handle(self, message: MCPInvokeRequest) -> MCPResult:
        _results = []
        g.timer.mark("进入plannerAgent")

        user_id = message.get("payload", {}).get("args", {}).get("user_id", "default")
        user_text = message.get("payload", {}).get("args", {}).get("text", "")
        add_to_short_term(user_id, "user", user_text)

        plan = self._llm_plan(user_text, user_id)
        logger.info(f"plan: {plan}")

        g.timer.mark("plannerAgent调用完成,开始分配任务")

        for agent_entry in plan:
            agent_name = agent_entry.get("agent", "")
            payload = agent_entry.get("payload", {})

            if agent_name not in ["MemoryAgent", "ToolAgent", "SearchAgent"]:
                logger.warning(f"非法 Agent 名称: {agent_name}")
                continue

            agent = self.registry.get(agent_name)
            if not agent:
                logger.warning(f"未注册的 Agent: {agent_name}")
                continue

            task_message = {"agent": agent_name, "payload": payload}

            if self.is_no_wait(agent_name, payload):
                logger.info(f"{payload}添加到并发")
                self.executor.submit(agent.handle, task_message)
            else:
                try:
                    g.timer.mark(f"{agent_name}_开始")
                    result = agent.handle(task_message)
                    g.timer.mark(f"{agent_name}_结束")

                    _results.append({
                        "agent": agent_name,
                        "status": "success",
                        "raw_response": result.get("payload", {})
                    })
                except Exception as e:
                    _results.append({
                        "agent": agent_name,
                        "status": "error",
                        "raw_response": {"error": str(e)}
                    })
                    logger.error(f"Agent 处理异常: {e}")
                finally:
                    message.get("payload").setdefault("args", {"results": _results})

        return self.registry.get("ChatAgent").handle(message)



    def _llm_plan(self, user_text: str,user_id:str) -> list:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        

        full_prompt = f"{PLANNER_AGENT_SYSPROMPT}\n\n{PLANNER_AGENT_INST.format(now_str=now_str, user_id=user_id)}\n\n{PLANNER_AGENT_FEW_SHOT}"

        #reply = call_deepseek(user_message=user_text, system_prompt=full_prompt)
        reply = call_qwen(user_message=user_text, system_prompt=full_prompt)
        try:
            match = re.search(r"```json\s*(.*?)\s*```", reply, re.DOTALL)
            json_text = match.group(1) if match else reply.strip()

            plan = json.loads(json_text)

            # ✅ 判断返回类型是否为你期望的格式：一个含有 agent 字段的 JSON 列表
            if isinstance(plan, list) and all(isinstance(x, dict) and "agent" in x for x in plan):
                return plan
            else:
                logger.error(f"返回内容格式不正确:{plan}", )

        except Exception as e:
            logger.error(f"解析 LLM 返回失败: {e} | 原始返回: {reply}")

        return []
