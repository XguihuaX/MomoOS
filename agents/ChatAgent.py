# agents/ChatAgent.py
from ..type_hints.interfaces import IAgent
from ..type_hints.request_type import MCPInvokeRequest
from ..type_hints.result_type import MCPResult
from ..core.llm.qwen_api import call_qwen
from ..core.message.mcp_message import build_message
from ..core.short_memory.memory_buffer import add_to_short_term,get_short_term
from ..core.llm.prompt_state import prompt_manager
from ..core.logger import logger
import requests
from flask import g
from ..core.active_user import active_user_ids

class ChatAgent(IAgent):

    def handle(self, message: MCPInvokeRequest) -> MCPResult:
        try:
            g.timer.mark("进入chatAgent")
            payload = message.get("payload", {})
            mid_result = payload.get("results", None)
            inquiry = payload.get("text", None)
            user_id = message.get("payload", {}).get("user_id", "错误")
            
            
            short_memory = get_short_term(user_id)
            active_user_ids.add(user_id)
            
            context = "\n".join([f"{m['role']}：{m['text']}" for m in short_memory]) if short_memory else ""
            history_message = f"【以下是近期对话记录，可用于参考语境】\n{context}\n" if context else ""
            logger.info(f"用户{user_id}的历史记忆:{history_message}")


            user_message = f"{history_message}消息：{inquiry}\n反馈：{mid_result}" if inquiry else mid_result

            system_prompt = ""
            emotion = ""
            character = ""
            try:
                cfg = prompt_manager.get_prompt(user_id)
                system_prompt = cfg["system_prompt"]
                emotion = cfg["default_emotion"]
                character = cfg["character_id"]
                logger.info(f"当前角色配置：{character}")
            except Exception as e:
                logger.error(f"获取角色配置出错：{e}")
            #cfg = prompt_manager.get_prompt()
            #system_prompt = cfg["system_prompt"]
            #emotion = cfg["default_emotion"]
            #print("[ChatAgent] 当前角色配置：", emotion)  # 加这一行

            
            llm_reply = call_qwen(
                user_message=user_message,
                system_prompt=system_prompt
            )
            
            logger.info(f" LLM 回复内容:{llm_reply}")
            add_to_short_term(user_id,"ChatAgent", llm_reply)
            logger.info(" 已将回复加入短期记忆")
            # Step 3️⃣ 调用本地 TTS 接口
            g.timer.mark("chatAgent完成")
            tts_response = requests.post("http://127.0.0.1:5001/api/tts", json={
                "text": llm_reply,
                "emotion": emotion
            })
            g.timer.mark("语音合成完成")
            logger.info(f"🧪 当前 timer 记录数量: {len(g.timer.timestamps)}")
            if tts_response.status_code == 200:
                tts_data = tts_response.json()
                return build_message(
                    status="success",
                    payload={
                        "character": character,
                        "text": tts_data.get("text", llm_reply),
                        "audio": tts_data.get("audio")
                    }
                )
            else:
                return build_message(
                    status="error",
                    payload={
                        "character": character,
                        "text": llm_reply,
                        "audio": None,
                        "message": "TTS 接口调用失败"
                    }
                )

        except Exception as e:
            return build_message(
                status="error",
                payload={
                    "message": f"ChatAgent 出错: {e}"
                }
            )