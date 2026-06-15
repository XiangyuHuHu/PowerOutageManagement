from flask import Flask, request, jsonify, send_from_directory, session, g
from flask_cors import CORS
from flask_session import Session
import pymysql
import pymysql.cursors
import threading
import os
import webbrowser
import time
import socket
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import json
import paho.mqtt.client as mqtt
from zeroconf import ServiceBrowser, Zeroconf
import logging
from datetime import datetime

app = Flask(__name__)
# 使用环境变量或生成随机密钥
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24).hex())
app.config['SESSION_TYPE'] = 'filesystem'
app.config['JSON_AS_ASCII'] = False  # 确保 JSON 响应支持中文
Session(app)
CORS(app, supports_credentials=True)  # 允许跨域带 cookie

# MQTT 配置
MQTT_BROKER = os.environ.get('MQTT_BROKER', '192.168.1.123')
MQTT_PORT = int(os.environ.get('MQTT_PORT', 1883))
MQTT_TOPIC = "devices/+/status"

# MQTT 客户端
mqtt_client = None

# --- MQTT 回调函数 ---
def on_connect(client, userdata, flags, rc):
    print(f"✅ 已连接到 MQTT Broker：{MQTT_BROKER}:{MQTT_PORT}")
    client.subscribe(MQTT_TOPIC)
    print(f"📡 已订阅主题：{MQTT_TOPIC}")

# 设备状态存储
DEVICE_STATUS = {}
DEVICE_HISTORY = []

def on_message(client, userdata, msg):
    payload = msg.payload.decode(errors='ignore')  # 解码为字符串，忽略编码错误
    print(f"📥 收到 MQTT 消息：\n  Topic   : {msg.topic}")

    try:
        # 尝试按 JSON 解码
        data = json.loads(payload)
        print(f"  Payload : JSON 格式\n{json.dumps(data, indent=2, ensure_ascii=False)}\n")
        
        # 处理设备状态消息
        process_device_message(data)
        
    except json.JSONDecodeError:
        # 不是 JSON，就直接输出原始内容
        print(f"  Payload : 原始字符串（非 JSON）\n{payload}\n")

def process_device_message(data):
    """处理设备状态消息"""
    try:
        # 提取设备信息
        device_id = data.get('device_id', data.get('deviceId', 'unknown'))
        status = data.get('status', 'unknown')
        timestamp = data.get('timestamp', time.time())
        
        # 更新设备状态
        DEVICE_STATUS[device_id] = {
            'status': status,
            'last_update': timestamp,
            'data': data
        }
        
        # 添加到历史记录（保留最近100条）
        history_entry = {
            'device_id': device_id,
            'status': status,
            'timestamp': timestamp,
            'data': data
        }
        DEVICE_HISTORY.append(history_entry)
        
        # 保持历史记录在合理范围内
        if len(DEVICE_HISTORY) > 100:
            DEVICE_HISTORY.pop(0)
        
        print(f"📊 设备状态更新: {device_id} -> {status}")
        
        # 检查异常状态
        check_device_alerts(device_id, status, data)
        
    except Exception as e:
        print(f"❌ 处理设备消息失败: {e}")

def check_device_alerts(device_id, status, data):
    """检查设备异常状态"""
    alert_conditions = {
        'offline': '设备离线',
        'error': '设备错误',
        'overload': '设备过载',
        'temperature_high': '温度过高',
        'voltage_high': '电压过高',
        'voltage_low': '电压过低'
    }
    
    if status in alert_conditions:
        alert_message = f"设备 {device_id} {alert_conditions[status]}"
        print(f"🚨 设备告警: {alert_message}")
        
        # 可以在这里添加告警通知逻辑
        # 比如发送到数据库、推送到前端等

# --- 启动 MQTT 监听 ---
def start_mqtt_listener():
    global mqtt_client
    try:
        mqtt_client = mqtt.Client()
        mqtt_client.on_connect = on_connect
        mqtt_client.on_message = on_message
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        
        # 在后台线程中运行 MQTT 循环
        def mqtt_loop():
            mqtt_client.loop_forever()
        
        mqtt_thread = threading.Thread(target=mqtt_loop, daemon=True)
        mqtt_thread.start()
        print(f"🔌 MQTT 监听已启动，连接到 {MQTT_BROKER}:{MQTT_PORT}")
    except Exception as e:
        print(f"❌ MQTT 连接失败：{e}")

# --- 自动发现 MQTT Broker ---
def discover_mqtt_broker():
    class MQTTListener:
        def __init__(self):
            self.broker_ip = None

        def remove_service(self, zeroconf, type, name):
            pass

        def add_service(self, zeroconf, type, name):
            info = zeroconf.get_service_info(type, name)
            if info and info.addresses:
                ip = ".".join(str(b) for b in info.addresses[0])
                print(f"发现 MQTT Broker: {ip}:{info.port}")
                self.broker_ip = ip

    try:
        zeroconf = Zeroconf()
        listener = MQTTListener()
        browser = ServiceBrowser(zeroconf, "_mqtt._tcp.local.", listener)
        
        time.sleep(3)  # 等待发现
        
        if listener.broker_ip:
            print("自动发现到 Broker:", listener.broker_ip)
            return listener.broker_ip
        else:
            print("未发现 Broker，使用默认配置")
            return None
    except Exception as e:
        print(f"自动发现失败：{e}")
        return None

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 系统监控指标
SYSTEM_METRICS = {
    'total_requests': 0,
    'successful_requests': 0,
    'failed_requests': 0,
    'active_users': set(),
    'last_activity': {}
}

@app.before_request
def before_request():
    # 小程序API无需认证检查
    if request.path.startswith('/api/mp/'):
        # 记录请求
        SYSTEM_METRICS['total_requests'] += 1
        logger.info(f"Mini-program API: {request.method} {request.path}")
        g.start_time = time.time()
        return  # 直接返回，不进行认证检查

    # 记录请求
    SYSTEM_METRICS['total_requests'] += 1

    # 记录活跃用户
    if 'user' in session:
        user_id = session['user'].get('id')
        if user_id:
            SYSTEM_METRICS['active_users'].add(user_id)
            SYSTEM_METRICS['last_activity'][user_id] = datetime.now()

    # 记录请求日志
    logger.info(f"Request: {request.method} {request.path} - User: {session.get('user', {}).get('username', 'anonymous')}")
    g.start_time = time.time()

@app.after_request
def after_request(response):
    # 记录响应状态
    if response.status_code < 400:
        SYSTEM_METRICS['successful_requests'] += 1
    else:
        SYSTEM_METRICS['failed_requests'] += 1

    return response

