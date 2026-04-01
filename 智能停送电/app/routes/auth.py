import logging

from flask import Blueprint, jsonify, request, session
from werkzeug.security import generate_password_hash

from app.auth import authenticate_user, login_required
from app.database import get_db_cursor

bp = Blueprint("auth", __name__)
logger = logging.getLogger(__name__)


@bp.route("/api/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"msg": "用户名和密码不能为空"}), 400

    user = authenticate_user(username, password)
    if not user:
        return jsonify({"msg": "用户名或密码错误"}), 401

    session["user_id"] = user["id"]
    return jsonify(
        {
            "msg": "登录成功",
            "id": user["id"],
            "username": user["username"],
            "realname": user["realname"],
            "role": user["role"],
            "function_permissions": user.get("function_permissions", []),
            "room_scopes": user.get("room_scopes", []),
            "access_all_rooms": user.get("access_all_rooms", True),
        }
    ), 200


@bp.route("/api/logout", methods=["POST"])
@login_required()
def logout():
    session.clear()
    return jsonify({"msg": "退出成功"}), 200


@bp.route("/api/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")
    realname = data.get("realname")
    role = data.get("role", "user")

    if not username or not password:
        return jsonify({"msg": "用户名和密码不能为空"}), 400

    try:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            if cursor.fetchone():
                return jsonify({"msg": "用户名已存在"}), 400

            hashed_password = generate_password_hash(password)
            cursor.execute(
                """
                INSERT INTO users (username, password, realname, role)
                VALUES (%s, %s, %s, %s)
                """,
                (username, hashed_password, realname, role),
            )

        return jsonify({"msg": "注册成功"}), 200
    except Exception:
        logger.exception("用户注册失败: username=%s", username)
        return jsonify({"msg": "注册失败"}), 500

