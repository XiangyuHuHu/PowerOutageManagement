from flask import Blueprint, request, jsonify, g
from app.auth import login_required
from app.database import get_db_cursor
from app.notifications import notify_dispatchers_new_application, notify_applicant_confirmation, notify_approval_result

bp = Blueprint('api', __name__)

@bp.route('/api/power-apply', methods=['POST'])
@login_required()
def power_apply():
    """停电申请"""
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
        with get_db_cursor() as cursor:
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
            
            # 创建通知
            notify_dispatchers_new_application(application_id, applicant, deviceId, reason)
            notify_applicant_confirmation(application_id, applicant_id)
            
        return jsonify({"msg": "申请接收成功", "id": application_id}), 200
    except Exception as e:
        print("插入申请异常：", e)
        return jsonify({"msg": "插入失败", "error": str(e)}), 500

@bp.route('/api/list', methods=['GET'])
@login_required()
def get_list():
    """获取申请列表"""
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
        with get_db_cursor() as cursor:
            # 构建基础查询
            base_query = "SELECT * FROM applications WHERE 1=1"
            params = []
            
            # 根据角色过滤
            if role == 'admin':
                pass  # 管理员看所有
            elif role == 'dispatcher':
                pass  # 调度员看所有
            elif role == 'electrician':
                base_query += " AND (applicant_id = %s OR status IN ('approved', 'verified', 'repairing', 'repair_completed'))"
                params.append(user_id)
            else:
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

@bp.route('/api/power-off-approve', methods=['POST'])
@login_required(role="dispatcher")
def power_off_approve():
    """停电审批"""
    data = request.get_json()
    app_id = data.get('id')
    approve_action = data.get('action')
    comment = data.get('comment', '')
    
    user = g.user
    approver = user.get('realname') or user.get('username')
    approver_id = user.get('id')
    
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
            new_status = 'approved' if approve_action == 'approve' else 'rejected'
            sql = """
                UPDATE applications 
                SET status = %s, power_off_approver = %s, power_off_approver_id = %s,
                    power_off_approve_time = NOW(), power_off_approve_comment = %s
                WHERE id = %s
            """
            cursor.execute(sql, (new_status, approver, approver_id, comment, app_id))
            
            # 记录操作日志
            log_sql = """
                INSERT INTO application_logs
                (application_id, operator, operator_id, operation_type, operation_comment, old_status, new_status)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(log_sql, (
                app_id, approver, approver_id, 'power_off_approve', comment, 'pending', new_status
            ))
            
            # 获取申请人信息并发送通知
            cursor.execute("SELECT applicant_id, applicant FROM applications WHERE id = %s", (app_id,))
            application = cursor.fetchone()
            
            if application:
                notify_approval_result(app_id, application['applicant_id'], approve_action == 'approve', approver, comment)
            
        return jsonify({"msg": "审批完成", "status": new_status}), 200
    except Exception as e:
        print("审批操作异常：", e)
        return jsonify({"msg": "审批失败", "error": str(e)}), 500

@bp.route('/api/notifications', methods=['GET'])
@login_required()
def get_notifications():
    """获取用户通知"""
    user = g.user
    user_id = user.get('id')
    
    try:
        from app.notifications import get_user_notifications
        notifications = get_user_notifications(user_id)
        return jsonify(notifications), 200
    except Exception as e:
        return jsonify({"msg": "获取通知失败", "error": str(e)}), 500

@bp.route('/api/notifications/<int:notification_id>/read', methods=['PUT'])
@login_required()
def mark_notification_read(notification_id):
    """标记通知为已读"""
    user = g.user
    user_id = user.get('id')
    
    try:
        from app.notifications import mark_notification_read
        success = mark_notification_read(notification_id, user_id)
        if success:
            return jsonify({"msg": "标记成功"}), 200
        else:
            return jsonify({"msg": "标记失败"}), 500
    except Exception as e:
        return jsonify({"msg": "标记失败", "error": str(e)}), 500

@bp.route('/api/electrician-verify', methods=['POST'])
@login_required(role='electrician')
def electrician_verify():
    """电工验电：电工确认安全措施"""
    data = request.get_json()
    app_id = data.get('id')
    safety_measures = data.get('safety_measures', '')
    comment = data.get('comment', '')
    
    user = g.user
    verifier = user.get('realname') or user.get('username')
    verifier_id = user.get('id')
    
    try:
        with get_db_cursor() as cursor:
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
            
            # 记录操作日志
            log_sql = """
                INSERT INTO application_logs
                (application_id, operator, operator_id, operation_type, operation_comment, old_status, new_status)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(log_sql, (
                app_id, verifier, verifier_id, 'electrician_verify', comment, 'approved', 'verified'
            ))
            
        return jsonify({"msg": "验电完成"}), 200
    except Exception as e:
        print("验电操作异常：", e)
        return jsonify({"msg": "验电失败", "error": str(e)}), 500