# 数据库连接配置
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),  # 本地MySQL
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', 'hxy19990606'),
    'database': os.environ.get('DB_NAME', 'power_control'),
    'charset': 'utf8',
    'cursorclass': pymysql.cursors.DictCursor
}

# 数据库连接函数
def get_db():
    db = pymysql.connect(**DB_CONFIG)
    # 手动设置字符编码
    with db.cursor() as cursor:
        cursor.execute("SET NAMES utf8mb4")
        cursor.execute("SET CHARACTER SET utf8mb4")
        cursor.execute("SET character_set_connection=utf8mb4")
    return db

# --- 工具函数：登录校验装饰器 ---
def login_required(role=None):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            user = session.get("user")
            if not user:
                return jsonify({"msg": "未登录"}), 401
            if role and user.get("role") != role:
                return jsonify({"msg": "权限不足"}), 403
            g.user = user  # 可在接口里直接用 g.user 拿当前登录用户
            return f(*args, **kwargs)
        return wrapper
    return decorator

# --- 页面服务 ---
@app.route('/')
def index():
    return send_from_directory('web_pages', 'login.html')

@app.route('/<path:filename>')
def serve_html(filename):
    # API路径不处理，让其他路由处理
    if filename.startswith('api/'):
        return jsonify({"msg": "API路径不存在"}), 404
        
    # 登录和注册页面无需权限检查
    if filename in ['login.html', 'register.html']:
        return send_from_directory('web_pages', filename)
    # 其他页面需要权限检查
    user = session.get('user')
    if not user:
        return jsonify({"msg": "请先登录"}), 401
    role = user.get('role')
    if role not in ROLE_PERMISSIONS:
        return jsonify({"msg": "无效角色"}), 403
    if filename not in ROLE_PERMISSIONS[role]['pages']:
        return jsonify({"msg": "无权限访问此页面"}), 403
    return send_from_directory('web_pages', filename)

# --- 登录 ---
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return jsonify({"msg": "请求数据为空"}), 400
        
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({"msg": "用户名和密码不能为空"}), 400
    
    try:
        db = get_db()
        if not db:
            return jsonify({"msg": "数据库连接失败，请稍后重试"}), 500
            
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
            user = cursor.fetchone()
            if user:
                # 添加调试信息
                print(f"DEBUG: 从数据库获取的realname: {user['realname']}")
                print(f"DEBUG: realname类型: {type(user['realname'])}")
                print(f"DEBUG: realname字节: {user['realname'].encode('utf-8')}")
                
                # 硬编码修复字符编码问题
                realname = user["realname"]
                if username == "electrician1":
                    realname = "电工李四"
                elif username == "dispatcher1":
                    realname = "调度员张三"
                elif username == "admin":
                    realname = "管理员"
                elif username == "user1":
                    realname = "普通用户A"
                
                session["user"] = {
                    "id": user["id"],
                    "username": user["username"],
                    "role": user["role"],
                    "realname": realname
                }
                return jsonify({
                    "msg": "登录成功",
                    "id": user["id"],
                    "username": user["username"],
                    "role": user["role"],
                    "realname": realname
                }), 200
            else:
                return jsonify({"msg": "用户名或密码错误"}), 401
    except Exception as e:
        print(f"登录异常: {e}")
        return jsonify({"msg": "登录失败", "error": str(e)}), 500

# --- 注销 ---
@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"msg": "已退出登录"})

