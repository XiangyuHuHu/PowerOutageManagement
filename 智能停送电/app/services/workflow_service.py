"""
工作流服务
管理停送电流程的状态机和步骤
"""

from app.database import get_db
from app.services.mqtt_service import get_device_power_status, get_device_tag_status, snapshot_mqtt_status
import pymysql
import json
import logging

logger = logging.getLogger(__name__)

# 停电流程步骤定义
POWER_OFF_STEPS = {
    'powered': [  # 有电状态下的步骤
        {'name': 'applied', 'order': 1, 'status': 'pending'},
        {'name': 'pending_approval', 'order': 2, 'status': 'pending'},
        {'name': 'approved', 'order': 3, 'status': 'pending'},
        {'name': 'power_off_operating', 'order': 4, 'status': 'skipped'},  # 不在程序中
        {'name': 'verifying', 'order': 5, 'status': 'pending'},
        {'name': 'confirmed_power_off', 'order': 6, 'status': 'pending'},
        {'name': 'tagging', 'order': 7, 'status': 'pending'},
    ],
    'unpowered': [  # 没电状态下的步骤
        {'name': 'applied', 'order': 1, 'status': 'pending'},
        {'name': 'tagging', 'order': 2, 'status': 'pending'},
    ]
}

# 送电流程步骤定义
POWER_ON_STEPS = {
    'tagged': [  # 已挂牌
        {'name': 'power_on_applied', 'order': 1, 'status': 'pending'},
        {'name': 'power_on_operating', 'order': 2, 'status': 'pending'},
        {'name': 'confirmed_power_on', 'order': 3, 'status': 'pending'},
    ],
    'untagged': [  # 未挂牌
        {'name': 'power_on_applied', 'order': 1, 'status': 'pending'},
        {'name': 'checking_tag', 'order': 2, 'status': 'pending'},
        {'name': 'pending_approval', 'order': 3, 'status': 'pending'},
        {'name': 'approved', 'order': 4, 'status': 'pending'},
        {'name': 'power_on_operating', 'order': 5, 'status': 'pending'},
        {'name': 'confirmed_power_on', 'order': 6, 'status': 'pending'},
    ]
}


