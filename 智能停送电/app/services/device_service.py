import json
from datetime import datetime

from app.database import get_db_cursor
from app.kep_opcua_address import FAULT_SIGNAL_TYPES, SIGNAL_TYPE_LABELS
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
            SELECT device_id, signal_type, signal_name, signal_address, data_type, source_sheet, description
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
        status_data = status.get("data") if isinstance(status.get("data"), dict) else {}
        item["live_signals"] = status_data.get("signals") or {}
        enriched.append(item)

    return enriched


WORKFLOW_OPERATION_LABELS = {
    "create": "停电申请",
    "power_off_approve": "停电审批",
    "electrician_verify": "验电挂牌",
    "repair_start": "开始检修",
    "repair_end": "完成检修",
    "power_on_apply": "申请送电",
    "power_on_approve": "送电审批",
    "tag_release": "解除挂牌",
    "auto_skip_power_off_approval": "失电免审批转安全确认",
}


def _history_safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _history_format_signal_value(signal_type, value):
    if signal_type == "power_feedback":
        return "未知" if value is None else ("带电" if bool(value) else "失电")
    if signal_type == "tag_count":
        return str(_history_safe_int(value, 0))
    if signal_type == "run_status":
        return "未知" if value is None else ("运行" if bool(value) else "停止")
    if value is None:
        return "未知"
    return "是" if bool(value) else "否"


def _history_extract_signals(status_data):
    if not status_data:
        return {}
    if isinstance(status_data, str):
        try:
            status_data = json.loads(status_data)
        except json.JSONDecodeError:
            return {}
    if not isinstance(status_data, dict):
        return {}
    signals = status_data.get("signals")
    if isinstance(signals, dict):
        return signals
    legacy = {}
    if "power_feedback" in status_data:
        legacy["power_feedback"] = status_data.get("power_feedback")
    if "tag_count" in status_data:
        legacy["tag_count"] = status_data.get("tag_count")
    return legacy


def _history_category_matches(signal_type, category):
    category = (category or "all").lower()
    if category in ("all", ""):
        return True
    if category == "workflow":
        return False
    if category == "fault":
        return signal_type in FAULT_SIGNAL_TYPES
    if category == "run":
        return signal_type == "run_status"
    if category in ("power", "breaker"):
        return signal_type == "power_feedback"
    return True


def query_device_event_history(device_id=None, date_from=None, date_to=None, category="all", limit=500):
    category = (category or "all").strip().lower()
    limit = int(limit or 500)
    events = []

    if category != "workflow":
        params = []
        query = """
            SELECT h.device_id, h.timestamp, h.status_data, d.device_name
            FROM device_status_history h
            LEFT JOIN devices d ON d.device_id = h.device_id
            WHERE 1=1
        """
        if device_id:
            query += " AND h.device_id = %s"
            params.append(device_id)
        if date_from:
            query += " AND h.timestamp >= %s"
            params.append(date_from)
        if date_to:
            query += " AND h.timestamp <= %s"
            params.append(date_to)
        query += " ORDER BY h.device_id ASC, h.timestamp ASC LIMIT %s"
        params.append(max(limit * 4, 500))

        with get_db_cursor() as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()

        last_signals = {}
        for row in rows:
            device = row["device_id"]
            device_label = f"{row.get('device_name') or device}（{device}）"
            signals = _history_extract_signals(row.get("status_data"))
            previous = last_signals.get(device, {})
            for signal_type, new_value in signals.items():
                if not _history_category_matches(signal_type, category):
                    continue
                old_value = previous.get(signal_type)
                if old_value is not None and old_value == new_value:
                    continue
                label = SIGNAL_TYPE_LABELS.get(signal_type, signal_type)
                old_text = _history_format_signal_value(signal_type, old_value)
                new_text = _history_format_signal_value(signal_type, new_value)
                desc = f"{device_label} {label}：{old_text} → {new_text}"
                if signal_type == "power_feedback":
                    desc += "（合闸/带电）" if new_text == "带电" else "（分闸/失电）"
                events.append(
                    {
                        "source": "signal",
                        "device_id": device,
                        "device_name": row.get("device_name") or device,
                        "event_time": row["timestamp"],
                        "event_type": signal_type,
                        "event_category": (
                            "fault"
                            if signal_type in FAULT_SIGNAL_TYPES
                            else "run"
                            if signal_type == "run_status"
                            else "power"
                        ),
                        "description": desc,
                    }
                )
            last_signals[device] = dict(signals)

    if category in ("all", "workflow"):
        params = []
        query = """
            SELECT a.deviceId AS device_id, d.device_name, l.operation_type, l.operation_time,
                   l.operation_comment, l.operator, l.old_status, l.new_status
            FROM application_logs l
            INNER JOIN applications a ON a.id = l.application_id
            LEFT JOIN devices d ON d.device_id = a.deviceId
            WHERE 1=1
        """
        if device_id:
            query += " AND a.deviceId = %s"
            params.append(device_id)
        if date_from:
            query += " AND l.operation_time >= %s"
            params.append(date_from)
        if date_to:
            query += " AND l.operation_time <= %s"
            params.append(date_to)
        query += " ORDER BY l.operation_time DESC LIMIT %s"
        params.append(min(200, limit))

        with get_db_cursor() as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()

        for row in rows:
            op = row.get("operation_type") or ""
            device = row.get("device_id") or ""
            device_name = row.get("device_name") or device
            label = WORKFLOW_OPERATION_LABELS.get(op, op or "流程操作")
            comment = (row.get("operation_comment") or "").strip()
            desc = f"{device_name}（{device}）{label}"
            if comment:
                desc += f"：{comment}"
            events.append(
                {
                    "source": "workflow",
                    "device_id": device,
                    "device_name": device_name,
                    "event_time": row.get("operation_time"),
                    "event_type": op,
                    "event_category": "workflow",
                    "description": desc,
                }
            )

    events.sort(key=lambda item: item.get("event_time") or datetime.min, reverse=True)
    return events[:limit]
