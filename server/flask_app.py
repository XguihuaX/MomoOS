""" Flask框架的服务器实现 """
from ..core.exec_hook import set_exechook
set_exechook()
from flask import Flask, request, jsonify
from flask_cors import CORS
import os, atexit, signal, sys, uuid, base64, requests
from ..utils.timer import Timer
from ..utils import toolbox
from ..database.init import db
from ..agents.AgentRegistry import AgentRegistry
from ..agents.PlannerAgent import PlannerAgent
from ..core.audio.generate_audio import generate_audio
from ..core.audio.asr_server import recognize_audio
from ..core.message.mcp_message import build_message
from flask import g
# 初始化
registry = AgentRegistry()
registry.register_default_agents()
planner = PlannerAgent(registry)

app = Flask(__name__)
CORS(app)
app.config.from_pyfile("database/config.py")
db.init_app(app)

with app.app_context():
    conn = db.engine.raw_connection()
    conn.close()

os.makedirs("audio", exist_ok=True)

# ----------- ASR 接口 ------------
@app.route("/api/asr", methods=["POST"])
def api_asr():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "未上传文件"}), 400

    raw_path = os.path.join("audio", f"raw_{uuid.uuid4().hex}.wav")
    file.save(raw_path)

    try:
        result = recognize_audio(raw_path)
        os.remove(raw_path)
        return jsonify({"text": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ----------- TTS 接口 ------------
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
        print("[❌ TTS 错误]:", str(e))
        return jsonify({"error": str(e)}), 500

# ----------- Dispatch 接口 ------------
@app.route("/api/dispatch", methods=["POST"])
def api_dispatch():
    g.timer = Timer()
    if request.content_type.startswith("multipart/form-data"):     ####----------语音部分晚一点改目前都共用雪---------#####
        file = request.files.get("file")
        if not file:
            return jsonify({"error": "未上传语音文件"}), 400

        temp_path = os.path.join("audio", f"temp_{uuid.uuid4().hex}.wav")
        file.save(temp_path)

        try:
            with open(temp_path, "rb") as f:
                response = requests.post("http://127.0.0.1:5001/api/asr", files={"file": f})
            os.remove(temp_path)

            if response.status_code != 200:
                return jsonify({"error": "ASR 识别失败", "detail": response.text}), 500

            asr_result = response.json().get("text", "")
            print(f"[ASR@Dispatch] 识别内容: {asr_result}")
            user_id = request.form.get("user_id","错误")
            message = build_message(status="success", payload={"text": asr_result, "user_id": user_id})
            return handle_frontend(message)

        except Exception as e:
            return jsonify({"error": f"ASR 接口调用失败: {str(e)}"}), 500
    g.timer.mark("语音判定完成")
    data = request.get_json()
    print("[Dispatch] 接收到请求数据:", data)
    source = data.get("source", "unknown")

    if source == "frontend":
        if not isinstance(data, dict) or "text" not in data:
            return jsonify({"error": "请求格式错误：必须包含 'text'" }), 400
        user_id = data.get("user_id","错误")  # 默认值可保留，防止缺失
        message = build_message(status="success", payload={"text": data["text"], "user_id": user_id})
        return handle_frontend(message)

    elif source == "alarm":
        return handle_alarm(data)
    else:
        return jsonify({"error": f"未知 source: {source}"}), 400

def handle_frontend(data):
    print("[Dispatch] Handling frontend request")
    result = planner.handle(data)
    g.timer.report()
    return jsonify({
        "character":result.get("payload",{}).get("character","默认"),
        "text": result.get("payload", {}).get("text", ""),
        "audio": result.get("payload", {}).get("audio", None)
    })

def handle_alarm(data):
    function = data.get("function", "say")
    text = data.get("text", "")
    if function not in ["say", None]:
        try:
            func = getattr(toolbox, function)
            func(text)
        except AttributeError:
            print(f"[Alarm] toolbox 中不存在函数 '{function}'")

    user_id = data.get("user_id", "错误")
    message = {
        "agent": "ChatAgent",
        "payload": {"text": text, "user_id": user_id}
    }

    chat_agent = planner.registry.get("ChatAgent")
    result = chat_agent.handle(message) # type: ignore
    return jsonify({
        "text": result.get("payload", {}).get("text", ""),
        "audio": result.get("payload", {}).get("audio", None)
    })

# ----------- 优雅退出处理 ------------不得已的修改全部的
def on_exit():
    print("[退出] 应用关闭，正在执行记忆总结...")
    try:
        registry.get("MemoryAgent").summarize_and_save()  # ✅ 不传 user_id # type: ignore
    except Exception as e:
        print("[退出] 总结失败:", e)

def handle_shutdown(signum, frame):
    print(f"[信号] 收到退出信号 ({signum})，即将关闭应用...")
    sys.exit(0)

def main_run(host: str = "localhost", port: int = 5001) -> None:
    """ 启动服务 """
    #with app.app_context():
        #scheduler.start_scheduler()
    atexit.register(on_exit)
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    app.run(host=host, port=port)

# ----------- 启动应用 ------------
if __name__ == "__main__":

    main_run()