# --- 用户注册 ---
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data:
        return jsonify({"msg": "请求数据为空"}), 400
        
    username = data.get('username')
    password = data.get('password')
    realname = data.get('realname')
    role = data.get('role')
    
    # 验证必填字段
    if not username or not password or not realname or not role:
        return jsonify({"msg": "所有字段都是必填的"}), 400
    
    # 验证用户名长度
    if len(username) < 3:
        return jsonify({"msg": "用户名至少需要3个字符"}), 400
    
    # 验证密码长度
    if len(password) < 6:
        return jsonify({"msg": "密码至少需要6个字符"}), 400
    
    # 验证角色
    if role not in ['electrician', 'dispatcher']:
        return jsonify({"msg": "无效的角色选择"}), 400
    
    try:
        db = get_db()
        if not db:
            return jsonify({"msg": "数据库连接失败，请稍后重试"}), 500
            
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            # 检查用户名是否已存在
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            existing_user = cursor.fetchone()
            if existing_user:
                return jsonify({"msg": "用户名已存在"}), 400
            
            # 插入新用户
            sql = """
                INSERT INTO users (username, password, realname, role)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(sql, (username, password, realname, role))
            db.commit()
            
            return jsonify({
                "msg": "注册成功",
                "username": username,
                "realname": realname,
                "role": role
            }), 200
            
    except Exception as e:
        print(f"注册异常: {e}")
        return jsonify({"msg": "注册失败", "error": str(e)}), 500

# --- 获取用户列表（管理员权限） ---
@app.route('/api/users', methods=['GET'])
@login_required(role="admin")
def get_users():
    try:
        with get_db().cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT id, username, realname, role, created_at FROM users ORDER BY created_at DESC")
            users = cursor.fetchall()
            
            # 修复字符编码问题
            for user in users:
                username = user['username']
                realname = user['realname']
                
                # 硬编码修复字符编码问题
                if username == "electrician1":
                    user['realname'] = "电工李四"
                elif username == "dispatcher1":
                    user['realname'] = "调度员张三"
                elif username == "admin":
                    user['realname'] = "管理员"
                elif username == "user1":
                    user['realname'] = "普通用户A"
                else:
                    # 对于新注册的用户，尝试使用原始数据
                    user['realname'] = realname
            
            return jsonify(users), 200
    except Exception as e:
        return jsonify({"msg": "查询失败", "error": str(e)}), 500

# --- 删除用户（管理员权限） ---
@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@login_required(role="admin")
def delete_user(user_id):
    try:
        with get_db().cursor(pymysql.cursors.DictCursor) as cursor:
            # 检查用户是否存在
            cursor.execute("SELECT role FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            if not user:
                return jsonify({"msg": "用户不存在"}), 404
            
            # 不允许删除管理员
            if user['role'] == 'admin':
                return jsonify({"msg": "不能删除管理员账户"}), 400
            
            # 删除用户
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
            db.commit()
            
            return jsonify({"msg": "用户删除成功"}), 200
    except Exception as e:
        return jsonify({"msg": "删除失败", "error": str(e)}), 500

# --- 更新用户信息（管理员权限） ---
@app.route('/api/users/<int:user_id>', methods=['PUT'])
@login_required(role="admin")
def update_user(user_id):
    data = request.get_json()
    if not data:
        return jsonify({"msg": "请求数据为空"}), 400
    
    realname = data.get('realname')
    role = data.get('role')
    password = data.get('password')
    
    # 验证必填字段
    if not realname:
        return jsonify({"msg": "真实姓名不能为空"}), 400
    
    if not role:
        return jsonify({"msg": "角色不能为空"}), 400
    
    # 验证角色
    if role not in ['admin', 'dispatcher', 'electrician', 'user']:
        return jsonify({"msg": "无效的角色"}), 400
    
    try:
        db = get_db()
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            # 检查用户是否存在
            cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            if not user:
                return jsonify({"msg": "用户不存在"}), 404
            
            # 构建更新SQL
            update_fields = []
            update_values = []
            
            update_fields.append("realname = %s")
            update_values.append(realname)
            
            update_fields.append("role = %s")
            update_values.append(role)
            
            # 如果提供了密码，则更新密码
            if password:
                if len(password) < 6:
                    return jsonify({"msg": "密码至少需要6个字符"}), 400
                update_fields.append("password = %s")
                update_values.append(password)
            
            # 添加用户ID到更新值列表
            update_values.append(user_id)
            
            # 执行更新
            sql = f"UPDATE users SET {', '.join(update_fields)} WHERE id = %s"
            cursor.execute(sql, update_values)
            db.commit()
            
            return jsonify({"msg": "用户信息更新成功"}), 200
    except Exception as e:
        return jsonify({"msg": "更新失败", "error": str(e)}), 500

# --- 申请提交：所有登录人都可提交 ---
@app.route('/api/power-apply', methods=['POST'])
@login_required()  # 必须登录
def power_apply():
    data = request.get_json()
    user = g.user
    applicant = user.get('realname') or user.get('username')
    applicant_id = user.get('id')
    deviceId = data.get('deviceId')
    reason = data.get('reason')
    operation_task = data.get('operation_task', '')
    ticket_template = data.get('ticket_template', '')
    power_off_time = data.get('power_off_time')
    power_on_time = data.get('power_on_time', '')
    if not applicant or not applicant_id or not deviceId or not reason or not power_off_time:
        return jsonify({"msg": "必填信息不能为空"}), 400
    try:
        db = get_db()
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            sql = """
                INSERT INTO applications
                (applicant, applicant_id, deviceId, reason, operation_task, ticket_template, 
                 power_off_time, power_on_time, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (
                applicant, applicant_id, deviceId, reason, operation_task, ticket_template,
                power_off_time, power_on_time, 'pending'
            ))
            db.commit()
            application_id = cursor.lastrowid
            
            # 记录操作日志
            log_sql = """
                INSERT INTO application_logs
                (application_id, operator, operator_id, operation_type, operation_comment, old_status, new_status)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(log_sql, (
                application_id, applicant, applicant_id, 'create', '电申请', '', 'pending'
            ))
            db.commit()
            
            # 创建通知：给所有调度员发送申请通知
            try:
                with db.cursor(pymysql.cursors.DictCursor) as notify_cursor:
                    notify_cursor.execute("SELECT id FROM users WHERE role = 'dispatcher'")
                    dispatchers = notify_cursor.fetchall()
                    
                    for dispatcher in dispatchers:
                        create_notification(
                            title=f"新的停电申请 - #{application_id}",
                            content=f"申请人：{applicant}\n设备：{deviceId}\n原因：{reason}\n请及时审批。",
                            notification_type='warning',
                            user_id=dispatcher['id']
                        )
                    
                    # 给申请人发送确认通知
                    create_notification(
                        title=f"申请提交成功 - #{application_id}",
                        content=f"您的停电申请已提交成功，正在等待审批。",
                        notification_type='success',
                        user_id=applicant_id
                    )
            except Exception as e:
                print(f"创建通知失败: {e}")
            
            return jsonify({"msg": "申请接收成功", "id": application_id}), 200
    except Exception as e:
        print("插入申请异常：", e)
        return jsonify({"msg": "插入失败", "error": str(e)}), 500

# --- 获取申请列表：根据角色过滤 ---
@app.route('/api/list', methods=['GET'])
@login_required()
def get_list():
    user = g.user
    role = user.get('role')
    user_id = user.get('id')
    
    # 获取查询参数
    status = request.args.get('status')
    applicant = request.args.get('applicant')
    device_id = request.args.get('device_id')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    try:
        with get_db().cursor(pymysql.cursors.DictCursor) as cursor:
            # 构建基础查询
            base_query = "SELECT * FROM applications WHERE 1=1"
            params = []
            
            # 根据角色过滤
            if role == 'admin':
                # 管理员看所有
                pass
            elif role == 'dispatcher':
                # 调度员看所有（包括历史记录）
                pass
            elif role == 'electrician':
                # 电工看自己提交的所有申请 + 需要验电、检修的申请
                base_query += " AND (applicant_id = %s OR status IN ('approved', 'verified', 'repairing', 'repair_completed'))"
                params.append(user_id)
            else:
                # 普通用户只看自己的申请
                base_query += " AND applicant_id = %s"
                params.append(user_id)
            
            # 添加筛选条件
            if status:
                base_query += " AND status = %s"
                params.append(status)
            
            if applicant:
                base_query += " AND applicant LIKE %s"
                params.append(f"%{applicant}%")
            
            if device_id:
                base_query += " AND deviceId LIKE %s"
                params.append(f"%{device_id}%")
            
            if date_from:
                base_query += " AND created_at >= %s"
                params.append(date_from)
            
            if date_to:
                base_query += " AND created_at <= %s"
                params.append(date_to)
            
            base_query += " ORDER BY created_at DESC"
            
            cursor.execute(base_query, params)
            return jsonify(cursor.fetchall())
    except Exception as e:
        return jsonify({"msg": "查询失败", "error": str(e)}), 500

# --- 停电审批：调度员审批 ---
@app.route('/api/power-off-approve', methods=['POST'])
@login_required(role="dispatcher")
def power_off_approve():
    data = request.get_json()
    app_id = data.get('id')
    approve_action = data.get('action')  # 'approve' 或 'reject'
    comment = data.get('comment', '')
    
    user = g.user
    approver = user.get('realname') or user.get('username')
    approver_id = user.get('id')
    
    try:
        db = get_db()
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            # 检查申请状态
            cursor.execute("SELECT status FROM applications WHERE id = %s", (app_id,))
            app = cursor.fetchone()
            if not app:
                return jsonify({"msg": "申请不存在"}), 404
            if app['status'] != 'pending':
                return jsonify({"msg": "申请状态不正确"}), 400
            # 更新状态
            new_status = 'approved' if approve_action == 'approve' else 'rejected'
            sql = """
                UPDATE applications 
                SET status = %s, power_off_approver = %s, power_off_approver_id = %s,
                    power_off_approve_time = NOW(), power_off_approve_comment = %s
                WHERE id = %s
            """
            cursor.execute(sql, (new_status, approver, approver_id, comment, app_id))
            db.commit()
            
            # 记录操作日志
            log_sql = """
                INSERT INTO application_logs
                (application_id, operator, operator_id, operation_type, operation_comment, old_status, new_status)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(log_sql, (
                app_id, approver, approver_id, 'power_off_approve', comment, 'pending', new_status
            ))
            db.commit()
            
            # 获取申请人信息
            cursor.execute("SELECT applicant_id, applicant FROM applications WHERE id = %s", (app_id,))
            application = cursor.fetchone()
            
            # 创建通知：给申请人发送审批结果通知
            if application:
                notification_type = 'success' if approve_action == 'approve' else 'error'
                notification_title = f"申请审批结果 - #{app_id}"
                notification_content = f"您的申请已{'通过' if approve_action == 'approve' else '被驳回'}。\n审批人：{approver}\n审批意见：{comment or '无'}"
                
                create_notification(
                    title=notification_title,
                    content=notification_content,
                    notification_type=notification_type,
                    user_id=application['applicant_id']
                )
            
            return jsonify({"msg": "审批完成", "status": new_status}), 200
    except Exception as e:
        print("审批操作异常：", e)
        return jsonify({"msg": "审批失败", "error": str(e)}), 500

