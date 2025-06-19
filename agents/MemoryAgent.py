##memoryAgent的作用是调取数据库信息   ##同时在每一次chatting结束以后看看是否要收录
from database.services import *
from agents.BaseAgent import BaseAgent
from core.short_memory.memory_buffer import get_short_term,clear_short_term
from core.llm.deepseek_api import call_deepseek


class MemoryAgent(BaseAgent):
    def handle(self,message):
        payload = message.get("payload", {})
        function = payload.get("function")
        args = payload.get("args", {})
        user_id = args.get("user_id")
        if not user_id:
            return {
                "status": "error",
                "payload": {
                    "msg": "缺少 user_id 参数"
                }
            }
        try:
            if function == "add_todo":
                todo = add_todo(**args)
                return {
                    "status": "success",
                    "payload": {
                        "msg": "Todo 添加成功",
                        "id": todo.id
                    }
                }

            elif function == "delete_todo":
                success = delete_todo(args["id"])
                return {
                    "status": "success" if success else "error",
                    "payload": {
                        "msg": "Todo 删除成功" if success else "未找到对应 ID"
                    }
                }

            elif function == "search_todo":
                results = search_todo(**args)
                return {
                    "status": "success",
                    "payload": {
                        "msg": "查询成功",
                        "results": results
                    }
                }

            elif function == "add_memory":

                memory = add_memory(**args)
                return {
                    "status": "success",
                    "payload": {
                        "msg": "Memory 添加成功",
                        "id": memory.id
                    }
            }

            elif function == "delete_memory":

                success = delete_memory(args["memory_id"])
                return {
                "status": "success" if success else "error",
                "payload": {
                    "msg": "Memory 删除成功" if success else "未找到对应 ID"
                    }
            }

            elif function == "search_memory":

                results = search_memory(**args)
                return {
                    "status": "success",
                    "payload": {
                        "msg": "Memory 查询成功",
                        "results": [{"id": r.id,"user_id": r.user_id, "role": r.role, "type": r.type, "content": r.content,
                                     "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S")} for r in results]
                    }
                }

        # ✅ personality 操作

            elif function == "add_personality":
                add_personality(**args)
                return {
                    "status": "success",
                    "payload": {
                        "msg": "Personality 添加或更新成功"
                    }
                }

            elif function == "delete_personality":

                success = delete_personality(**args)
                return {
                    "status": "success" if success else "error",
                    "payload": {
                        "msg": "Personality 删除成功" if success else "未找到对应记录"
                    }
                }

            elif function == "search_personality":

                results = search_personality(**args)
                return {
                    "status": "success",
                    "payload": {
                        "msg": "Personality 查询成功",
                        "results": [{"user_id": r.user_id, "type": r.type.value, "tag": r.tag, "content": r.content} for r in results]
                    }
                }

        # ⛔ 未知函数处理

            else:
                return {
                    "status": "error",
                    "payload": {
                        "msg": f"未知函数: {function}"
                    }
                }


        except Exception as e:
            return {
                "status": "error",
                "payload": {
                    "msg": f"MemoryAgent 执行失败: {str(e)}"
                }
            }

#### --------memory的写入操作---------####
    def write(self, item: dict):
        biao = item.get("biao")
        content = item.get("content")
        user_id = content.get("user_id")
        try:
            if biao == "memory":
                from database.services import add_memory
                add_memory(
                    user_id = user_id,
                    role = content["role"],
                    type = content["type"],
                    content = content["content"],
                )

            elif biao == "personality":
                from database.services import add_personality
                add_personality(
                    user_id = user_id,
                    type = content["type"],
                    tag = content["tag"],
                    content = content["content"],
                )

            else:
                print(f"[MemoryAgent] ❌ 未识别的表名: {biao}")
                return None

        except Exception as e:
            print(f"[MemoryAgent] ❌ 写入失败: {e} | 数据: {item}")
            return None

