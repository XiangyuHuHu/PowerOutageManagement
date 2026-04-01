"""
操作服务
封装停送电操作相关的业务逻辑
包括：创建申请、多人申请支持、步骤管理等
"""

from app.database import get_db_cursor
from app.services.workflow_service import WorkflowService
from app.services.mqtt_service import get_device_power_status, get_device_tag_status
import pymysql
import logging

logger = logging.getLogger(__name__)

class OperationService:
    """操作服务类"""
    
    @staticmethod
    def create_power_off_application(applicant_id, applicant_name, device_id, reason, 
                                     operation_task='', ticket_template='', 
                                     power_off_time='', power_on_time='', 
                                     additional_applicants=None):
        """
        创建停电申请
        
        Args:
            applicant_id: 主申请人ID
            applicant_name: 主申请人姓名
            device_id: 设备编号
            reason: 申请原因
            operation_task: 操作任务
            ticket_template: 操作票模板
            power_off_time: 计划停电时间
            power_on_time: 计划送电时间
            additional_applicants: 其他申请人列表 [{'name': 'xxx', 'id': 123, 'role': 'user'}, ...]
        
        Returns:
            (success: bool, operation_id: int, message: str)
        """
        try:
            with get_db_cursor() as cursor:
                # 1. 获取设备初始带电状态（从MQTT）
                initial_power_status = get_device_power_status(device_id) or 'powered'
                
                # 2. 创建申请记录
                sql = """
                    INSERT INTO applications
                    (applicant, applicant_id, deviceId, reason, operation_task, ticket_template, 
                     power_off_time, power_on_time, status, operation_type, initial_power_status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (
                    applicant_name, applicant_id, device_id, reason, operation_task, ticket_template,
                    power_off_time, power_on_time, 'applied', 'power_off', initial_power_status
                ))
                operation_id = cursor.lastrowid
                
                # 3. 添加主申请人到申请人表
                cursor.execute("""
                    INSERT INTO operation_applicants 
                    (operation_id, applicant_name, applicant_id, is_primary)
                    VALUES (%s, %s, %s, TRUE)
                """, (operation_id, applicant_name, applicant_id))
                
                # 4. 添加其他申请人（如果存在）
                if additional_applicants:
                    for app in additional_applicants:
                        cursor.execute("""
                            INSERT INTO operation_applicants 
                            (operation_id, applicant_name, applicant_id, applicant_role, is_primary)
                            VALUES (%s, %s, %s, %s, FALSE)
                        """, (operation_id, app.get('name'), app.get('id'), app.get('role', 'user')))
                
                # 5. 创建操作步骤
                WorkflowService.create_power_off_steps(operation_id, device_id, initial_power_status)
                
                # 6. 记录操作日志
                log_sql = """
                    INSERT INTO application_logs
                    (application_id, operator, operator_id, operation_type, operation_comment, old_status, new_status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(log_sql, (
                    operation_id, applicant_name, applicant_id, 'create', '停电申请', '', 'applied'
                ))
                
                return True, operation_id, "申请创建成功"
                
        except Exception as e:
            logger.exception("创建停电申请失败: applicant_id=%s, device_id=%s", applicant_id, device_id)
            return False, None, f"申请创建失败: {str(e)}"
    
    @staticmethod
    def create_power_on_application(applicant_id, applicant_name, device_id, reason,
                                    operation_task='', ticket_template='',
                                    power_on_time='', additional_applicants=None):
        """
        创建送电申请
        
        Args:
            applicant_id: 主申请人ID
            applicant_name: 主申请人姓名
            device_id: 设备编号
            reason: 申请原因
            operation_task: 操作任务
            ticket_template: 操作票模板
            power_on_time: 计划送电时间
            additional_applicants: 其他申请人列表
        
        Returns:
            (success: bool, operation_id: int, message: str)
        """
        try:
            with get_db_cursor() as cursor:
                # 1. 获取设备挂牌状态（从MQTT）
                tag_status = get_device_tag_status(device_id) or 'untagged'
                
                # 2. 创建申请记录
                sql = """
                    INSERT INTO applications
                    (applicant, applicant_id, deviceId, reason, operation_task, ticket_template, 
                     power_on_time, status, operation_type, tag_status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (
                    applicant_name, applicant_id, device_id, reason, operation_task, ticket_template,
                    power_on_time, 'power_on_applied', 'power_on', tag_status
                ))
                operation_id = cursor.lastrowid
                
                # 3. 添加主申请人
                cursor.execute("""
                    INSERT INTO operation_applicants 
                    (operation_id, applicant_name, applicant_id, is_primary)
                    VALUES (%s, %s, %s, TRUE)
                """, (operation_id, applicant_name, applicant_id))
                
                # 4. 添加其他申请人（如果存在）
                if additional_applicants:
                    for app in additional_applicants:
                        cursor.execute("""
                            INSERT INTO operation_applicants 
                            (operation_id, applicant_name, applicant_id, applicant_role, is_primary)
                            VALUES (%s, %s, %s, %s, FALSE)
                        """, (operation_id, app.get('name'), app.get('id'), app.get('role', 'user')))
                
                # 5. 创建操作步骤
                WorkflowService.create_power_on_steps(operation_id, device_id, tag_status)
                
                # 6. 记录操作日志
                log_sql = """
                    INSERT INTO application_logs
                    (application_id, operator, operator_id, operation_type, operation_comment, old_status, new_status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(log_sql, (
                    operation_id, applicant_name, applicant_id, 'create', '送电申请', '', 'power_on_applied'
                ))
                
                return True, operation_id, "申请创建成功"
                
        except Exception as e:
            logger.exception("创建送电申请失败: applicant_id=%s, device_id=%s", applicant_id, device_id)
            return False, None, f"申请创建失败: {str(e)}"
    
    @staticmethod
    def get_operation_with_steps(operation_id):
        """获取操作详情（包含步骤）"""
        from app.database import get_db
        import pymysql
        
        db = get_db()
        if not db:
            return None
        
        try:
            with db.cursor(pymysql.cursors.DictCursor) as cursor:
                # 获取操作详情
                cursor.execute("""
                    SELECT a.*, u.realname as applicant_realname, u.role as applicant_role
                    FROM applications a
                    LEFT JOIN users u ON a.applicant_id = u.id
                    WHERE a.id = %s
                """, (operation_id,))
                operation = cursor.fetchone()
                
                if not operation:
                    return None
                
                # 获取申请人列表
                cursor.execute("""
                    SELECT * FROM operation_applicants 
                    WHERE operation_id = %s 
                    ORDER BY is_primary DESC, created_at ASC
                """, (operation_id,))
                applicants = cursor.fetchall()
                operation['applicants'] = applicants
                
                # 获取步骤列表
                steps = WorkflowService.get_all_steps(operation_id)
                operation['steps'] = steps
                
                # 获取操作日志
                cursor.execute("""
                    SELECT * FROM application_logs 
                    WHERE application_id = %s 
                    ORDER BY operation_time DESC
                """, (operation_id,))
                logs = cursor.fetchall()
                operation['logs'] = logs
                
                return operation
        except Exception as e:
            logger.exception("获取操作详情失败: operation_id=%s", operation_id)
            return None
        finally:
            db.close()