@bp.route('/api/repair-operation', methods=['POST'])
@login_required(role='electrician')
def repair_operation():
    """检修操作：电工开始/结束检修"""
    data = request.get_json()
    app_id = data.get('id')
    operation = data.get('operation')  # 'start' 或 'end'
    comment = data.get('comment', '')
    
    user = g.user
    operator = user.get('realname') or user.get('username')
    operator_id = user.get('id')
    
    try:
        with get_db_cursor() as cursor:
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
            
            # 记录操作日志
            log_sql = """
                INSERT INTO application_logs
                (application_id, operator, operator_id, operation_type, operation_comment, old_status, new_status)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(log_sql, (
                app_id, operator, operator_id, f'repair_{operation}', comment, app['status'], new_status
            ))
            
        return jsonify({"msg": f"检修{operation}操作完成"}), 200
    except Exception as e:
        print("检修操作异常：", e)
        return jsonify({"msg": "检修操作失败", "error": str(e)}), 500

@bp.route('/api/power-on-apply', methods=['POST'])
@login_required(role='electrician')
def power_on_apply():
    """送电申请"""
    data = request.get_json()
    user = g.user
    applicant = user.get('realname') or user.get('username')
    applicant_id = user.get('id')
    deviceId = data.get('deviceId')
    reason = data.get('reason')
    operation_task = data.get('operation_task', '')
    ticket_template = data.get('ticket_template', '')
    power_on_time = data.get('power_on_time')
    
    if not applicant or not applicant_id or not deviceId or not reason or not power_on_time:
        return jsonify({"msg": "必填信息不能为空"}), 400
    
    try:
        with get_db_cursor() as cursor:
            sql = """
                INSERT INTO applications
                (applicant, applicant_id, deviceId, reason, operation_task, ticket_template, 
                 power_on_time, status, application_type)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (
                applicant, applicant_id, deviceId, reason, operation_task, ticket_template,
                power_on_time, 'pending', 'power_on'
            ))
            application_id = cursor.lastrowid
            
            # 记录操作日志
            log_sql = """
                INSERT INTO application_logs
                (application_id, operator, operator_id, operation_type, operation_comment, old_status, new_status)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(log_sql, (
                application_id, applicant, applicant_id, 'create', '送电申请', '', 'pending'
            ))
            
            # 创建通知
            notify_dispatchers_new_application(application_id, applicant, deviceId, reason)
            notify_applicant_confirmation(application_id, applicant_id)
            
        return jsonify({"msg": "送电申请接收成功", "id": application_id}), 200
    except Exception as e:
        print("插入送电申请异常：", e)
        return jsonify({"msg": "插入失败", "error": str(e)}), 500

@bp.route('/api/power-on-approve', methods=['POST'])
@login_required(role="dispatcher")
def power_on_approve():
    """送电审批"""
    data = request.get_json()
    app_id = data.get('id')
    approved = data.get('approved')
    comment = data.get('comment', '')
    
    user = g.user
    approver = user.get('realname') or user.get('username')
    approver_id = user.get('id')
    
    try:
        with get_db_cursor() as cursor:
            # 检查申请状态
            cursor.execute("SELECT status, applicant_id FROM applications WHERE id = %s", (app_id,))
            app = cursor.fetchone()
            if not app:
                return jsonify({"msg": "申请不存在"}), 404
            if app['status'] != 'pending':
                return jsonify({"msg": "申请状态不正确"}), 400
            
            # 更新状态
            new_status = 'approved' if approved else 'rejected'
            sql = """
                UPDATE applications 
                SET status = %s, approver = %s, approver_id = %s,
                    approve_time = NOW(), approve_comment = %s
                WHERE id = %s
            """
            cursor.execute(sql, (new_status, approver, approver_id, comment, app_id))
            
            # 记录操作日志
            log_sql = """
                INSERT INTO application_logs
                (application_id, operator, operator_id, operation_type, operation_comment, old_status, new_status)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(log_sql, (
                app_id, approver, approver_id, 'approve', comment, 'pending', new_status
            ))
            
            # 创建通知
            notify_approval_result(app_id, app['applicant_id'], approved, approver, comment)
            
        return jsonify({"msg": "审批完成"}), 200
    except Exception as e:
        print("审批操作异常：", e)
        return jsonify({"msg": "审批失败", "error": str(e)}), 500