class WorkflowService:
    """工作流服务类"""
    
    @staticmethod
    def create_power_off_steps(operation_id, device_id, initial_power_status=None):
        """根据初始带电状态创建停电流程步骤"""
        # 如果未提供初始状态，从MQTT获取
        if initial_power_status is None:
            initial_power_status = get_device_power_status(device_id) or 'powered'
        
        # 获取对应步骤定义
        steps = POWER_OFF_STEPS.get(initial_power_status, POWER_OFF_STEPS['powered'])
        
        # 快照MQTT状态
        mqtt_snapshot = snapshot_mqtt_status(device_id)
        
        # 插入步骤
        db = get_db()
        if not db:
            return False
        
        try:
            with db.cursor() as cursor:
                for step in steps:
                    cursor.execute("""
                        INSERT INTO operation_steps 
                        (operation_id, step_name, step_order, step_status, mqtt_snapshot)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (
                        operation_id,
                        step['name'],
                        step['order'],
                        step['status'],
                        json.dumps(mqtt_snapshot) if mqtt_snapshot else None
                    ))
                
                # 更新applications表的初始状态和当前步骤
                cursor.execute("""
                    UPDATE applications 
                    SET initial_power_status = %s, 
                        current_step = %s,
                        status = 'applied'
                    WHERE id = %s
                """, (initial_power_status, steps[0]['name'], operation_id))
                
                db.commit()
                return True
        except Exception as e:
            logger.exception("创建停电步骤失败: operation_id=%s", operation_id)
            db.rollback()
            return False
        finally:
            db.close()
    
    @staticmethod
    def create_power_on_steps(operation_id, device_id, tag_status=None):
        """根据挂牌状态创建送电流程步骤"""
        # 如果未提供挂牌状态，从MQTT获取
        if tag_status is None:
            tag_status = get_device_tag_status(device_id) or 'untagged'
        
        # 获取对应步骤定义
        steps = POWER_ON_STEPS.get(tag_status, POWER_ON_STEPS['untagged'])
        
        # 快照MQTT状态
        mqtt_snapshot = snapshot_mqtt_status(device_id)
        
        # 插入步骤
        db = get_db()
        if not db:
            return False
        
        try:
            with db.cursor() as cursor:
                for step in steps:
                    cursor.execute("""
                        INSERT INTO operation_steps 
                        (operation_id, step_name, step_order, step_status, mqtt_snapshot)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (
                        operation_id,
                        step['name'],
                        step['order'],
                        step['status'],
                        json.dumps(mqtt_snapshot) if mqtt_snapshot else None
                    ))
                
                # 更新applications表的当前步骤
                cursor.execute("""
                    UPDATE applications 
                    SET tag_status = %s,
                        current_step = %s,
                        status = 'power_on_applied'
                    WHERE id = %s
                """, (tag_status, steps[0]['name'], operation_id))
                
                db.commit()
                return True
        except Exception as e:
            logger.exception("创建送电步骤失败: operation_id=%s", operation_id)
            db.rollback()
            return False
        finally:
            db.close()
    
    @staticmethod
    def complete_step(operation_id, step_name, operator_name, operator_id, 
                     operator_role, comment='', mqtt_snapshot=None):
        """完成步骤并更新状态"""
        db = get_db()
        if not db:
            return False
        
        try:
            with db.cursor(pymysql.cursors.DictCursor) as cursor:
                # 获取当前步骤
                cursor.execute("""
                    SELECT * FROM operation_steps 
                    WHERE operation_id = %s AND step_name = %s
                """, (operation_id, step_name))
                step = cursor.fetchone()
                
                if not step:
                    logger.warning("步骤不存在: operation_id=%s, step=%s", operation_id, step_name)
                    return False
                
                if step['step_status'] == 'completed':
                    logger.info("步骤已完成: operation_id=%s, step=%s", operation_id, step_name)
                    return True
                
                # 更新步骤状态
                if mqtt_snapshot is None:
                    # 获取当前设备ID
                    cursor.execute("SELECT deviceId FROM applications WHERE id = %s", (operation_id,))
                    app = cursor.fetchone()
                    if app:
                        mqtt_snapshot = snapshot_mqtt_status(app['deviceId'])
                
                cursor.execute("""
                    UPDATE operation_steps 
                    SET step_status = 'completed',
                        operator_name = %s,
                        operator_id = %s,
                        operator_role = %s,
                        complete_time = NOW(),
                        comment = %s,
                        mqtt_snapshot = %s
                    WHERE id = %s
                """, (
                    operator_name, operator_id, operator_role, comment,
                    json.dumps(mqtt_snapshot) if mqtt_snapshot else None,
                    step['id']
                ))
                
                # 获取下一步骤
                next_step = WorkflowService.get_next_step(operation_id)
                if next_step:
                    # 开始下一步骤
                    cursor.execute("""
                        UPDATE operation_steps 
                        SET step_status = 'in_progress',
                            start_time = NOW()
                        WHERE id = %s
                    """, (next_step['id'],))
                    
                    # 更新applications表的当前步骤
                    cursor.execute("""
                        UPDATE applications 
                        SET current_step = %s,
                            status = %s
                        WHERE id = %s
                    """, (next_step['step_name'], next_step['step_name'], operation_id))
                else:
                    # 没有下一步，流程可能完成
                    cursor.execute("""
                        UPDATE applications 
                        SET current_step = NULL,
                            status = 'completed',
                            final_status = 'completed',
                            completed_time = NOW()
                        WHERE id = %s
                    """, (operation_id,))
                
                db.commit()
                return True
        except Exception as e:
            logger.exception("完成步骤失败: operation_id=%s, step=%s", operation_id, step_name)
            db.rollback()
            return False
        finally:
            db.close()
    
    @staticmethod
    def get_next_step(operation_id):
        """获取下一步骤"""
        db = get_db()
        if not db:
            return None
        
        try:
            with db.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM operation_steps 
                    WHERE operation_id = %s 
                    AND step_status = 'pending'
                    ORDER BY step_order ASC
                    LIMIT 1
                """, (operation_id,))
                return cursor.fetchone()
        except Exception as e:
            logger.exception("获取下一步骤失败: operation_id=%s", operation_id)
            return None
        finally:
            db.close()
    
    @staticmethod
    def get_all_steps(operation_id):
        """获取所有步骤"""
        db = get_db()
        if not db:
            return []
        
        try:
            with db.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM operation_steps 
                    WHERE operation_id = %s 
                    ORDER BY step_order ASC
                """, (operation_id,))
                return cursor.fetchall()
        except Exception as e:
            logger.exception("获取步骤列表失败: operation_id=%s", operation_id)
            return []
        finally:
            db.close()
    
    @staticmethod
    def get_current_step(operation_id):
        """获取当前步骤"""
        db = get_db()
        if not db:
            return None
        
        try:
            with db.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM operation_steps 
                    WHERE operation_id = %s 
                    AND step_status IN ('in_progress', 'pending')
                    ORDER BY step_order ASC
                    LIMIT 1
                """, (operation_id,))
                return cursor.fetchone()
        except Exception as e:
            logger.exception("获取当前步骤失败: operation_id=%s", operation_id)
            return None
        finally:
            db.close()
    
    @staticmethod
    def report_fault(operation_id, fault_reason, operator_name, operator_id):
        """报故障"""
        db = get_db()
        if not db:
            return False
        
        try:
            with db.cursor() as cursor:
                cursor.execute("""
                    UPDATE applications 
                    SET status = 'fault',
                        final_status = 'fault',
                        fault_reason = %s,
                        completed_time = NOW()
                    WHERE id = %s
                """, (fault_reason, operation_id))
                
                # 记录操作日志
                cursor.execute("""
                    INSERT INTO application_logs
                    (application_id, operator, operator_id, operation_type, operation_comment, old_status, new_status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (operation_id, operator_name, operator_id, 'report_fault', fault_reason, 'in_progress', 'fault'))
                
                db.commit()
                return True
        except Exception as e:
            logger.exception("报故障失败: operation_id=%s", operation_id)
            db.rollback()
            return False
        finally:
            db.close()