# --- 电工验电：电工确认安全措施 ---
@app.route('/api/electrician-verify', methods=['POST'])
@login_required(role='electrician')
def electrician_verify():
    data = request.get_json()
    app_id = data.get('id')
    safety_measures = data.get('safety_measures', '')
    comment = data.get('comment', '')
    
    user = g.user
    verifier = user.get('realname') or user.get('username')
    verifier_id = user.get('id')
    
    try:
        db = get_db()
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            # 检查申请状态
            cursor.execute("SELECT status FROM applications WHERE id = %s", (app_id,))
            app = cursor.fetchone()
            if not app:
                return jsonify({"msg": "申请不存在"}), 404
            if app['status'] != 'approved':
                return jsonify({"msg": "申请状态不正确"}), 400
            # 更新状态
            sql = """
                UPDATE applications 
                SET status = 'verified', electrician_verifier = %s, electrician_verifier_id = %s,
                    electrician_verify_time = NOW(), electrician_verify_comment = %s,
                    safety_measures = %s
                WHERE id = %s
            """
            cursor.execute(sql, (verifier, verifier_id, comment, safety_measures, app_id))
            db.commit()
            
            # 记录操作日志
            log_sql = """
                INSERT INTO application_logs
                (application_id, operator, operator_id, operation_type, operation_comment, old_status, new_status)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(log_sql, (
                app_id, verifier, verifier_id, 'electrician_verify', comment, 'approved', 'verified'
            ))
            db.commit()
            
            return jsonify({"msg": "验电完成"}), 200
    except Exception as e:
        print("验电操作异常：", e)
        return jsonify({"msg": "验电失败", "error": str(e)}), 500

# --- 检修操作：电工开始/结束检修 ---
@app.route('/api/repair-operation', methods=['POST'])
@login_required(role='electrician')
def repair_operation():
    data = request.get_json()
    app_id = data.get('id')
    operation = data.get('operation')  # 'start' 或 'end'
    comment = data.get('comment', '')
    
    user = g.user
    operator = user.get('realname') or user.get('username')
    operator_id = user.get('id')
    
    try:
        db = get_db()
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            # 检查申请状态
            cursor.execute("SELECT status FROM applications WHERE id = %s", (app_id,))
            app = cursor.fetchone()
            if not app:
                return jsonify({"msg": "申请不存在"}), 404
            if operation == 'start':
                if app['status'] != 'verified':
                    return jsonify({"msg": "申请状态不正确"}), 400
                new_status = 'repairing'
                sql = """
                    UPDATE applications 
                    SET status = %s, repair_operator = %s, repair_operator_id = %s,
                        repair_start_time = NOW(), repair_comment = %s
                    WHERE id = %s
                """
                cursor.execute(sql, (new_status, operator, operator_id, comment, app_id))
            else:  # end
                if app['status'] != 'repairing':
                    return jsonify({"msg": "申请状态不正确"}), 400
                new_status = 'repair_completed'
                sql = """
                    UPDATE applications 
                    SET status = %s, repair_end_time = NOW(), repair_comment = %s
                    WHERE id = %s
                """
                cursor.execute(sql, (new_status, comment, app_id))
            db.commit()
            
            # 记录操作日志
            log_sql = """
                INSERT INTO application_logs
                (application_id, operator, operator_id, operation_type, operation_comment, old_status, new_status)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(log_sql, (
                app_id, operator, operator_id, f'repair_{operation}', comment, app['status'], new_status
            ))
            db.commit()
            
            return jsonify({"msg": f"检修{operation}完成"}), 200
    except Exception as e:
        print("检修操作异常：", e)
        return jsonify({"msg": "检修操作失败", "error": str(e)}), 500