@bp.route('/api/application/<int:app_id>', methods=['GET'])
@login_required()
def get_application_detail(app_id):
    """获取申请详情"""
    user = g.user
    user_id = user.get('id')
    role = user.get('role')
    
    try:
        with get_db_cursor() as cursor:
            # 检查权限
            if role not in ['admin', 'dispatcher']:
                cursor.execute("SELECT applicant_id FROM applications WHERE id = %s", (app_id,))
                app = cursor.fetchone()
                if not app or app['applicant_id'] != user_id:
                    return jsonify({"msg": "无权限查看此申请"}), 403
            
            # 获取申请详情
            cursor.execute("""
                SELECT a.*, u.realname as applicant_realname, u.role as applicant_role
                FROM applications a
                LEFT JOIN users u ON a.applicant_id = u.id
                WHERE a.id = %s
            """, (app_id,))
            application = cursor.fetchone()
            
            if not application:
                return jsonify({"msg": "申请不存在"}), 404
            
            # 获取操作日志
            cursor.execute("""
                SELECT * FROM application_logs 
                WHERE application_id = %s 
                ORDER BY created_at DESC
            """, (app_id,))
            logs = cursor.fetchall()
            
            application['logs'] = logs
            
        return jsonify({"application": application}), 200
    except Exception as e:
        print("获取申请详情异常：", e)
        return jsonify({"msg": "获取详情失败", "error": str(e)}), 500

@bp.route('/api/export/applications', methods=['GET'])
@login_required(role="admin")
def export_applications():
    """导出申请数据"""
    try:
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT a.*, u.realname as applicant_realname
                FROM applications a
                LEFT JOIN users u ON a.applicant_id = u.id
                ORDER BY a.created_at DESC
            """)
            applications = cursor.fetchall()
            
            # 生成CSV数据
            import csv
            import io
            output = io.StringIO()
            writer = csv.writer(output)
            
            # 写入表头
            writer.writerow([
                'ID', '申请人', '设备ID', '原因', '状态', '停电时间', '送电时间',
                '申请时间', '审批人', '审批时间', '审批意见'
            ])
            
            # 写入数据
            for app in applications:
                writer.writerow([
                    app['id'],
                    app['applicant_realname'] or app['applicant'],
                    app['deviceId'],
                    app['reason'],
                    app['status'],
                    app['power_off_time'],
                    app['power_on_time'],
                    app['created_at'].strftime('%Y-%m-%d %H:%M:%S') if app['created_at'] else '',
                    app['approver'],
                    app['approve_time'].strftime('%Y-%m-%d %H:%M:%S') if app['approve_time'] else '',
                    app['approve_comment']
                ])
            
            output.seek(0)
            
            from flask import Response
            return Response(
                output.getvalue(),
                mimetype='text/csv',
                headers={'Content-Disposition': 'attachment; filename=applications.csv'}
            )
            
    except Exception as e:
        print("导出申请数据异常：", e)
        return jsonify({"msg": "导出失败", "error": str(e)}), 500 