###-------读的-------------##-------------6.18用户隔离更新：目前因为完全没调用，没有修改user_id部分---------###
    def read(self, biao: str, **kwargs):
        try:
            if biao == "memory":
                from database.services import search_memory
                return search_memory(
                    role=kwargs.get("role"),
                    type=kwargs.get("type")
                )

            elif biao == "personality":
                from database.services import search_personality
                # 统一使用 user_id = "雪"，或 kwargs.get("user_id", "雪")
                return search_personality(
                    user_id=kwargs.get("user_id", "雪"),
                    type=kwargs.get("type"),
                    tag=kwargs.get("tag")
                )

            else:
                print(f"[MemoryAgent] ❌ 未识别的表名: {biao}")
                return None

        except Exception as e:
            print(f"[MemoryAgent] ❌ 读取失败: {e} | 表: {biao}, 参数: {kwargs}")
            return None


### ---------总结--------- ###


    def summarize_and_save(self,user_id = None):
        from app import app
        with app.app_context():
            if user_id is None:
                user_ids = get_all_user_ids_from_memory()
                for uid in user_ids:
                    print(f"[MemoryAgent] 正在总结用户 {uid} 的记忆...")
                    self.summarize_and_save(uid)
                return
    
            memory = get_short_term(user_id)
            if not memory:
                print(f"[MemoryAgent] 用户 {user_id} 无短期记忆可总结")
                return
    
            dialogue = "\n".join([f"{m['role']}：{m['text']}" for m in memory])
            prompt = f"""
            你是一个 AI 记忆助手。以下是一次用户与助手的短期对话内容，请你从中提取**具有长期价值的信息**，并输出标准 JSON 格式的结构化结果。
    
            【提取规则】
    
            - 请仅记录用户明确表达的事实、行为、计划、情绪或偏好；
            - **不是所有内容都需要总结**，如果无法提取，可返回空；
            - 每类信息可以包含 **0 条、1 条或多条**，请使用列表结构；
            - 如果某类信息完全无法提取，该字段可以为空数组，或完全省略。
            - 如对话中包含系统自动反馈的“查询结果”或“历史记忆内容”（如来自数据库的回显），请不要将其重复提取或记录。

            ️ **分类规则必须严格遵守**，请特别注意以下分类约束：
            此外
            【1】当 `"biao": "memory"` 时，type 字段只能是以下五种之一：
            → "fact", "instruction", "emotion", "activity", "daily"
             此类型用于记录用户的行为、情绪、计划、描述性事实等。
            
            【2】当 `"biao": "personality"` 时，type 字段只能是：
            → "personality" 或 "preference"
             此类型用于记录用户的稳定偏好或性格特征（例如：喜欢音乐、讨厌吵闹环境等）。
            
              严禁将 `"preference"` 误写入 `"memory"` 类型中，否则会被丢弃。
            
            【3】请根据内容合理划分，不允许一个对象同时属于两个分类。
            【输出字段说明】
    
            1. memory（列表）：
               用户表达的长期相关行为或信息（如计划、情绪、事实等）；
               每条包含：
               - role: "user" 或 "system"
               - type: one of ["fact", "instruction", "emotion", "activity", "daily"]
               - content: 简洁描述该条信息
    
            2. personality（列表）：
               用户的稳定偏好或性格特征；
               每条包含：
               - type: "personality" 或 "preference"
               - tag: 描述是什么东西/品质（如 "网易云，音乐，懒惰"）
               - content: 对该偏好的解释或引用依据
    
            【格式要求】
    
            - 输出必须是合法 JSON（标准对象，不嵌套字符串）；
            - 不要添加任何额外解释、换行或注释；
            - 所有中文内容请保留原样输出；
            - 示例（结构仅供参考，具体条数不固定）：
    
            [
              {{
                "biao": "memory",
                "content": {{
                  "role": "user",
                  "type": "activity",
                  "content": "我明天要去上野公园散步"
                }}
              }},
              {{
                "biao": "personality",
                "content": {{
                  "type": "preference",
                  "tag": "喜欢自然风景",
                  "content": "用户多次提到喜欢去公园散步"
                }}
              }}
            ]
    
            【原始对话如下】：
            {dialogue}
    
            请仅输出符合结构要求的 JSON。
            """
            try:
                summary_json = call_deepseek(prompt).strip()
                result = eval(summary_json) if isinstance(summary_json, str) else summary_json

                for item in result:
                    item["user_id"] = user_id  # ✅ 加入 user_id
                    self.write(item)

                print("[MemoryAgent] 总结完成并写入成功")
                clear_short_term()

            except Exception as e:
                print(f"[MemoryAgent] 总结失败: {e}")
