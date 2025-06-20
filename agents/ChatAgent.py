# agents/ChatAgent.py
from agents.BaseAgent import BaseAgent
from core.llm.qwen_api import call_qwen
from core.message.mcp_message import build_message
from core.short_memory.memory_buffer import add_to_short_term,get_short_term
import requests
import logging
from core.llm.prompt_state import prompt_manager
from flask import g
logger = logging.getLogger(__name__)

class ChatAgent(BaseAgent):
    def handle(self, message):
        try:
            g.timer.mark("进入chatAgent")
            payload = message.get("payload", {})
            mid_result = payload.get("results", None)
            inquiry = payload.get("text", None)
            user_id = message.get("payload", {}).get("user_id", "错误")

            
            short_memory = get_short_term(user_id)
            context = "\n".join([f"{m['role']}：{m['text']}" for m in short_memory]) if short_memory else ""
            history_message = f"【以下是近期对话记录，可用于参考语境】\n{context}\n" if context else ""
            logger.info("[ChatAgent] 用户 %s 的历史记忆：%s", user_id, history_message)


            user_message = f"{history_message}消息：{inquiry}\n反馈：{mid_result}" if inquiry else mid_result


            try:
                cfg = prompt_manager.get_prompt(user_id)
                
                system_prompt = cfg["system_prompt"]
                model_name= cfg["model_name"]
                emotion = cfg["emotion"]
                character = cfg["character_id"]
                logger.info("[ChatAgent] 当前角色配置：%s", character)
            except Exception as e:
                logger.error("[ChatAgent] 获取角色配置出错：%s", str(e))

            
            llm_reply = call_qwen(
                user_message=user_message,
                system_prompt=system_prompt
            )
            
            logger.info("[ChatAgent] LLM 回复内容：%s", llm_reply)
            add_to_short_term(user_id,"ChatAgent", llm_reply)
            logger.info("[ChatAgent] 已将回复加入短期记忆")
            # Step 3️⃣ 调用本地 TTS 接口
            g.timer.mark("chatAgent完成")
            tts_response = requests.post("http://127.0.0.1:5001/api/tts", json={
                "text": llm_reply,
                "emotion": emotion,
                "model_name": model_name,
                "lang": "中文"
            })
            g.timer.mark("语音合成完成")

            if tts_response.status_code == 200:
                tts_data = tts_response.json()
                return build_message(
                    payload={
                        "character": character,
                        "text": tts_data.get("text", llm_reply),
                        "audio": tts_data.get("audio")
                    }
                )
            else:
                return build_message(
                    payload={
                        "character": character,
                        "text": llm_reply,
                        "audio": None,
                        "message": "TTS 接口调用失败"
                    }
                )

        except Exception as e:
            return build_message(
                payload={
                    "message": f"ChatAgent 出错: {str(e)}"
                }
            )
