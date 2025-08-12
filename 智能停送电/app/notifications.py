from app.database import get_db_cursor

def create_notification(title, content, notification_type='info', user_id=None):
    """创建通知"""
    try:
        with get_db_cursor() as cursor:
            sql = """
                INSERT INTO notifications (user_id, title, content, type)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(sql, (user_id, title, content, notification_type))
        return True
    except Exception as e:
        print(f"创建通知失败: {e}")
        return False

def get_user_notifications(user_id):
    """获取用户通知"""
    try:
        with get_db_cursor() as cursor:
            sql = """
                SELECT * FROM notifications 
                WHERE user_id = %s 
                ORDER BY created_at DESC
            """
            cursor.execute(sql, (user_id,))
            return cursor.fetchall()
    except Exception as e:
        print(f"获取用户通知失败: {e}")
        return []

def mark_notification_read(notification_id, user_id):
    """标记通知为已读"""
    try:
        with get_db_cursor() as cursor:
            sql = """
                UPDATE notifications 
                SET is_read = TRUE 
                WHERE id = %s AND user_id = %s
            """
            cursor.execute(sql, (notification_id, user_id))
        return True
    except Exception as e:
        print(f"标记通知已读失败: {e}")
        return False

def get_notification_stats(user_id):
    """获取通知统计"""
    try:
        with get_db_cursor() as cursor:
            # 总通知数
            cursor.execute("SELECT COUNT(*) as total FROM notifications WHERE user_id = %s", (user_id,))
            total = cursor.fetchone()['total']
            
            # 未读通知数
            cursor.execute("SELECT COUNT(*) as unread FROM notifications WHERE user_id = %s AND is_read = FALSE", (user_id,))
            unread = cursor.fetchone()['unread']
            
            # 今日通知数
            cursor.execute("""
                SELECT COUNT(*) as today FROM notifications 
                WHERE user_id = %s AND DATE(created_at) = CURDATE()
            """, (user_id,))
            today = cursor.fetchone()['today']
            
            # 本周通知数
            cursor.execute("""
                SELECT COUNT(*) as week FROM notifications 
                WHERE user_id = %s AND YEARWEEK(created_at) = YEARWEEK(NOW())
            """, (user_id,))
            week = cursor.fetchone()['week']
            
            return {
                'total': total,
                'unread': unread,
                'today': today,
                'week': week
            }
    except Exception as e:
        print(f"获取通知统计失败: {e}")
        return {'total': 0, 'unread': 0, 'today': 0, 'week': 0}

def notify_dispatchers_new_application(application_id, applicant, device_id, reason):
    """通知调度员有新申请"""
    try:
        with get_db_cursor() as cursor:
            # 获取所有调度员
            cursor.execute("SELECT id FROM users WHERE role = 'dispatcher'")
            dispatchers = cursor.fetchall()
            
            # 给每个调度员发送通知
            for dispatcher in dispatchers:
                create_notification(
                    title=f"新的停电申请 - #{application_id}",
                    content=f"申请人：{applicant}\n设备：{device_id}\n原因：{reason}\n请及时审批。",
                    notification_type='warning',
                    user_id=dispatcher['id']
                )
        return True
    except Exception as e:
        print(f"通知调度员失败: {e}")
        return False

def notify_applicant_confirmation(application_id, user_id):
    """通知申请人申请提交成功"""
    return create_notification(
        title=f"申请提交成功 - #{application_id}",
        content=f"您的停电申请已提交成功，正在等待审批。",
        notification_type='success',
        user_id=user_id
    )

def notify_approval_result(application_id, user_id, approved, approver, comment):
    """通知申请人审批结果"""
    notification_type = 'success' if approved else 'error'
    status_text = '通过' if approved else '被驳回'
    
    return create_notification(
        title=f"申请审批结果 - #{application_id}",
        content=f"您的申请已{status_text}。\n审批人：{approver}\n审批意见：{comment or '无'}",
        notification_type=notification_type,
        user_id=user_id
    ) 