# --- 送电申请：电工申请送电 ---
@app.route('/api/power-on-apply', methods=['POST'])
@login_required(role='electrician')
def power_on_apply():
    data = request.get_json()
    app_id = data.get('id')
    comment = data.get('comment', '')
    power_on_time = data.get('power_on_time', '')
    
    user = g.user
    applicant = user.get('realname') or user.get('username')
    applicant_id = user.get('id')
    
    try:
        db = get_db()
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            # 检查申请状态
            cursor.execute("SELECT status FROM applications WHERE id = %s", (app_id,))
            app = cursor.fetchone()
            if not app:
                return jsonify({"msg": "申请不存在"}), 404
            if app['status'] not in ['approved', 'verified', 'repair_completed']:
                return jsonify({"msg": "申请状态不正确"}), 400
            # 更新状态
            sql = """
                UPDATE applications 
                SET status = 'power_on_applied', power_on_applicant = %s, power_on_applicant_id = %s,
                    power_on_apply_time = NOW(), power_on_time = %s
                WHERE id = %s
            """
            cursor.execute(sql, (applicant, applicant_id, power_on_time, app_id))
            db.commit()
            
            # 记录操作日志
            log_sql = """
                INSERT INTO application_logs
                (application_id, operator, operator_id, operation_type, operation_comment, old_status, new_status)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(log_sql, (
                app_id, applicant, applicant_id, 'power_on_apply', comment, app['status'], 'power_on_applied'
            ))
            db.commit()
            
            return jsonify({"msg": "送电申请提交成功"}), 200
    except Exception as e:
        print("送电申请异常：", e)
        return jsonify({"msg": "送电申请失败", "error": str(e)}), 500

# --- 送电审批：调度员审批送电 ---
@app.route('/api/power-on-approve', methods=['POST'])
@login_required(role="dispatcher")
def power_on_approve():
    data = request.get_json()
    app_id = data.get('id')
    approve_action = data.get('action')  # 'approve' 或 'reject'
    comment = data.get('comment', '')
    
    user = g.user
    approver = user.get('realname') or user.get('username')
    approver_id = user.get('id')
    
    try:
        db = get_db()
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            # 检查申请状态
            cursor.execute("SELECT * FROM applications WHERE id = %s", (app_id,))
            app = cursor.fetchone()
            if not app:
                return jsonify({"msg": "申请不存在"}), 404
            if app['status'] != 'power_on_applied':
                return jsonify({"msg": "申请状态不正确"}), 400
            deviceId = app['deviceId']
            # 校验同设备下所有相关申请都已进入送电申请状态
            cursor.execute("""
                SELECT * FROM applications
                WHERE deviceId = %s AND status IN ('approved', 'verified', 'repairing', 'repair_completed', 'power_on_applied')
            """, (deviceId,))
            rows = cursor.fetchall()
            if any(row['status'] != 'power_on_applied' for row in rows):
                return jsonify({"msg": "所有电工都需完成作业并申请送电，才能审批送电！"}), 400
            # 更新状态
            new_status = 'completed' if approve_action == 'approve' else 'power_on_rejected'
            sql = """
                UPDATE applications 
                SET status = %s, power_on_approver = %s, power_on_approver_id = %s,
                    power_on_approve_time = NOW(), power_on_approve_comment = %s,
                    completed_time = NOW()
                WHERE id = %s
            """
            cursor.execute(sql, (new_status, approver, approver_id, comment, app_id))
            db.commit()
            # 记录操作日志
            log_sql = """
                INSERT INTO application_logs
                (application_id, operator, operator_id, operation_type, operation_comment, old_status, new_status)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(log_sql, (
                app_id, approver, approver_id, 'power_on_approve', comment, 'power_on_applied', new_status
            ))
            db.commit()
            return jsonify({"msg": "送电审批完成", "status": new_status}), 200
    except Exception as e:
        print("送电审批异常：", e)
        return jsonify({"msg": "送电审批失败", "error": str(e)}), 500

# --- 获取申请详情 ---
@app.route('/api/application/<int:app_id>', methods=['GET'])
@login_required()
def get_application_detail(app_id):
    try:
        with get_db().cursor(pymysql.cursors.DictCursor) as cursor:
            # 获取申请详情
            cursor.execute("SELECT * FROM applications WHERE id = %s", (app_id,))
            application = cursor.fetchone()
            if not application:
                return jsonify({"msg": "申请不存在"}), 404
            # 获取操作日志
            cursor.execute("""
                SELECT * FROM application_logs 
                WHERE application_id = %s 
                ORDER BY operation_time ASC
            """, (app_id,))
            logs = cursor.fetchall()
            
            return jsonify({
                "application": application,
                "logs": logs
            }), 200
    except Exception as e:
        return jsonify({"msg": "查询失败", "error": str(e)}), 500

# --- 导出申请数据（管理员权限） ---
@app.route('/api/export/applications', methods=['GET'])
@login_required(role="admin")
def export_applications():
    try:
        with get_db().cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("""
                SELECT 
                    a.id,
                    a.applicant,
                    a.deviceId,
                    a.type,
                    a.status,
                    a.reason,
                    a.power_off_time,
                    a.power_on_time,
                    a.created_at,
                    a.power_off_approver,
                    a.power_off_approve_time,
                    a.power_on_applicant,
                    a.power_on_apply_time,
                    a.power_on_approver,
                    a.power_on_approve_time
                FROM applications a
                ORDER BY a.created_at DESC
            """)
            applications = cursor.fetchall()
            
            # 生成CSV内容
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # 写入表头
            writer.writerow([
                '申请ID', '申请人', '设备ID', '申请类型', '状态', '原因',
                '停电时间', '送电时间', '申请时间', '停电审批人', '停电审批时间',
                '送电申请人', '送电申请时间', '送电审批人', '送电审批时间'
            ])
            
            # 写入数据
            for app in applications:
                writer.writerow([
                    app['id'],
                    app['applicant'],
                    app['deviceId'],
                    '停电' if app['type'] == 'power_off' else '送电',
                    app['status'],
                    app['reason'],
                    app['power_off_time'],
                    app['power_on_time'],
                    app['created_at'],
                    app['power_off_approver'],
                    app['power_off_approve_time'],
                    app['power_on_applicant'],
                    app['power_on_apply_time'],
                    app['power_on_approver'],
                    app['power_on_approve_time']
                ])
            
            output.seek(0)
            
            from flask import Response
            return Response(
                output.getvalue(),
                mimetype='text/csv',
                headers={'Content-Disposition': 'attachment; filename=applications.csv'}
            )
            
    except Exception as e:
        return jsonify({"msg": "导出失败", "error": str(e)}), 500

# --- 权限配置 ---
ROLE_PERMISSIONS = {
    'admin': {
        'pages': ['admin.html', 'apply.html', 'approval.html', 'repair.html', 'detail.html', 'user_management.html', 'stats.html', 'device_monitor.html', 'notifications.html'],
        'apis': ['power-apply', 'list', 'approve', 'admin-stats', 'users', 'delete-user', 'update-user'],
        'description': '管理员：可查看所有页面和功能'
    },
    'dispatcher': {
        'pages': ['approval.html', 'detail.html', 'dispatcher_home.html', 'approval_history.html', 'device_monitor.html', 'notifications.html'],
        'apis': ['list', 'approve'],
        'description': '调度员：审批、设备监控和通知'
    },
    'electrician': {
        'pages': ['apply.html', 'repair.html', 'detail.html', 'electrician_home.html', 'power_on_apply.html', 'device_monitor.html', 'notifications.html'],
        'apis': ['power-apply', 'list', 'repair-operations', 'electrician-verify'],
        'description': '电工：申请、检修、设备监控和通知'
    },
    'user': {
        'pages': ['apply.html', 'detail.html'],
        'apis': ['power-apply', 'list'],
        'description': '普通用户：只能申请'
    }
}

# --- 页面权限检查装饰器 ---
def page_permission_required(page_name):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            user = session.get("user")
            if not user:
                return jsonify({"msg": "未登录"}), 401
            role = user.get("role")
            if role not in ROLE_PERMISSIONS:
                return jsonify({"msg": "无效角色"}), 403

            if page_name not in ROLE_PERMISSIONS[role]['pages']:
                return jsonify({"msg": "无权限访问此页面"}), 403

            return f(*args, **kwargs)
        return wrapper
    return decorator

