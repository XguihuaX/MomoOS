import json
import time
from datetime import datetime
import re
import logging
from core.llm.deepseek_api import call_deepseek
from core.llm.qwen_api import call_qwen
from core.short_memory.memory_buffer import add_to_short_term
from flask import g
import concurrent.futures

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


NO_WAIT_FUNCTIONS = {"add_memory", "add_personality","add_todo","delete_memory","delete_personality", "delete_todo",}

class PlannerAgent:
    def __init__(self, registry):
        self.registry = registry
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)

    def is_no_wait(self, agent_name, payload):
        func = payload.get("function")
        return func in NO_WAIT_FUNCTIONS


    def handle(self, message: dict) -> dict:
        g.timer.mark("进入plannerAgent")

        user_id = message.get("payload", {}).get("user_id", "default")
        user_text = message.get("payload", {}).get("text", "")
        add_to_short_term(user_id, "user", user_text)

        plan = self._llm_plan(user_text, user_id)
        logger.info("plan: %s", plan)

        message["payload"].setdefault("results", [])
        g.timer.mark("plannerAgent调用完成,开始分配任务")

        for agent_entry in plan:
            agent_name = agent_entry.get("agent", "")
            payload = agent_entry.get("payload", {})

            if agent_name not in ["MemoryAgent", "ToolAgent", "SearchAgent"]:
                logger.warning("非法 Agent 名称: %s", agent_name)
                continue

            agent = self.registry.get(agent_name)
            if not agent:
                logger.warning("未注册的 Agent: %s", agent_name)
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

                    message["payload"]["results"].append({
                        "agent": agent_name,
                        "status": "success",
                        "raw_response": result.get("payload", {})
                    })
                except Exception as e:
                    message["payload"]["results"].append({
                        "agent": agent_name,
                        "status": "error",
                        "raw_response": {"error": str(e)}
                    })
                    logger.error("Agent 处理异常: %s", e)

        return self.registry.get("ChatAgent").handle(message)



    def _llm_plan(self, user_text: str,user_id:str) -> list:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        system_prompt = '''
        你是 AI 任务规划器 “PlannerAgent”，用于解析用户自然语言请求，判断意图，并结合各 中间Agent 的职责（MemoryAgent、ToolAgent、SearchAgent），为每个目标 Agent 生成符合 MCP 协议格式的调用消息，包括函数名及所需参数，
        注意：PlannerAgent 自身不会直接调用 ChatAgent，但请注意，ChatAgent 具有联网功能，但如需获取实时信息（如天气、新闻、日期等），应通过调用 SearchAgent 实现联网查询。
        所有中间 Agent（如 MemoryAgent、ToolAgent、SearchAgent）处理完后的结果，都会最终由 ChatAgent 总结归纳呈现给用户，此外chatAgent具有联网功能。
        以下是 MCP 协议消息（目前因为没用调用MCP工具包只缩水为规范json格式）的格式说明和各个中间Agent：
        · MCP 协议格式的调用消息应如下结构：
        {
            "agent": "目标Agent名称",
            "payload": {
            "function": "要调用的函数名",
            "args": {      " // 参数内容，根据实际函数定义填写"
            }
          }
        }

        · MemoryAgent：负责连接数据库，管理所有与用户长期记忆相关的任务，如添加计划、设置闹钟等。操作管理闹钟计划(todos)，查阅与总结长期记忆(Memory）和个人偏好（Personality），记录提醒事项（如闹钟、日程、代办）。
        todos 表字段包括：
        - id: int，系统分配的主键
        - user_id: varchar 用户独立主键
        - owner_type: enum ['alarm', 'agent', 'schedule']，任务类型，
        - title: varchar，调用的功能名
        - description: text，任务描述（如提醒内容）
        - due_time: datetime，执行时间
        - status: enum ['pending', 'completed', 'failed', 'multiple']，任务状态
        - created_at: datetime, 创建时间
        
        Memory 表字段包括:
        - id: int,系统分配的主键
        - user_id: varchar 用户身份id
        - role: enum ['user', 'system']，判断是用户还是系统的记忆.
        - type: enum ['fact', 'instruction', 'emotion', 'activity', 'daily']记录是什么记忆类型，
        - content: text类型，具体内容
        - created_at:分配的创建时间
        
        personality 表字段包括:
        - user_id: varchar，系统分配，当前默认使用 "雪"
        - type: enum ['personality', 'preference']，判断是个人偏好（preference）或性格特质（personality）
        - tag: varchar，**用于表示偏好或性格的关键词（如“音乐”、“咖啡”、“散步”）**，应尽量简洁、可复用
        - content: text，**用于描述偏好的上下文或推理依据**（如“用户提到在咖啡店听歌看书”）
        
        PlannerAgent支持的MemoryAgent中相关可调用函数：
        todo：
        - add_todo(user_id, owner_type, title, description, due_time, status): 添加提醒
        - delete_todo(user_id, id): 删除提醒
        - search_todo(user_id, id=None, owner_type=None, title=None, description=None, status=None, due_start=None, due_end=None, created_start=None, created_end=None):description是模糊查询description内容；due_start / due_end：任务截止时间范围（起始 ≤ due_time < 终止）；created_start / created_end：任务创建时间范围（起始 ≤ created_at < 终止）；
        
        personality:
        - add_personality(user_id, type, tag, content): 添加或更新用户偏好/性格信息，该条需要用户明确添加
        - delete_personality(user_id, type, tag): 删除指定信息
        - search_personality(user_id, type=None, tag=None): 查询用户偏好/性格;
        
        Memory:
        - add_memory(user_id, role, type, content): 添加长期记忆（如用户情绪、行为、指令等）：该条需要用户明确添加
        - delete_memory(user_id, memory_id): 删除指定记忆
        - search_memory(user_id, role=None, type=None, content=None, start_time=None, end_time=None): 按条件查询记忆内容；content：记忆内容模糊搜索（支持部分关键词匹配）; start_time和end_time是对created_at的范围显示。例子：对于start_time和end_time 比如当天，就是start_time就是当天0点，end_time就是第二天0点。
        
        
        
        · ToolAgent：用于执行即时动作，如控制应用程序、智能设备，或获取实时数据，对外调用n8n所有事件（如新闻等）。
        1.ChatAgent角色相关操作：
        - switch_character(user_id:str,character_id: str):切换ChatAgent的角色： 目前character_name支持 ‘默认’ ，'八重神子'，‘神里绫华’，‘凝光’，’荧‘。
        - clear_short_term(user_id:str): 清空聊天记忆。
        
        · SearchAgent：用于联网查询，如天气、实时新闻、股市、日期等； 
        - 如果选用输出格式为：
        {
            "agent": "SearchAgent",
            "payload": {
                "query": "用户的原始问题",
                "user_id": "当前用户 ID"
            }
        }
        query是用户的原query
        '''






        instruction=f'''
        请根据以下步骤完成判断与生成：
        1. 首先判断需要调用哪些 Agent：
           - 若涉及添加提醒、偏好、记忆等长期保存内容 → 使用 MemoryAgent
           - 若是控制软件、设备、角色切换等即时操作 → 使用 ToolAgent
           - 若用户询问需要联网信息（如天气、新闻、时间、节假日、股市等） → 使用 SearchAgent
           - 若不涉及任何行为，仅是问候或闲聊 → 不生成任何调用消息

        2. 判断完成后，为每个目标 Agent 构造符合 MCP 协议格式的调用消息。
        当前时间为 {now_str}（北京时间），请你基于此进行时间推理，due_time 必须为北京时间，格式为 "YYYY-MM-DD HH:MM:SS"，
        ）
        3. user_id应是当前实际用户id，当前的实际用户是：{user_id}
        
        4.给出的消息不得使用注释（如 // 或 #），输出必须为合法 JSON 格式 '''.format(now_str = now_str,user_id=user_id)






        few_shot = """
        以下是示例：
        例子1是一个一次性的闹钟
        输入：请帮我设置明早8点的起床闹钟
        
        输出：
        [
          {
            "agent": "MemoryAgent",
            "payload": {
              "function": "add_todo",
              "args": {
                "user_id": 实际用户id,
                "owner_type": "alarm",
                "title": "alarm",
                "description": "明天早上8点叫我起床",
                "due_time": "要求时间",
                "status": "pending"
              }
            }
          }
        ]
        
        例子2是一个重复型闹钟
        输入：请每天早上7点叫我起床
        输出：
        [
          {
            "agent": "MemoryAgent",
            "payload": {
              "function": "add_todo",
              "args": {
                "user_id": 实际用户id,
                "owner_type": "alarm",
                "title": "alarm",
                "description": "每天早上7点叫我起床",
                "due_time": "要求时间",
                "status": "multiple"
              }
            }
          }
        ]
        
        例子3是一个纯聊天型消息
        输入：早上好呀
        输出
        [
        ]
        
        例子4是一个纯聊天型消息
        输入：上饶的天气怎么样？
        输出:
        [
        ]
        
        例子5：查询长期记忆
        输入：我之前是不是说过我讨厌早起？

        输出：
        [
            {
                "agent": "MemoryAgent",
                "payload": {
                    "function": "search_memory",
                    "args": {
                        "user_id":实际用户id,
                        "role": "user",
                        "type": "emotion"
                    }
                }
            }
        ]

        例子6：查询偏好信息
        输入：我之前都喜欢听什么类型的音乐？

        输出：
        [
            {
                "agent": "MemoryAgent",
                "payload": {
                    "function": "search_personality",
                    "args": {
                        "user_id": 实际用户id,
                        "type": "preference"
                    }
                }
            }
        ]
        
        例子7:切换角色
        输入：请切换角色至八重神子
        
        输出：
        [
            {
                "agent": "ToolAgent",
                "payload": {
                    "function": "switch_character",
                    "args": {
                        "user_id": 实际用户id,
                        "character_id": "八重神子"
                    }
                }
            }
        ]
        例子8：联网查询（天气）
        输入：请查一下今天北京的天气
        输出：
        [
            {
                "agent": "SearchAgent",
                "payload": {
                    "user_id": 实际用户id,
                    "query": "今天北京的天气"
                    }
                }
            }
        ]
        例子9: 清空短期记忆
        输入：清空我刚才的聊天记录
        输出：
        [
            {
                "agent": "ToolAgent",
                "payload": {
                    "user_id": 实际用户id,
                    "function": "clear_short_term",
                    "args": {}
                }
            }
        ]
        """

        full_prompt = f"{system_prompt}\n\n{instruction}\n\n{few_shot}"

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
                logger.error("返回内容格式不正确:", plan)

        except Exception as e:
            logger.error(f"解析 LLM 返回失败: {e} | 原始返回: {reply}")

        return []



