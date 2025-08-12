from flask import Blueprint, request, jsonify
from app.database import get_db_cursor
from app.mqtt_client import get_device_status, get_device_history
import time

bp = Blueprint('mp', __name__)

@bp.route('/api/mp/users', methods=['GET'])
def mp_get_users():
    """小程序专用 - 获取用户列表（无认证）"""
    try:
        with get_db_cursor() as cursor:
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

@bp.route('/api/mp/stats', methods=['GET'])
def mp_get_stats():
    """小程序专用 - 获取统计数据（无认证）"""
    try:
        with get_db_cursor() as cursor:
            # 获取申请统计
            cursor.execute("SELECT COUNT(*) as total FROM applications")
            app_count = cursor.fetchone()['total']
            
            # 获取用户统计
            cursor.execute("SELECT role, COUNT(*) as count FROM users GROUP BY role")
            role_stats = {}
            for row in cursor.fetchall():
                role_stats[row['role']] = row['count']
            
            return jsonify({
                "applications": app_count,
                "users": sum(role_stats.values()),
                "role_stats": role_stats
            }), 200
    except Exception as e:
        print(f"获取统计数据失败: {e}")
        return jsonify({"msg": "获取统计数据失败"}), 500

@bp.route('/api/mp/applications', methods=['GET'])
def mp_get_applications():
    """小程序专用 - 获取申请列表（无认证）"""
    try:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT * FROM applications ORDER BY created_at DESC LIMIT 50")
            applications = cursor.fetchall()
            return jsonify(applications), 200
    except Exception as e:
        print(f"获取申请列表失败: {e}")
        return jsonify({"msg": "获取申请列表失败"}), 500

@bp.route('/api/mp/device-status', methods=['GET'])
def mp_get_device_status():
    """小程序专用 - 获取设备状态（无认证）"""
    try:
        device_status = get_device_status()
        devices = []
        
        for device_id, status in device_status.items():
            devices.append({
                'device_id': device_id,
                'status': status
            })
        
        return jsonify(devices), 200
    except Exception as e:
        print(f"获取设备状态失败: {e}")
        return jsonify({"msg": "获取设备状态失败"}), 500

@bp.route('/api/mp/device-history', methods=['GET'])
def mp_get_device_history():
    """小程序专用 - 获取设备历史（无认证）"""
    try:
        device_history = get_device_history()
        return jsonify(device_history), 200
    except Exception as e:
        print(f"获取设备历史失败: {e}")
        return jsonify({"msg": "获取设备历史失败"}), 500

@bp.route('/api/mp/device-alerts', methods=['GET'])
def mp_get_device_alerts():
    """小程序专用 - 获取设备告警（无认证）"""
    try:
        device_status = get_device_status()
        alerts = []
        
        for device_id, status in device_status.items():
            if status.get('status') in ['error', 'offline', 'warning']:
                alerts.append({
                    'device_id': device_id,
                    'status': status.get('status'),
                    'message': f"设备 {device_id} 状态异常: {status.get('status')}",
                    'timestamp': status.get('last_update')
                })
        
        return jsonify(alerts), 200
    except Exception as e:
        print(f"获取设备告警失败: {e}")
        return jsonify({"msg": "获取设备告警失败"}), 500