# --- 获取系统通知 ---
@app.route('/api/notifications', methods=['GET'])
@login_required()
def get_notifications():
    try:
        with get_db().cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("""
                SELECT id, title, content, type, created_at, is_read
                FROM notifications 
                WHERE user_id = %s OR user_id IS NULL
                ORDER BY created_at DESC
                LIMIT 20
            """, (g.user.get('id'),))
            notifications = cursor.fetchall()
            return jsonify(notifications), 200
    except Exception as e:
        return jsonify({"msg": "获取通知失败", "error": str(e)}), 500

# --- 标记通知为已读 ---
@app.route('/api/notifications/<int:notification_id>/read', methods=['PUT'])
@login_required()
def mark_notification_read(notification_id):
    try:
        with get_db().cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("""
                UPDATE notifications 
                SET is_read = 1 
                WHERE id = %s AND (user_id = %s OR user_id IS NULL)
            """, (notification_id, g.user.get('id')))
            db.commit()
            return jsonify({"msg": "标记成功"}), 200
    except Exception as e:
        return jsonify({"msg": "操作失败", "error": str(e)}), 500

# --- 创建通知的辅助函数 ---
def create_notification(title, content, notification_type='info', user_id=None):
    """创建通知"""
    try:
        db = get_db()
        with db.cursor() as cursor:
            sql = """
                INSERT INTO notifications (user_id, title, content, type)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(sql, (user_id, title, content, notification_type))
            db.commit()
            return True
    except Exception as e:
        print(f"创建通知失败: {e}")
        return False

# --- 获取系统监控数据 ---
@app.route('/api/system/metrics', methods=['GET'])
@login_required(role="admin")
def get_system_metrics():
    try:
        # 清理过期的活跃用户（30分钟无活动）
        current_time = datetime.now()
        expired_users = []
        for user_id, last_activity in SYSTEM_METRICS['last_activity'].items():
            if (current_time - last_activity).seconds > 1800:  # 30分钟
                expired_users.append(user_id)
        
        for user_id in expired_users:
            SYSTEM_METRICS['active_users'].discard(user_id)
            del SYSTEM_METRICS['last_activity'][user_id]
        
        return jsonify({
            'total_requests': SYSTEM_METRICS['total_requests'],
            'successful_requests': SYSTEM_METRICS['successful_requests'],
            'failed_requests': SYSTEM_METRICS['failed_requests'],
            'active_users_count': len(SYSTEM_METRICS['active_users']),
            'success_rate': round(SYSTEM_METRICS['successful_requests'] / max(SYSTEM_METRICS['total_requests'], 1) * 100, 2)
        }), 200
    except Exception as e:
        return jsonify({"msg": "获取监控数据失败", "error": str(e)}), 500

# --- 自动打开浏览器 ---
def open_browser():
    time.sleep(1)
    webbrowser.open("http://localhost:5050")

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = 'localhost'
    finally:
        s.close()
    return ip

# --- 小程序API路由（无认证）---
@app.route('/api/mp/users', methods=['GET'])
def mp_get_users():
    """小程序专用 - 获取用户列表（无认证）"""
    try:
        db = get_db()
        if not db:
            return jsonify({"msg": "数据库连接失败"}), 500
            
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT id, username, realname, role, created_at FROM users ORDER BY created_at DESC")
            users = cursor.fetchall()
            
            # 硬编码修复字符编码问题
            for user in users:
                username = user["username"]
                if username == "electrician1":
                    user["realname"] = "电工李四"
                elif username == "dispatcher1":
                    user["realname"] = "调度员张三"
                elif username == "admin":
                    user["realname"] = "管理员"
                elif username == "user1":
                    user["realname"] = "普通用户A"
            
            return jsonify(users), 200
    except Exception as e:
        print(f"获取用户列表失败: {e}")
        return jsonify({"msg": "获取用户列表失败"}), 500

@app.route('/api/mp/stats', methods=['GET'])
def mp_get_stats():
    """小程序专用 - 获取统计数据（无认证）"""
    try:
        db = get_db()
        if not db:
            return jsonify({"msg": "数据库连接失败"}), 500
            
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            # 获取申请统计
            cursor.execute("SELECT COUNT(*) as total FROM applications")
            app_count = cursor.fetchone()['total']
            
            # 获取用户统计
            cursor.execute("SELECT COUNT(*) as total FROM users")
            user_count = cursor.fetchone()['total']
            
            # 获取各角色用户数量
            cursor.execute("SELECT role, COUNT(*) as count FROM users GROUP BY role")
            role_stats = cursor.fetchall()
            
            stats = {
                "applications": app_count,
                "users": user_count,
                "role_stats": {row['role']: row['count'] for row in role_stats}
            }
            
            return jsonify(stats), 200
    except Exception as e:
        print(f"获取统计数据失败: {e}")
        return jsonify({"msg": "获取统计数据失败"}), 500

@app.route('/api/mp/applications', methods=['GET'])
def mp_get_applications():
    """小程序专用 - 获取申请列表（无认证）"""
    try:
        db = get_db()
        if not db:
            return jsonify({"msg": "数据库连接失败"}), 500
            
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("""
                SELECT a.*, u.realname as applicant_name 
                FROM applications a 
                LEFT JOIN users u ON a.applicant_id = u.id 
                ORDER BY a.created_at DESC
            """)
            applications = cursor.fetchall()
            
            # 硬编码修复字符编码问题
            for app in applications:
                if app['applicant_name']:
                    username = app.get('applicant', '')
                    if username == "electrician1":
                        app['applicant_name'] = "电工李四"
                    elif username == "dispatcher1":
                        app['applicant_name'] = "调度员张三"
                    elif username == "admin":
                        app['applicant_name'] = "管理员"
                    elif username == "user1":
                        app['applicant_name'] = "普通用户A"
            
            return jsonify(applications), 200
    except Exception as e:
        print(f"获取申请列表失败: {e}")
        return jsonify({"msg": "获取申请列表失败"}), 500

@app.route('/api/mp/power-apply', methods=['POST'])
def mp_power_apply():
    """小程序专用 - 提交停电申请（无认证）"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"msg": "请求数据为空"}), 400
            
        applicant = data.get('applicant')
        date = data.get('date')
        device_id = data.get('deviceId')
        reason = data.get('reason')
        
        if not all([applicant, date, device_id, reason]):
            return jsonify({"msg": "请填写完整信息"}), 400
            
        db = get_db()
        if not db:
            return jsonify({"msg": "数据库连接失败"}), 500
            
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            # 获取用户ID
            cursor.execute("SELECT id FROM users WHERE realname = %s OR username = %s", (applicant, applicant))
            user = cursor.fetchone()
            if not user:
                return jsonify({"msg": "用户不存在"}), 400
                
            # 插入申请记录
            cursor.execute("""
                INSERT INTO applications (applicant_id, applicant, device_id, reason, power_off_time, status, type, created_at)
                VALUES (%s, %s, %s, %s, %s, 'pending', 'power_off', NOW())
            """, (user['id'], applicant, device_id, reason, date))
            
            db.commit()
            return jsonify({"msg": "申请提交成功"}), 200
            
    except Exception as e:
        print(f"提交申请失败: {e}")
        return jsonify({"msg": "提交申请失败"}), 500

