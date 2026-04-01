from app.database import get_db_cursor
from app.mqtt_client import get_device_status


DEVICE_FIELDS = """
    d.device_id,
    d.device_name,
    d.power_room,
    d.cabinet,
    d.area_code,
    d.line_name,
    d.sort_order,
    d.is_active
"""


def get_signal_points_map(device_ids=None):
    with get_db_cursor() as cursor:
        params = []
        where_sql = ""
        if device_ids:
            placeholders = ",".join(["%s"] * len(device_ids))
            where_sql = f"WHERE device_id IN ({placeholders})"
            params = list(device_ids)

        cursor.execute(
            f"""
            SELECT device_id, signal_type, signal_name, signal_address, source_sheet, description
            FROM device_signal_points
            {where_sql}
            ORDER BY device_id ASC, signal_type ASC, signal_name ASC, id ASC
            """,
            params,
        )
        rows = cursor.fetchall()

    mapping = {}
    for row in rows:
        entry = mapping.setdefault(
            row["device_id"],
            {
                "signal_points": [],
                "signal_points_count": 0,
                "remote_local_signal": None,
                "power_feedback_signal": None,
                "tag_count_signal": None,
                "fault_signal": None,
                "remote_switch_binding": None,
                "has_signal_config": False,
            },
        )
        entry["signal_points"].append(dict(row))
        entry["signal_points_count"] += 1
        entry["has_signal_config"] = True

        signal_type = row.get("signal_type")
        if signal_type == "remote_local" and not entry["remote_local_signal"]:
            entry["remote_local_signal"] = row.get("signal_address")
        elif signal_type == "power_feedback" and not entry["power_feedback_signal"]:
            entry["power_feedback_signal"] = row.get("signal_address")
        elif signal_type == "tag_count" and not entry["tag_count_signal"]:
            entry["tag_count_signal"] = row.get("signal_address")
        elif signal_type == "fault_feedback" and not entry["fault_signal"]:
            entry["fault_signal"] = row.get("signal_address")
        elif signal_type == "remote_switch_binding" and not entry["remote_switch_binding"]:
            entry["remote_switch_binding"] = row.get("signal_address")

    return mapping


def get_active_devices():
    with get_db_cursor() as cursor:
        cursor.execute(
            f"""
            SELECT {DEVICE_FIELDS}
            FROM devices d
            WHERE d.is_active = TRUE
            ORDER BY
                COALESCE(NULLIF(d.power_room, ''), 'zzz'),
                d.sort_order ASC,
                d.device_id ASC
            """
        )
        return cursor.fetchall()


def get_device_by_id(device_id):
    with get_db_cursor() as cursor:
        cursor.execute(
            f"""
            SELECT {DEVICE_FIELDS}
            FROM devices d
            WHERE d.device_id = %s
            LIMIT 1
            """,
            (device_id,),
        )
        return cursor.fetchone()


def get_user_managed_device_ids(user_id):
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            SELECT device_id
            FROM user_managed_devices
            WHERE user_id = %s
            ORDER BY device_id ASC
            """,
            (user_id,),
        )
        return [row["device_id"] for row in cursor.fetchall()]


def set_user_managed_device_ids(user_id, device_ids, cursor=None):
    unique_ids = sorted({device_id for device_id in (device_ids or []) if device_id})

    def _run(inner_cursor):
        inner_cursor.execute("DELETE FROM user_managed_devices WHERE user_id = %s", (user_id,))
        if not unique_ids:
            return
        inner_cursor.executemany(
            """
            INSERT INTO user_managed_devices (user_id, device_id)
            VALUES (%s, %s)
            """,
            [(user_id, device_id) for device_id in unique_ids],
        )

    if cursor is not None:
        _run(cursor)
        return

    with get_db_cursor() as inner_cursor:
        _run(inner_cursor)


def enrich_devices_with_status(devices, managed_device_ids=None):
    status_map = get_device_status()
    signal_map = get_signal_points_map([device["device_id"] for device in devices])
    managed_device_ids = set(managed_device_ids or [])
    enriched = []

    for device in devices:
        status = status_map.get(device["device_id"], {})
        power_status = status.get("power_status")
        tag_status = status.get("tag_status")
        online_status = status.get("status")
        signal_info = signal_map.get(
            device["device_id"],
            {
                "signal_points": [],
                "signal_points_count": 0,
                "remote_local_signal": None,
                "power_feedback_signal": None,
                "tag_count_signal": None,
                "fault_signal": None,
                "remote_switch_binding": None,
                "has_signal_config": False,
            },
        )

        item = dict(device)
        item["is_managed"] = device["device_id"] in managed_device_ids
        item["current_status"] = online_status
        item["current_power_status"] = power_status
        item["current_tag_status"] = tag_status
        item["current_active_tag_count"] = int(status.get("active_tag_count") or 0)
        item["last_update"] = status.get("last_update")
        item.update(signal_info)
        active_tag_count = int(status.get("active_tag_count") or 0)
        item["can_skip_approval"] = active_tag_count > 0 and bool(signal_info.get("has_signal_config"))
        item["skip_approval_source"] = "tag_count_signal" if item["can_skip_approval"] else None
        enriched.append(item)

    return enriched
