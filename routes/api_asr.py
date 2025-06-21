from flask import Blueprint, request, jsonify
import os, uuid
from ..core.audio.asr_server import recognize_audio

asr_blueprint = Blueprint("asr", __name__)

@asr_blueprint.route("/asr", methods=["POST"])
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