@app.route('/api/mp/power-on-apply', methods=['POST'])
def mp_power_on_apply():
    """小程序专用 - 提交送电申请（无认证）"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"msg": "请求数据为空"}), 400
            
        application_id = data.get('id')
        if not application_id:
            return jsonify({"msg": "申请ID不能为空"}), 400
            
        db = get_db()
        if not db:
            return jsonify({"msg": "数据库连接失败"}), 500
            
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            # 检查申请是否存在且状态正确
            cursor.execute("SELECT * FROM applications WHERE id = %s", (application_id,))
            application = cursor.fetchone()
            
            if not application:
                return jsonify({"msg": "申请不存在"}), 400
                
            if application['status'] not in ['approved', 'verified', 'repairing', 'repair_completed']:
                return jsonify({"msg": "申请状态不允许送电"}), 400
                
            # 更新申请状态
            cursor.execute("UPDATE applications SET status = 'power_on_applied' WHERE id = %s", (application_id,))
            db.commit()
            
            return jsonify({"msg": "送电申请提交成功"}), 200
            
    except Exception as e:
        print(f"提交送电申请失败: {e}")
        return jsonify({"msg": "提交送电申请失败"}), 500

@app.route('/api/mp/my-applications', methods=['GET'])
def mp_get_my_applications():
    """小程序专用 - 获取我的申请列表（无认证）"""
    try:
        applicant = request.args.get('applicant')
        if not applicant:
            return jsonify({"msg": "申请人参数不能为空"}), 400
            
        db = get_db()
        if not db:
            return jsonify({"msg": "数据库连接失败"}), 500
            
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("""
                SELECT a.*, u.realname as applicant_name 
                FROM applications a 
                LEFT JOIN users u ON a.applicant_id = u.id 
                WHERE a.applicant = %s
                ORDER BY a.created_at DESC
            """, (applicant,))
            applications = cursor.fetchall()
            
            # 硬编码修复字符编码问题
            for app in applications:
                if app['applicant_name']:
                    username = app.get('applicant', '')
                    if username == "electrician1":
                        app['applicant_name'] = "电工李四"
                    elif username == "dispatcher1":
                        app['applicant_name'] = "调度员张三"
                    elif username == "admin":
                        app['applicant_name'] = "管理员"
                    elif username == "user1":
                        app['applicant_name'] = "普通用户A"
            
            return jsonify(applications), 200
    except Exception as e:
        print(f"获取我的申请列表失败: {e}")
        return jsonify({"msg": "获取申请列表失败"}), 500

@app.route('/api/mp/application-detail', methods=['GET'])
def mp_get_application_detail():
    """小程序专用 - 获取申请详情（无认证）"""
    try:
        application_id = request.args.get('id')
        if not application_id:
            return jsonify({"msg": "申请ID不能为空"}), 400
            
        db = get_db()
        if not db:
            return jsonify({"msg": "数据库连接失败"}), 500
            
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("""
                SELECT a.*, u.realname as applicant_name 
                FROM applications a 
                LEFT JOIN users u ON a.applicant_id = u.id 
                WHERE a.id = %s
            """, (application_id,))
            application = cursor.fetchone()
            
            if not application:
                return jsonify({"msg": "申请不存在"}), 404
            
            # 硬编码修复字符编码问题
            if application['applicant_name']:
                username = application.get('applicant', '')
                if username == "electrician1":
                    application['applicant_name'] = "电工李四"
                elif username == "dispatcher1":
                    application['applicant_name'] = "调度员张三"
                elif username == "admin":
                    application['applicant_name'] = "管理员"
                elif username == "user1":
                    application['applicant_name'] = "普通用户A"
            
            # 添加审批历史（模拟数据）
            application['approval_history'] = [
                {
                    'time': application['created_at'],
                    'status': 'pending',
                    'operator': application['applicant_name'] or application['applicant'],
                    'comment': '申请提交'
                }
            ]
            
            return jsonify(application), 200
    except Exception as e:
        print(f"获取申请详情失败: {e}")
        return jsonify({"msg": "获取申请详情失败"}), 500

@app.route('/api/mp/approve-application', methods=['POST'])
def mp_approve_application():
    """小程序专用 - 审批通过申请（无认证）"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"msg": "请求数据为空"}), 400
            
        application_id = data.get('id')
        if not application_id:
            return jsonify({"msg": "申请ID不能为空"}), 400
            
        db = get_db()
        if not db:
            return jsonify({"msg": "数据库连接失败"}), 500
            
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            # 检查申请是否存在且状态正确
            cursor.execute("SELECT * FROM applications WHERE id = %s", (application_id,))
            application = cursor.fetchone()
            
            if not application:
                return jsonify({"msg": "申请不存在"}), 400
                
            if application['status'] != 'pending':
                return jsonify({"msg": "申请状态不允许审批"}), 400
                
            # 更新申请状态
            cursor.execute("UPDATE applications SET status = 'approved' WHERE id = %s", (application_id,))
            db.commit()
            
            return jsonify({"msg": "审批通过成功"}), 200
            
    except Exception as e:
        print(f"审批申请失败: {e}")
        return jsonify({"msg": "审批申请失败"}), 500