@bp.route('/api/mp/power-apply', methods=['POST'])
def mp_power_apply():
    """小程序专用 - 停电申请（无认证）"""
    data = request.get_json()
    applicant = data.get('applicant')
    deviceId = data.get('deviceId')
    reason = data.get('reason')
    power_off_time = data.get('power_off_time')
    
    if not applicant or not deviceId or not reason or not power_off_time:
        return jsonify({"msg": "必填信息不能为空"}), 400
    
    try:
        with get_db_cursor() as cursor:
            sql = """
                INSERT INTO applications
                (applicant, deviceId, reason, power_off_time, status)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (applicant, deviceId, reason, power_off_time, 'pending'))
            application_id = cursor.lastrowid
            
        return jsonify({"msg": "申请接收成功", "id": application_id}), 200
    except Exception as e:
        print(f"插入申请异常: {e}")
        return jsonify({"msg": "插入失败", "error": str(e)}), 500

@bp.route('/api/mp/power-on-apply', methods=['POST'])
def mp_power_on_apply():
    """小程序专用 - 送电申请（无认证）"""
    data = request.get_json()
    applicant = data.get('applicant')
    deviceId = data.get('deviceId')
    reason = data.get('reason')
    power_on_time = data.get('power_on_time')
    
    if not applicant or not deviceId or not reason or not power_on_time:
        return jsonify({"msg": "必填信息不能为空"}), 400
    
    try:
        with get_db_cursor() as cursor:
            sql = """
                INSERT INTO applications
                (applicant, deviceId, reason, power_on_time, status, application_type)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (applicant, deviceId, reason, power_on_time, 'pending', 'power_on'))
            application_id = cursor.lastrowid
            
        return jsonify({"msg": "送电申请接收成功", "id": application_id}), 200
    except Exception as e:
        print(f"插入送电申请异常: {e}")
        return jsonify({"msg": "插入失败", "error": str(e)}), 500

@bp.route('/api/mp/my-applications', methods=['GET'])
def mp_get_my_applications():
    """小程序专用 - 获取我的申请（无认证）"""
    applicant = request.args.get('applicant')
    
    if not applicant:
        return jsonify({"msg": "申请人不能为空"}), 400
    
    try:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT * FROM applications WHERE applicant = %s ORDER BY created_at DESC", (applicant,))
            applications = cursor.fetchall()
            return jsonify(applications), 200
    except Exception as e:
        print(f"获取我的申请失败: {e}")
        return jsonify({"msg": "获取申请失败"}), 500

@bp.route('/api/mp/application-detail', methods=['GET'])
def mp_get_application_detail():
    """小程序专用 - 获取申请详情（无认证）"""
    app_id = request.args.get('id')
    
    if not app_id:
        return jsonify({"msg": "申请ID不能为空"}), 400
    
    try:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT * FROM applications WHERE id = %s", (app_id,))
            application = cursor.fetchone()
            
            if not application:
                return jsonify({"msg": "申请不存在"}), 404
            
            return jsonify(application), 200
    except Exception as e:
        print(f"获取申请详情失败: {e}")
        return jsonify({"msg": "获取详情失败"}), 500

@bp.route('/api/mp/approve-application', methods=['POST'])
def mp_approve_application():
    """小程序专用 - 审批申请（无认证）"""
    data = request.get_json()
    app_id = data.get('id')
    approved = data.get('approved')
    approver = data.get('approver')
    comment = data.get('comment', '')
    
    if not app_id or approved is None or not approver:
        return jsonify({"msg": "必填信息不能为空"}), 400
    
    try:
        with get_db_cursor() as cursor:
            # 检查申请状态
            cursor.execute("SELECT status FROM applications WHERE id = %s", (app_id,))
            app = cursor.fetchone()
            if not app:
                return jsonify({"msg": "申请不存在"}), 404
            if app['status'] != 'pending':
                return jsonify({"msg": "申请状态不正确"}), 400
            
            # 更新状态
            new_status = 'approved' if approved else 'rejected'
            sql = """
                UPDATE applications 
                SET status = %s, approver = %s, approve_time = NOW(), approve_comment = %s
                WHERE id = %s
            """
            cursor.execute(sql, (new_status, approver, comment, app_id))
            
        return jsonify({"msg": "审批完成"}), 200
    except Exception as e:
        print(f"审批操作异常: {e}")
        return jsonify({"msg": "审批失败", "error": str(e)}), 500

