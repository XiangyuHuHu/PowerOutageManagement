import logging

from app.database import get_db_cursor
from app.opcua_client import adjust_device_tag_count

logger = logging.getLogger(__name__)


def _select_tag_records(cursor, sql, params):
    cursor.execute(sql, params)
    return cursor.fetchall()


def create_tag_record(application_id, device_id, electrician_id, electrician_name, cursor=None):
    """创建挂牌记录；同一工单同一电工仅保留一条 active 记录。"""
    try:
        if cursor is not None:
            cursor.execute(
                """
                SELECT id
                FROM device_tag_records
                WHERE application_id = %s
                  AND electrician_id = %s
                  AND tag_status = 'active'
                LIMIT 1
                """,
                (application_id, electrician_id),
            )
            existing = cursor.fetchone()
            if existing:
                return existing["id"]

            cursor.execute(
                """
                INSERT INTO device_tag_records
                (device_id, application_id, electrician_id, electrician_name, tag_status, tag_time)
                VALUES (%s, %s, %s, %s, 'active', NOW())
                """,
                (device_id, application_id, electrician_id, electrician_name),
            )
            record_id = cursor.lastrowid
            try:
                adjust_device_tag_count(device_id, 1)
            except Exception:
                logger.exception("同步 KEP 挂牌数量失败（加挂牌）: device_id=%s", device_id)
            return record_id

        with get_db_cursor() as inner_cursor:
            return create_tag_record(application_id, device_id, electrician_id, electrician_name, cursor=inner_cursor)
    except Exception:
        logger.exception(
            "创建挂牌记录失败: application_id=%s, electrician_id=%s",
            application_id,
            electrician_id,
        )
        raise


def release_tag_record(application_id, device_id, electrician_id, electrician_name, comment="", cursor=None):
    """解除当前工单下、当前电工本人名下的 active 挂牌。"""
    try:
        if cursor is not None:
            cursor.execute(
                """
                UPDATE device_tag_records
                SET tag_status = 'released',
                    release_time = NOW(),
                    release_application_id = %s,
                    release_operator_id = %s,
                    release_operator_name = %s,
                    release_comment = %s
                WHERE application_id = %s
                  AND device_id = %s
                  AND electrician_id = %s
                  AND tag_status = 'active'
                """,
                (
                    application_id,
                    electrician_id,
                    electrician_name,
                    comment,
                    application_id,
                    device_id,
                    electrician_id,
                ),
            )
            released = cursor.rowcount
            if released > 0:
                try:
                    adjust_device_tag_count(device_id, -released)
                except Exception:
                    logger.exception("同步 KEP 挂牌数量失败（解挂牌）: device_id=%s", device_id)
            return released

        with get_db_cursor() as inner_cursor:
            return release_tag_record(
                application_id,
                device_id,
                electrician_id,
                electrician_name,
                comment=comment,
                cursor=inner_cursor,
            )
    except Exception:
        logger.exception(
            "解除挂牌记录失败: application_id=%s, electrician_id=%s",
            application_id,
            electrician_id,
        )
        raise


def count_active_tags(device_id, cursor=None):
    try:
        if cursor is not None:
            cursor.execute(
                """
                SELECT COUNT(*) AS total
                FROM device_tag_records
                WHERE device_id = %s
                  AND tag_status = 'active'
                """,
                (device_id,),
            )
            row = cursor.fetchone()
            return int((row or {}).get("total", 0))

        with get_db_cursor() as inner_cursor:
            return count_active_tags(device_id, cursor=inner_cursor)
    except Exception:
        logger.exception("统计设备挂牌失败: device_id=%s", device_id)
        raise


def get_tag_records_by_application(application_id, cursor=None):
    try:
        sql = """
            SELECT id, device_id, application_id, electrician_id, electrician_name,
                   tag_status, tag_time, release_time, release_application_id,
                   release_operator_id, release_operator_name, release_comment
            FROM device_tag_records
            WHERE application_id = %s
            ORDER BY tag_time DESC, id DESC
        """
        if cursor is not None:
            return _select_tag_records(cursor, sql, (application_id,))

        with get_db_cursor() as inner_cursor:
            return _select_tag_records(inner_cursor, sql, (application_id,))
    except Exception:
        logger.exception("查询工单挂牌记录失败: application_id=%s", application_id)
        return []


def get_active_tags_by_device(device_id, cursor=None):
    try:
        sql = """
            SELECT id, device_id, application_id, electrician_id, electrician_name,
                   tag_status, tag_time
            FROM device_tag_records
            WHERE device_id = %s
              AND tag_status = 'active'
            ORDER BY tag_time ASC, id ASC
        """
        if cursor is not None:
            return _select_tag_records(cursor, sql, (device_id,))

        with get_db_cursor() as inner_cursor:
            return _select_tag_records(inner_cursor, sql, (device_id,))
    except Exception:
        logger.exception("查询设备有效挂牌失败: device_id=%s", device_id)
        return []