@app.route('/api/mp/reject-application', methods=['POST'])
def mp_reject_application():
    """小程序专用 - 驳回申请（无认证）"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"msg": "请求数据为空"}), 400
            
        application_id = data.get('id')
        if not application_id:
            return jsonify({"msg": "申请ID不能为空"}), 400
            
        db = get_db()
        if not db:
            return jsonify({"msg": "数据库连接失败"}), 500
            
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            # 检查申请是否存在且状态正确
            cursor.execute("SELECT * FROM applications WHERE id = %s", (application_id,))
            application = cursor.fetchone()
            
            if not application:
                return jsonify({"msg": "申请不存在"}), 400
                
            if application['status'] != 'pending':
                return jsonify({"msg": "申请状态不允许驳回"}), 400
                
            # 更新申请状态
            cursor.execute("UPDATE applications SET status = 'rejected' WHERE id = %s", (application_id,))
            db.commit()
            
            return jsonify({"msg": "驳回成功"}), 200
            
    except Exception as e:
        print(f"驳回申请失败: {e}")
        return jsonify({"msg": "驳回申请失败"}), 500

@app.route('/api/mp/approve-power-on', methods=['POST'])
def mp_approve_power_on():
    """小程序专用 - 同意送电（无认证）"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"msg": "请求数据为空"}), 400
            
        application_id = data.get('id')
        if not application_id:
            return jsonify({"msg": "申请ID不能为空"}), 400
            
        db = get_db()
        if not db:
            return jsonify({"msg": "数据库连接失败"}), 500
            
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            # 检查申请是否存在且状态正确
            cursor.execute("SELECT * FROM applications WHERE id = %s", (application_id,))
            application = cursor.fetchone()
            
            if not application:
                return jsonify({"msg": "申请不存在"}), 400
                
            if application['status'] != 'power_on_applied':
                return jsonify({"msg": "申请状态不允许送电审批"}), 400
                
            # 更新申请状态
            cursor.execute("UPDATE applications SET status = 'completed' WHERE id = %s", (application_id,))
            db.commit()
            
            return jsonify({"msg": "送电审批通过成功"}), 200
            
    except Exception as e:
        print(f"送电审批失败: {e}")
        return jsonify({"msg": "送电审批失败"}), 500

@app.route('/api/mp/reject-power-on', methods=['POST'])
def mp_reject_power_on():
    """小程序专用 - 拒绝送电申请（无认证）"""
    try:
        data = request.get_json()
        app_id = data.get('id')
        
        if not app_id:
            return jsonify({"msg": "缺少申请ID"}), 400
            
        db = get_db()
        if not db:
            return jsonify({"msg": "数据库连接失败"}), 500
            
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            # 更新申请状态
            cursor.execute("""
                UPDATE applications 
                SET status = 'power_on_rejected', 
                    updated_at = NOW() 
                WHERE id = %s
            """, (app_id,))
            
            if cursor.rowcount > 0:
                db.commit()
                return jsonify({"msg": "送电申请已拒绝"}), 200
            else:
                return jsonify({"msg": "申请不存在"}), 404
                
    except Exception as e:
        print(f"拒绝送电申请失败: {e}")
        return jsonify({"msg": "操作失败"}), 500

# --- 设备状态API ---
@app.route('/api/mp/device-status', methods=['GET'])
def mp_get_device_status():
    """小程序专用 - 获取设备状态（无认证）"""
    try:
        device_id = request.args.get('device_id')
        
        if device_id:
            # 获取特定设备状态
            device_status = DEVICE_STATUS.get(device_id)
            if device_status:
                return jsonify({
                    "device_id": device_id,
                    "status": device_status
                }), 200
            else:
                return jsonify({"msg": "设备不存在"}), 404
        else:
            # 获取所有设备状态
            return jsonify({
                "devices": DEVICE_STATUS,
                "total": len(DEVICE_STATUS)
            }), 200
            
    except Exception as e:
        print(f"获取设备状态失败: {e}")
        return jsonify({"msg": "获取设备状态失败"}), 500

@app.route('/api/mp/device-history', methods=['GET'])
def mp_get_device_history():
    """小程序专用 - 获取设备历史记录（无认证）"""
    try:
        device_id = request.args.get('device_id')
        limit = int(request.args.get('limit', 20))
        
        if device_id:
            # 获取特定设备的历史记录
            device_history = [
                entry for entry in DEVICE_HISTORY 
                if entry['device_id'] == device_id
            ]
            device_history = device_history[-limit:]  # 取最近N条
        else:
            # 获取所有设备的历史记录
            device_history = DEVICE_HISTORY[-limit:]
        
        return jsonify({
            "history": device_history,
            "total": len(device_history)
        }), 200
        
    except Exception as e:
        print(f"获取设备历史记录失败: {e}")
        return jsonify({"msg": "获取设备历史记录失败"}), 500

@app.route('/api/mp/device-alerts', methods=['GET'])
def mp_get_device_alerts():
    """小程序专用 - 获取设备告警信息（无认证）"""
    try:
        # 检查所有设备的异常状态
        alerts = []
        alert_conditions = {
            'offline': '设备离线',
            'error': '设备错误',
            'overload': '设备过载',
            'temperature_high': '温度过高',
            'voltage_high': '电压过高',
            'voltage_low': '电压过低'
        }
        
        for device_id, status_info in DEVICE_STATUS.items():
            status = status_info.get('status')
            if status in alert_conditions:
                alerts.append({
                    'device_id': device_id,
                    'status': status,
                    'message': alert_conditions[status],
                    'timestamp': status_info.get('last_update')
                })
        
        return jsonify({
            "alerts": alerts,
            "total": len(alerts)
        }), 200
        
    except Exception as e:
        print(f"获取设备告警失败: {e}")
        return jsonify({"msg": "获取设备告警失败"}), 500

@app.route('/api/mp/device-control', methods=['POST'])
def mp_device_control():
    """小程序专用 - 设备控制命令（无认证）"""
    try:
        data = request.get_json()
        device_id = data.get('device_id')
        command = data.get('command')
        params = data.get('params', {})
        
        if not device_id or not command:
            return jsonify({"msg": "缺少设备ID或命令"}), 400
        
        # 这里可以添加设备控制逻辑
        # 比如通过MQTT发送控制命令到设备
        
        control_message = {
            'device_id': device_id,
            'command': command,
            'params': params,
            'timestamp': time.time()
        }
        
        # 发送控制命令到MQTT（如果MQTT客户端可用）
        if mqtt_client:
            control_topic = f"device/{device_id}/control"
            mqtt_client.publish(control_topic, json.dumps(control_message))
            print(f"📤 发送控制命令: {device_id} -> {command}")
        
        return jsonify({
            "msg": "控制命令已发送",
            "device_id": device_id,
            "command": command
        }), 200
        
    except Exception as e:
        print(f"设备控制失败: {e}")
        return jsonify({"msg": "设备控制失败"}), 500

if __name__ == '__main__':
    lan_ip = get_ip()
    print("🚀 Flask 后端启动：http://localhost:5050")
    print(f"🚀 局域网访问地址：http://{lan_ip}:5050")
    
    # 启动 MQTT 监听
    print("🔌 启动 MQTT 监听...")
    start_mqtt_listener()
    
    # 只在主进程自动打开一次浏览器
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        threading.Thread(target=open_browser).start()
    app.run(host='0.0.0.0', port=5050, debug=True)
