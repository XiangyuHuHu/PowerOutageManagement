import logging
from functools import wraps

from flask import g, jsonify, session
from werkzeug.security import check_password_hash

from app.database import get_db_cursor
from app.services.authz_service import (
    DEFAULT_FUNCTION_PERMISSIONS,
    ensure_user_authz_defaults,
    get_user_function_permissions,
    get_user_room_scopes,
)

logger = logging.getLogger(__name__)

ROLE_PERMISSIONS = {
    "admin": {
        "pages": [
            "admin.html",
            "apply.html",
            "approval.html",
            "repair.html",
            "detail.html",
            "user_management.html",
            "maintenance_batches.html",
            "stats.html",
            "device_monitor.html",
            "notifications.html",
            "approval_history.html",
            "power_on_apply.html",
        ],
        "apis": ["*"],
        "description": "管理员：可查看全部页面和功能",
    },
    "dispatcher": {
        "pages": [
            "approval.html",
            "detail.html",
            "dispatcher_home.html",
            "approval_history.html",
            "device_monitor.html",
            "notifications.html",
        ],
        "apis": ["list", "approve"],
        "description": "调度员：审批、设备监控和通知",
    },
    "electrician": {
        "pages": [
            "apply.html",
            "repair.html",
            "detail.html",
            "electrician_home.html",
            "power_on_apply.html",
            "device_monitor.html",
            "notifications.html",
        ],
        "apis": ["power-apply", "list", "repair-operations", "electrician-verify"],
        "description": "电工：申请、检修、送电申请、设备监控和通知",
    },
    "user": {
        "pages": ["apply.html", "detail.html"],
        "apis": ["power-apply", "list"],
        "description": "普通用户：只可发起申请",
    },
}


def _normalize_builtin_realname(user):
    username = user.get("username")
    builtin_names = {
        "electrician1": "电工李四",
        "dispatcher1": "调度员张三",
        "admin": "管理员",
        "user1": "普通用户",
    }
    if username in builtin_names:
        user["realname"] = builtin_names[username]
    return user


def enrich_user_authz(user):
    user = _normalize_builtin_realname(user)
    role = user.get("role")
    user["function_permissions"] = get_user_function_permissions(user["id"])
    if not user["function_permissions"]:
        user["function_permissions"] = DEFAULT_FUNCTION_PERMISSIONS.get(role, [])
    user["room_scopes"] = get_user_room_scopes(user["id"])
    user["access_all_rooms"] = role == "admin" or len(user["room_scopes"]) == 0
    return user


def user_has_permission(user, permission_code):
    if not permission_code:
        return True
    if user.get("role") == "admin":
        return True
    return permission_code in (user.get("function_permissions") or [])


def user_room_filter_clause(user, table_alias="a"):
    if user.get("access_all_rooms"):
        return "", []
    room_scopes = user.get("room_scopes") or []
    if not room_scopes:
        return "", []
    placeholders = ",".join(["%s"] * len(room_scopes))
    return (
        f" AND COALESCE(d.power_room, '') COLLATE utf8mb4_0900_ai_ci IN ({placeholders})",
        room_scopes,
    )


def login_required(role=None, permission=None):
    """登录校验和权限检查装饰器。"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user_id = session.get("user_id")
            if not user_id:
                return jsonify({"msg": "请先登录"}), 401

            try:
                with get_db_cursor() as cursor:
                    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
                    user = cursor.fetchone()
                    if not user:
                        session.clear()
                        return jsonify({"msg": "用户不存在"}), 401
                    ensure_user_authz_defaults(cursor, user["id"], user.get("role"))

                user = enrich_user_authz(user)
                g.user = user

                if role and user.get("role") != role:
                    return jsonify({"msg": f"需要 {role} 权限"}), 403
                if permission and not user_has_permission(user, permission):
                    return jsonify({"msg": "无此功能权限"}), 403

                return func(*args, **kwargs)
            except Exception:
                logger.exception("认证检查失败")
                return jsonify({"msg": "认证失败"}), 500

        return wrapper

    return decorator


def page_permission_required(page_name):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user = g.user
            if not user:
                return jsonify({"msg": "请先登录"}), 401

            role = user.get("role")
            if role not in ROLE_PERMISSIONS:
                return jsonify({"msg": "无权限访问此页面"}), 403

            if page_name not in ROLE_PERMISSIONS[role]["pages"]:
                return jsonify({"msg": "无权限访问此页面"}), 403

            return func(*args, **kwargs)

        return wrapper

    return decorator


def authenticate_user(username, password):
    try:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
            if not user:
                return None

            stored_password = user["password"]
            if stored_password == password or check_password_hash(stored_password, password):
                ensure_user_authz_defaults(cursor, user["id"], user.get("role"))
                return enrich_user_authz(user)
            return None
    except Exception:
        logger.exception("用户认证失败: username=%s", username)
        return None


def get_user_by_id(user_id):
    try:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            if not user:
                return None
            ensure_user_authz_defaults(cursor, user["id"], user.get("role"))
        return enrich_user_authz(user)
    except Exception:
        logger.exception("获取用户失败: user_id=%s", user_id)
        return None