@bp.route('/api/mp/reject-application', methods=['POST'])
def mp_reject_application():
    """小程序专用 - 拒绝申请（无认证）"""
    data = request.get_json()
    app_id = data.get('id')
    approver = data.get('approver')
    comment = data.get('comment', '')
    
    if not app_id or not approver:
        return jsonify({"msg": "必填信息不能为空"}), 400
    
    try:
        with get_db_cursor() as cursor:
            # 检查申请状态
            cursor.execute("SELECT status FROM applications WHERE id = %s", (app_id,))
            app = cursor.fetchone()
            if not app:
                return jsonify({"msg": "申请不存在"}), 404
            if app['status'] != 'pending':
                return jsonify({"msg": "申请状态不正确"}), 400
            
            # 更新状态
            sql = """
                UPDATE applications 
                SET status = 'rejected', approver = %s, approve_time = NOW(), approve_comment = %s
                WHERE id = %s
            """
            cursor.execute(sql, ('rejected', approver, comment, app_id))
            
        return jsonify({"msg": "拒绝完成"}), 200
    except Exception as e:
        print(f"拒绝操作异常: {e}")
        return jsonify({"msg": "拒绝失败", "error": str(e)}), 500

@bp.route('/api/mp/approve-power-on', methods=['POST'])
def mp_approve_power_on():
    """小程序专用 - 审批送电（无认证）"""
    data = request.get_json()
    app_id = data.get('id')
    approved = data.get('approved')
    approver = data.get('approver')
    comment = data.get('comment', '')
    
    if not app_id or approved is None or not approver:
        return jsonify({"msg": "必填信息不能为空"}), 400
    
    try:
        with get_db_cursor() as cursor:
            # 检查申请状态
            cursor.execute("SELECT status FROM applications WHERE id = %s", (app_id,))
            app = cursor.fetchone()
            if not app:
                return jsonify({"msg": "申请不存在"}), 404
            if app['status'] != 'pending':
                return jsonify({"msg": "申请状态不正确"}), 400
            
            # 更新状态
            new_status = 'approved' if approved else 'rejected'
            sql = """
                UPDATE applications 
                SET status = %s, approver = %s, approve_time = NOW(), approve_comment = %s
                WHERE id = %s
            """
            cursor.execute(sql, (new_status, approver, comment, app_id))
            
        return jsonify({"msg": "送电审批完成"}), 200
    except Exception as e:
        print(f"送电审批操作异常: {e}")
        return jsonify({"msg": "审批失败", "error": str(e)}), 500

@bp.route('/api/mp/reject-power-on', methods=['POST'])
def mp_reject_power_on():
    """小程序专用 - 拒绝送电（无认证）"""
    data = request.get_json()
    app_id = data.get('id')
    approver = data.get('approver')
    comment = data.get('comment', '')
    
    if not app_id or not approver:
        return jsonify({"msg": "必填信息不能为空"}), 400
    
    try:
        with get_db_cursor() as cursor:
            # 检查申请状态
            cursor.execute("SELECT status FROM applications WHERE id = %s", (app_id,))
            app = cursor.fetchone()
            if not app:
                return jsonify({"msg": "申请不存在"}), 404
            if app['status'] != 'pending':
                return jsonify({"msg": "申请状态不正确"}), 400
            
            # 更新状态
            sql = """
                UPDATE applications 
                SET status = 'rejected', approver = %s, approve_time = NOW(), approve_comment = %s
                WHERE id = %s
            """
            cursor.execute(sql, ('rejected', approver, comment, app_id))
            
        return jsonify({"msg": "送电拒绝完成"}), 200
    except Exception as e:
        print(f"送电拒绝操作异常: {e}")
        return jsonify({"msg": "拒绝失败", "error": str(e)}), 500

@bp.route('/api/mp/device-control', methods=['POST'])
def mp_device_control():
    """小程序专用 - 设备控制（无认证）"""
    data = request.get_json()
    device_id = data.get('device_id')
    action = data.get('action')  # 'power_on', 'power_off', 'restart'
    command = data.get('command', '')
    
    if not device_id or not action:
        return jsonify({"msg": "设备ID和操作不能为空"}), 400
    
    try:
        # 这里可以添加实际的设备控制逻辑
        # 目前只是模拟响应
        control_result = {
            'device_id': device_id,
            'action': action,
            'status': 'success',
            'message': f'设备 {device_id} {action} 操作成功',
            'timestamp': time.time()
        }
        
        return jsonify(control_result), 200
    except Exception as e:
        print(f"设备控制操作异常: {e}")
        return jsonify({"msg": "设备控制失败", "error": str(e)}), 500 