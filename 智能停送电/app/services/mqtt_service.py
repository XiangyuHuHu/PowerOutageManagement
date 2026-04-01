"""
MQTT数据服务
提供设备状态查询和管理功能
"""

from app.database import get_db
import pymysql
import json
import logging

logger = logging.getLogger(__name__)

def get_device_status_from_db(device_id):
    """从数据库获取设备状态"""
    db = get_db()
    if not db:
        return None
    
    try:
        with db.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("""
                SELECT * FROM device_status 
                WHERE device_id = %s
            """, (device_id,))
            result = cursor.fetchone()
            return result
    except Exception as e:
        logger.exception("查询设备状态失败: device_id=%s", device_id)
        return None
    finally:
        db.close()

def get_device_power_status(device_id):
    """获取设备带电状态"""
    status = get_device_status_from_db(device_id)
    if status:
        return status.get('power_status')
    return None

def get_device_tag_status(device_id):
    """获取设备挂牌状态"""
    status = get_device_status_from_db(device_id)
    if status:
        return status.get('tag_status')
    return None

def get_electrician_name(device_id):
    """获取电工名称"""
    status = get_device_status_from_db(device_id)
    if status:
        return status.get('electrician_name')
    return None

def snapshot_mqtt_status(device_id):
    """快照当前MQTT状态（用于步骤记录）"""
    status = get_device_status_from_db(device_id)
    if status:
        return {
            'power_status': status.get('power_status'),
            'tag_status': status.get('tag_status'),
            'electrician_name': status.get('electrician_name'),
            'last_update': status.get('last_update').isoformat() if status.get('last_update') else None,
            'status_data': json.loads(status.get('status_data')) if status.get('status_data') else {}
        }
    return None

def update_device_status(device_id, power_status=None, tag_status=None,
                        active_tag_count=None, electrician_name=None, status_data=None):
    """更新设备状态到数据库"""
    db = get_db()
    if not db:
        return False
    
    try:
        with db.cursor() as cursor:
            # 构建字段和值
            fields = ['device_id']
            values = [device_id]
            updates = []
            
            if power_status is not None:
                fields.append('power_status')
                values.append(power_status)
                updates.append('power_status = VALUES(power_status)')
            
            if tag_status is not None:
                fields.append('tag_status')
                values.append(tag_status)
                updates.append('tag_status = VALUES(tag_status)')
            
            if electrician_name is not None:
                fields.append('electrician_name')
                values.append(electrician_name)
                updates.append('electrician_name = VALUES(electrician_name)')
            
            if status_data is not None:
                fields.append('status_data')
                if isinstance(status_data, dict) and active_tag_count is not None:
                    status_data = dict(status_data)
                    status_data['active_tag_count'] = int(active_tag_count or 0)
                json_data = json.dumps(status_data) if isinstance(status_data, dict) else status_data
                values.append(json_data)
                updates.append('status_data = VALUES(status_data)')
            
            if len(fields) == 1:  # 只有device_id，没有其他字段
                return False
            
            # UPSERT操作
            placeholders = ', '.join(['%s'] * len(fields))
            fields_str = ', '.join(fields)
            updates_str = ', '.join(updates) + ', last_update = NOW()'
            
            sql = f"""
                INSERT INTO device_status ({fields_str})
                VALUES ({placeholders})
                ON DUPLICATE KEY UPDATE {updates_str}
            """
            
            cursor.execute(sql, values)
            db.commit()
            return True
    except Exception as e:
        logger.exception("更新设备状态失败: device_id=%s", device_id)
        db.rollback()
        return False
    finally:
        db.close()

def save_device_status_history(device_id, power_status=None, tag_status=None,
                              active_tag_count=None, electrician_name=None, status_data=None):
    """保存设备状态历史记录"""
    db = get_db()
    if not db:
        return False
    
    try:
        with db.cursor() as cursor:
            if isinstance(status_data, dict) and active_tag_count is not None:
                status_data = dict(status_data)
                status_data['active_tag_count'] = int(active_tag_count or 0)

            cursor.execute("""
                INSERT INTO device_status_history 
                (device_id, power_status, tag_status, electrician_name, status_data)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                device_id,
                power_status,
                tag_status,
                electrician_name,
                json.dumps(status_data) if isinstance(status_data, dict) else status_data
            ))
            db.commit()
            return True
    except Exception as e:
        logger.exception("保存设备状态历史失败: device_id=%s", device_id)
        db.rollback()
        return False
    finally:
        db.close()
