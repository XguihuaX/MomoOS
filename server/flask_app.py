from ..core.exec_hook import set_exechook
set_exechook()
from flask import Flask, request, jsonify
from flask_cors import CORS
import os, atexit, signal, sys
from ..utils.timer import Timer
from ..database.init import db
from ..agents.AgentRegistry import AgentRegistry
from ..agents.PlannerAgent import PlannerAgent
from ..core.logger import logger
from ..core.audio.generate_audio import generate_audio
import os, atexit, signal, sys, uuid, base64, requests

# 初始化注册中心与总控 Planner
registry = AgentRegistry()
registry.register_default_agents()
planner = PlannerAgent(registry)

# 创建 Flask 应用
app = Flask(__name__)
CORS(app)
config_path = os.path.join(os.path.dirname(__file__), "../database/config.py")
app.config.from_pyfile(os.path.abspath(config_path))
db.init_app(app)

with app.app_context():
    conn = db.engine.raw_connection()
    conn.close()

# 创建音频文件夹
os.makedirs("audio", exist_ok=True)

# 注册路由模块
from ..routes.api_asr import asr_blueprint
from ..routes.api_dispatch import create_dispatch_blueprint
from ..routes.api_auth import auth_blueprint

app.register_blueprint(asr_blueprint, url_prefix="/api/asr")
app.register_blueprint(create_dispatch_blueprint(planner), url_prefix="/api")
app.register_blueprint(auth_blueprint, url_prefix="/api/auth")


# ✅ 保留的 TTS 接口
@app.route("/api/tts", methods=["POST"])
def api_tts():
    data = request.get_json()
    agent_reply = data.get("text")
    emotion = data.get("emotion", "八重神子默认")

    if not agent_reply:
        return jsonify({"error": "缺少 text 参数"}), 400

    try:
        temp_path = f"/tmp/temp_{uuid.uuid4().hex}.wav"
        output_path = generate_audio(text=agent_reply, emotion=emotion, filename=temp_path)

        with open(output_path, "rb") as f:
            audio_data = f.read()
        audio_base64 = base64.b64encode(audio_data).decode("utf-8")

        return jsonify({
            "text": agent_reply,
            "audio": audio_base64
        })
    except Exception as e:
        logger.error(f"[❌ TTS 错误]: {str(e)}")
        return jsonify({"error": str(e)}), 500
        
# ----------- 优雅退出处理 ------------
def on_exit():
    logger.info("[退出] 应用关闭，正在执行记忆总结...")
    try:
        registry.get("MemoryAgent").summarize_and_save()  # type: ignore
    except Exception as e:
        logger.error(f"[退出] 总结失败: {e}")

def handle_shutdown(signum, frame):
    logger.info(f"[信号] 收到退出信号 ({signum})，即将关闭应用...")
    sys.exit(0)

def main_run(host: str = "0.0.0.0", port: int = 5001) -> None:
    atexit.register(on_exit)
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)
    app.run(host=host, port=port)

# ----------- 启动应用 ------------
if __name__ == "__main__":
    main_run()
