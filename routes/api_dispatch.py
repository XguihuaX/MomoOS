from flask import Blueprint, request, jsonify, g
from ..utils.timer import Timer
from ..core.message.mcp_message import build_message
import uuid, os, requests
from ..utils import toolbox
from ..core.logger import logger


def create_dispatch_blueprint(planner):
    dispatch_blueprint = Blueprint("dispatch", __name__)

    @dispatch_blueprint.route("/dispatch", methods=["POST"])
    def api_dispatch():
        g.timer = Timer()

        if request.content_type.startswith("multipart/form-data"):
            file = request.files.get("file")
            if not file:
                logger.warning("未上传语音文件")
                return jsonify({"error": "未上传语音文件"}), 400

            temp_path = os.path.join("audio", f"temp_{uuid.uuid4().hex}.wav")
            file.save(temp_path)
            logger.info(f"收到语音文件，保存至: {temp_path}")

            try:
                with open(temp_path, "rb") as f:
                    response = requests.post("http://127.0.0.1:5001/api/asr", files={"file": f})
                os.remove(temp_path)

                if response.status_code != 200:
                    logger.error(f"ASR 请求失败: {response.text}")
                    return jsonify({"error": "ASR 识别失败", "detail": response.text}), 500

                asr_result = response.json().get("text", "")
                user_id = request.form.get("user_id", "错误")
                logger.info(f"识别内容: {asr_result}")
                message = build_message(status="success", payload={"text": asr_result, "user_id": user_id})
                return handle_frontend(planner, message)

            except Exception as e:
                logger.exception(f"ASR 接口调用异常: {str(e)}")
                return jsonify({"error": f"ASR 接口调用失败: {str(e)}"}), 500

        # 普通 JSON 输入
        data = request.get_json()
        g.timer.mark("语音判定完成")
        logger.info(f"接收到请求数据: {data}")

        source = data.get("source", "unknown")

        if source == "frontend":
            if not isinstance(data, dict) or "text" not in data:
                logger.warning("前端请求格式错误，缺少 text")
                return jsonify({"error": "请求格式错误：必须包含 'text'" }), 400
            user_id = data.get("user_id", "错误")
            message = build_message(status="success", payload={"text": data["text"], "user_id": user_id})
            return handle_frontend(planner, message)

        elif source == "alarm":
            return handle_alarm(planner, data)

        else:
            logger.warning(f"未知 source: {source}")
            return jsonify({"error": f"未知 source: {source}"}), 400

    return dispatch_blueprint


def handle_frontend(planner, data):
    logger.info("Handling frontend request")
    result = planner.handle(data)
    g.timer.report()
    return jsonify({
        "character": result.get("payload", {}).get("character", "默认"),
        "text": result.get("payload", {}).get("text", ""),
        "audio": result.get("payload", {}).get("audio", None)
    })


def handle_alarm(planner, data):
    function = data.get("function", "say")
    text = data.get("text", "")
    user_id = data.get("user_id", "错误")

    logger.info(f"Alarm触发 - function: {function}, text: {text}, user_id: {user_id}")

    if function not in ["say", None]:
        try:
            func = getattr(toolbox, function)
            func(text)
            logger.info(f"执行 toolbox.{function} 成功")
        except AttributeError:
            logger.error(f"toolbox 中不存在函数 '{function}'")

    message = {
        "agent": "ChatAgent",
        "payload": {"text": text, "user_id": user_id}
    }

    chat_agent = planner.registry.get("ChatAgent")
    result = chat_agent.handle(message)

    return jsonify({
        "text": result.get("payload", {}).get("text", ""),
        "audio": result.get("payload", {}).get("audio", None)
    })
