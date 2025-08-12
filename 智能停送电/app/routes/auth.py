from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash
from app.auth import authenticate_user, login_required
from app.database import get_db_cursor

bp = Blueprint('auth', __name__)

@bp.route('/api/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    print(f"登录尝试: username={username}, password={password}")
    
    if not username or not password:
        return jsonify({"msg": "用户名和密码不能为空"}), 400
    
    user = authenticate_user(username, password)
    print(f"认证结果: {user}")
    
    if user:
        session['user_id'] = user['id']
        return jsonify({
            "msg": "登录成功",
            "id": user['id'],
            "username": user['username'],
            "realname": user['realname'],
            "role": user['role']
        }), 200
    else:
        return jsonify({"msg": "用户名或密码错误"}), 401

@bp.route('/api/logout', methods=['POST'])
@login_required()
def logout():
    """用户登出"""
    session.clear()
    return jsonify({"msg": "登出成功"}), 200

@bp.route('/api/register', methods=['POST'])
def register():
    """用户注册"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    realname = data.get('realname')
    role = data.get('role', 'user')
    
    if not username or not password:
        return jsonify({"msg": "用户名和密码不能为空"}), 400
    
    try:
        with get_db_cursor() as cursor:
            # 检查用户名是否已存在
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            if cursor.fetchone():
                return jsonify({"msg": "用户名已存在"}), 400
            
            # 创建新用户
            hashed_password = generate_password_hash(password)
            cursor.execute("""
                INSERT INTO users (username, password, realname, role)
                VALUES (%s, %s, %s, %s)
            """, (username, hashed_password, realname, role))
            
        return jsonify({"msg": "注册成功"}), 200
    except Exception as e:
        print(f"注册失败: {e}")
        return jsonify({"msg": "注册失败"}), 500 