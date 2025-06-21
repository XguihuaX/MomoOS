# routes/api_auth.py
from flask import Blueprint, request, jsonify
from ..database.services import create_user
from ..core.logger import logger 
import uuid

auth_blueprint = Blueprint("auth", __name__)

@auth_blueprint.route("/register", methods=["POST"])
def register_user():
    data = request.get_json()
    user_name = data.get("user_name", "").strip()
    
    if not user_name:
        return jsonify({"error": "用户名不能为空"}), 400
    
    try:
        new_user = create_user(user_name)
        return jsonify({
            "success": True,
            "message": "注册成功",
            "data": {
                "user_id": new_user.user_id,
                "user_name": new_user.user_name
            }
        })
    except Exception as e:
        logger.error(f"[注册错误] {str(e)}")
        return jsonify({"success": False, "message": f"注册失败: {str(e)}"}), 500
