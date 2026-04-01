"""`r`n停送电操作相关路由。`r`n"""

import logging

from flask import Blueprint, g, jsonify, request

from app.auth import login_required, user_room_filter_clause
from app.database import get_db_cursor
from app.mqtt_client import get_device_history, get_device_status
from app.notifications import (
    get_user_notifications,
    mark_notification_read,
    notify_applicant_confirmation,
    notify_dispatchers_new_application,
)
from app.services.application_flow_service import raw_sql, transition_application, write_application_log
from app.services.device_service import (
    enrich_devices_with_status,
    get_active_devices,
    get_device_by_id,
    get_signal_points_map,
    get_user_managed_device_ids,
    set_user_managed_device_ids,
)
from app.services.tag_service import (
    count_active_tags,
    create_tag_record,
    get_active_tags_by_device,
    release_tag_record,
)

bp = Blueprint("operations", __name__)
logger = logging.getLogger(__name__)
TERMINAL_APPLICATION_STATUSES = {"completed", "rejected", "power_on_rejected"}


LIST_SELECT_SQL = """
    SELECT
        a.*,
        d.device_name,
        d.power_room,
        d.cabinet,
        d.area_code,
        d.line_name,
        COALESCE(tag_summary.active_tag_count, 0) AS active_tag_count
    FROM applications a
    LEFT JOIN devices d ON d.device_id = a.deviceId
    LEFT JOIN (
        SELECT device_id, COUNT(*) AS active_tag_count
        FROM device_tag_records
        WHERE tag_status = 'active'
        GROUP BY device_id
    ) tag_summary ON tag_summary.device_id = a.deviceId
    WHERE 1=1
"""


def attach_active_tags(rows):
    device_ids = sorted({row.get("deviceId") for row in rows if row.get("deviceId")})
    if not device_ids:
        return rows

    placeholders = ",".join(["%s"] * len(device_ids))
    tags_by_device = {device_id: [] for device_id in device_ids}
    with get_db_cursor() as cursor:
        cursor.execute(
            f"""
            SELECT
                id,
                device_id,
                application_id,
                electrician_id,
                electrician_name,
                tag_status,
                tag_time
            FROM device_tag_records
            WHERE tag_status = 'active'
              AND device_id IN ({placeholders})
            ORDER BY device_id ASC, tag_time ASC, id ASC
            """,
            device_ids,
        )
        for record in cursor.fetchall():
            tags_by_device.setdefault(record["device_id"], []).append(record)

    for row in rows:
        active_tags = tags_by_device.get(row.get("deviceId"), [])
        row["active_tags"] = active_tags
        row["active_tag_count"] = int(row.get("active_tag_count") or len(active_tags))
    return rows


def _filter_devices_by_scope(devices, user):
    if user.get("access_all_rooms"):
        return list(devices)

    room_scopes = set(user.get("room_scopes") or [])
    return [item for item in devices if (item.get("power_room") or "") in room_scopes]


def _get_accessible_devices_for_user(user):
    devices = _filter_devices_by_scope(get_active_devices(), user)
    managed_ids = get_user_managed_device_ids(user.get("id"))
    accessible_ids = {item["device_id"] for item in devices}
    managed_ids = [device_id for device_id in managed_ids if device_id in accessible_ids]
    return enrich_devices_with_status(devices, managed_ids), managed_ids


def _find_open_application_conflicts(cursor, device_ids):
    if not device_ids:
        return {}

    placeholders = ",".join(["%s"] * len(device_ids))
    terminal_placeholders = ",".join(["%s"] * len(TERMINAL_APPLICATION_STATUSES))
    cursor.execute(
        f"""
        SELECT id, deviceId, status, applicant, created_at
        FROM applications
        WHERE deviceId IN ({placeholders})
          AND status NOT IN ({terminal_placeholders})
        ORDER BY created_at DESC, id DESC
        """,
        list(device_ids) + list(TERMINAL_APPLICATION_STATUSES),
    )

    conflicts = {}
    for row in cursor.fetchall():
        conflicts.setdefault(row["deviceId"], row)
    return conflicts


@bp.route("/api/devices", methods=["GET"])
@login_required()
def get_devices():
    """Return active device master data."""
    try:
        user = g.user
        devices, managed_ids = _get_accessible_devices_for_user(user)
        query = (request.args.get("q") or "").strip().lower()
        managed_only = request.args.get("managed_only", "").lower() in {"1", "true", "yes"}

        if managed_only:
            devices = [item for item in devices if item["device_id"] in set(managed_ids)]

        if query:
            devices = [
                item
                for item in devices
                if query in (item.get("device_id") or "").lower()
                or query in (item.get("device_name") or "").lower()
                or query in (item.get("power_room") or "").lower()
                or query in (item.get("cabinet") or "").lower()
                or query in (item.get("line_name") or "").lower()
            ]

        return jsonify(devices), 200
    except Exception as exc:
        logger.exception("加载设备台账失败")
        return jsonify({"msg": "加载设备台账失败", "error": str(exc)}), 500


@bp.route("/api/my-devices", methods=["GET", "PUT"])
@login_required()
def my_devices():
    user = g.user

    try:
        accessible_devices, managed_ids = _get_accessible_devices_for_user(user)
        accessible_ids = {item["device_id"] for item in accessible_devices}

        if request.method == "GET":
            managed_devices = [item for item in accessible_devices if item["device_id"] in set(managed_ids)]
            return jsonify({"device_ids": managed_ids, "devices": managed_devices}), 200

        payload = request.get_json() or {}
        device_ids = payload.get("device_ids") or []
        if not isinstance(device_ids, list):
            return jsonify({"msg": "负责设备列表格式不正确"}), 400

        invalid_ids = sorted({device_id for device_id in device_ids if device_id not in accessible_ids})
        if invalid_ids:
            return jsonify({"msg": "存在无权限管理的设备", "invalid_device_ids": invalid_ids}), 403

        set_user_managed_device_ids(user.get("id"), device_ids)
        updated_devices = [item for item in accessible_devices if item["device_id"] in set(device_ids)]
        return jsonify({"msg": "负责设备已更新", "device_ids": sorted(set(device_ids)), "devices": updated_devices}), 200
    except Exception as exc:
        logger.exception("维护负责设备失败")
        return jsonify({"msg": "维护负责设备失败", "error": str(exc)}), 500


@bp.route("/api/power-apply", methods=["POST"])
@login_required()
def power_apply():
    """Create one or many power-off applications."""
    data = request.get_json() or {}
    user = g.user
    applicant = user.get("realname") or user.get("username")
    applicant_id = user.get("id")
    submitted_device_ids = data.get("deviceIds") or []
    if not submitted_device_ids and data.get("deviceId"):
        submitted_device_ids = [data.get("deviceId")]
    device_ids = [device_id for device_id in dict.fromkeys(submitted_device_ids) if device_id]
    reason = data.get("reason")
    operation_task = data.get("operation_task", "")
    ticket_template = data.get("ticket_template", "")
    power_off_time = data.get("power_off_time")
    power_on_time = data.get("power_on_time", "")

    if not applicant or not applicant_id or not device_ids or not reason or not power_off_time:
        return jsonify({"msg": "必填信息不能为空"}), 400

    try:
        accessible_devices, managed_ids = _get_accessible_devices_for_user(user)
        accessible_map = {item["device_id"]: item for item in accessible_devices}
        managed_id_set = set(managed_ids)

        missing_ids = [device_id for device_id in device_ids if device_id not in accessible_map]
        if missing_ids:
            return jsonify({"msg": "存在不存在、已停用或无权限访问的设备", "invalid_device_ids": missing_ids}), 400

        if managed_id_set:
            unmanaged_ids = [device_id for device_id in device_ids if device_id not in managed_id_set]
            if unmanaged_ids:
                return jsonify({"msg": "存在非本人负责设备，不能提交申请", "invalid_device_ids": unmanaged_ids}), 403

        with get_db_cursor() as cursor:
            conflicts = _find_open_application_conflicts(cursor, device_ids)
            created_applications = []
            joined_applications = []
            skipped_devices = []

            for device_id in device_ids:
                device = accessible_map[device_id]
                if device_id in conflicts:
                    conflict = conflicts[device_id]
                    # 对于“已有挂牌可免停电审批”的设备：允许多人并行提交，直接加入既有工单并新增挂牌记录
                    if device.get("can_skip_approval"):
                        # 确保冲突工单处于免审批可推进状态：若仍在 pending，则自动转为 approved
                        if conflict.get("status") == "pending":
                            transition_application(
                                cursor=cursor,
                                app_id=conflict["id"],
                                expected_status="pending",
                                new_status="approved",
                                operator=applicant,
                                operator_id=applicant_id,
                                operation_type="auto_skip_power_off_approval",
                                comment="设备已存在挂牌且符合免审批配置，系统自动跳过停电审批（多人挂牌加入）",
                                update_fields={
                                    "power_off_approver": "系统自动确认",
                                    "power_off_approver_id": 0,
                                    "power_off_approve_time": raw_sql("NOW()"),
                                    "power_off_approve_comment": "设备当前已存在挂牌且已配置有效信号点，系统跳过停电审批",
                                },
                            )

                        # 在既有工单下为当前提交人创建一条有效挂牌（同工单同电工去重）
                        create_tag_record(
                            conflict["id"],
                            device_id,
                            applicant_id,
                            applicant,
                            cursor=cursor,
                        )
                        write_application_log(
                            cursor,
                            conflict["id"],
                            applicant,
                            applicant_id,
                            "auto_join_tag",
                            "免审批设备：加入既有工单并新增挂牌",
                            conflict.get("status") or "",
                            conflict.get("status") or "",
                        )

                        notify_applicant_confirmation(conflict["id"], applicant_id)
                        joined_applications.append(
                            {
                                "id": conflict["id"],
                                "device_id": device_id,
                                "device_name": device.get("device_name"),
                                "power_room": device.get("power_room"),
                                "status": conflict.get("status") or "approved",
                                "auto_mode": "join_existing_application_add_tag",
                            }
                        )
                        continue

                    skipped_devices.append(
                        {
                            "device_id": device_id,
                            "device_name": device.get("device_name"),
                            "reason": f"已有未完成工单 #{conflict['id']}（状态：{conflict['status']}）",
                        }
                    )
                    continue

                cursor.execute(
                    """
                    INSERT INTO applications
                    (applicant, applicant_id, deviceId, reason, operation_task, ticket_template,
                     power_off_time, power_on_time, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'pending')
                    """,
                    (
                        applicant,
                        applicant_id,
                        device_id,
                        reason,
                        operation_task,
                        ticket_template,
                        power_off_time,
                        power_on_time,
                    ),
                )
                application_id = cursor.lastrowid

                write_application_log(
                    cursor,
                    application_id,
                    applicant,
                    applicant_id,
                    "create",
                    "停电申请",
                    "",
                    "pending",
                )

                current_power_status = device.get("current_power_status")
                auto_mode = None
                if device.get("can_skip_approval"):
                    transition_application(
                        cursor=cursor,
                        app_id=application_id,
                        expected_status="pending",
                        new_status="approved",
                        operator=applicant,
                        operator_id=applicant_id,
                        operation_type="auto_skip_power_off_approval",
                        comment="系统依据当前挂牌状态和信号台账配置，已免停电审批，后续按已挂牌设备流程处理",
                        update_fields={
                            "power_off_approver": "系统自动确认",
                            "power_off_approver_id": 0,
                            "power_off_approve_time": raw_sql("NOW()"),
                            "power_off_approve_comment": "设备当前已存在挂牌且已配置有效信号点，系统跳过停电审批",
                        },
                    )
                    auto_mode = "auto_skip_safety_confirm"
                else:
                    notify_dispatchers_new_application(application_id, applicant, device_id, reason)

                notify_applicant_confirmation(application_id, applicant_id)
                created_applications.append(
                    {
                        "id": application_id,
                        "device_id": device_id,
                        "device_name": device.get("device_name"),
                        "power_room": device.get("power_room"),
                        "status": "approved" if auto_mode == "auto_skip_safety_confirm" else "pending",
                        "auto_mode": auto_mode,
                    }
                )

        if not created_applications and not joined_applications:
            return jsonify(
                {"msg": "没有可提交的设备，所选设备均存在未完工单", "created": [], "joined": [], "skipped": skipped_devices}
            ), 409

        auto_skip_count = sum(1 for item in created_applications if item["auto_mode"] == "auto_skip_safety_confirm")
        msg = f"成功提交 {len(created_applications)} 条停电申请"
        if auto_skip_count > 0:
            msg += f"，其中 {auto_skip_count} 条因设备当前已有挂牌而跳过停电审批"
        if joined_applications:
            msg += f"，另有 {len(joined_applications)} 台设备已加入既有工单并新增挂牌"

        return jsonify(
            {"msg": msg, "created": created_applications, "joined": joined_applications, "skipped": skipped_devices}
        ), 200
    except Exception as exc:
        logger.exception("提交停电申请失败")
        return jsonify({"msg": "提交失败", "error": str(exc)}), 500


@bp.route("/api/list", methods=["GET"])
@login_required()
def get_list():
    """Return applications enriched with device metadata and active tags."""
    user = g.user
    role = user.get("role")
    user_id = user.get("id")

    status = request.args.get("status")
    applicant = request.args.get("applicant")
    device_id = request.args.get("device_id")
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")

    params = []
    query = LIST_SELECT_SQL

    if role == "electrician":
        query += " AND (a.applicant_id = %s OR a.status IN ('approved', 'verified', 'repairing', 'repair_completed', 'power_on_applied'))"
        params.append(user_id)
    elif role not in ("admin", "dispatcher"):
        query += " AND a.applicant_id = %s"
        params.append(user_id)

    room_clause, room_params = user_room_filter_clause(user, "a")
    query += room_clause
    params.extend(room_params)

    if status:
        query += " AND a.status = %s"
        params.append(status)
    if applicant:
        query += " AND a.applicant LIKE %s"
        params.append(f"%{applicant}%")
    if device_id:
        query += " AND a.deviceId LIKE %s"
        params.append(f"%{device_id}%")
    if date_from:
        query += " AND a.created_at >= %s"
        params.append(date_from)
    if date_to:
        query += " AND a.created_at <= %s"
        params.append(date_to)

    query += " ORDER BY a.created_at DESC"

    try:
        with get_db_cursor() as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()
        rows = attach_active_tags(rows)
        my_tag_state_map = {}
        application_ids = [row.get("id") for row in rows if row.get("id")]
        if application_ids:
            placeholders = ",".join(["%s"] * len(application_ids))
            with get_db_cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT application_id, tag_status, MAX(id) AS latest_id
                    FROM device_tag_records
                    WHERE electrician_id = %s
                      AND application_id IN ({placeholders})
                    GROUP BY application_id, tag_status
                    """,
                    [user_id] + application_ids,
                )
                for record in cursor.fetchall():
                    state = my_tag_state_map.setdefault(record["application_id"], {"active": False, "released": False})
                    if record["tag_status"] == "active":
                        state["active"] = True
                    elif record["tag_status"] == "released":
                        state["released"] = True

        managed_ids = set(get_user_managed_device_ids(user_id))
        for row in rows:
            row["is_managed_device"] = row.get("deviceId") in managed_ids
            tag_state = my_tag_state_map.get(row.get("id"), {"active": False, "released": False})
            row["my_active_tag"] = bool(tag_state["active"])
            if tag_state["active"]:
                row["my_tag_state"] = "active"
                row["my_tag_state_text"] = "本人已挂牌"
            elif tag_state["released"]:
                row["my_tag_state"] = "released"
                row["my_tag_state_text"] = "本人已解牌"
            else:
                row["my_tag_state"] = "none"
                row["my_tag_state_text"] = "本人未挂牌"

        return jsonify(rows), 200
    except Exception as exc:
        logger.exception("查询工单列表失败")
        return jsonify({"msg": "查询失败", "error": str(exc)}), 500


@bp.route("/api/electrician-verify", methods=["POST"])
@login_required(role="electrician")
def electrician_verify():
    """Electrician confirms safety measures and starts tag tracking."""
    data = request.get_json() or {}
    app_id = data.get("id")
    safety_measures = data.get("safety_measures", "")
    comment = data.get("comment", "")

    user = g.user
    verifier = user.get("realname") or user.get("username")
    verifier_id = user.get("id")

    try:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT status, deviceId FROM applications WHERE id = %s", (app_id,))
            app = cursor.fetchone()
            if not app:
                return jsonify({"msg": "申请不存在"}), 404
            if app["status"] != "approved":
                return jsonify({"msg": "申请状态不正确"}), 400

            result = transition_application(
                cursor=cursor,
                app_id=app_id,
                expected_status="approved",
                new_status="verified",
                operator=verifier,
                operator_id=verifier_id,
                operation_type="electrician_verify",
                comment=comment,
                update_fields={
                    "electrician_verifier": verifier,
                    "electrician_verifier_id": verifier_id,
                    "electrician_verify_time": raw_sql("NOW()"),
                    "electrician_verify_comment": comment,
                    "safety_measures": safety_measures,
                },
            )
            if not result["ok"]:
                if result["reason"] == "not_found":
                    return jsonify({"msg": "申请不存在"}), 404
                return jsonify({"msg": "申请状态已变化，请刷新后重试"}), 409

            create_tag_record(app_id, app["deviceId"], verifier_id, verifier, cursor=cursor)

        return jsonify({"msg": "验电完成"}), 200
    except Exception as exc:
        logger.exception("验电操作失败")
        return jsonify({"msg": "验电失败", "error": str(exc)}), 500
@bp.route("/api/repair-operation", methods=["POST"])
@login_required(role="electrician")
def repair_operation():
    """Start or finish repair work."""
    data = request.get_json() or {}
    app_id = data.get("id")
    operation = data.get("operation")
    comment = data.get("comment", "")

    user = g.user
    operator = user.get("realname") or user.get("username")
    operator_id = user.get("id")

    if operation not in ("start", "end"):
        return jsonify({"msg": "不支持的检修操作"}), 400

    try:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT status FROM applications WHERE id = %s", (app_id,))
            app = cursor.fetchone()
            if not app:
                return jsonify({"msg": "申请不存在"}), 404

            if operation == "start":
                if app["status"] != "verified":
                    return jsonify({"msg": "申请状态不正确"}), 400
                expected_status = "verified"
                new_status = "repairing"
                update_fields = {
                    "repair_operator": operator,
                    "repair_operator_id": operator_id,
                    "repair_start_time": raw_sql("NOW()"),
                    "repair_comment": comment,
                }
            else:
                if app["status"] != "repairing":
                    return jsonify({"msg": "申请状态不正确"}), 400
                expected_status = "repairing"
                new_status = "repair_completed"
                update_fields = {
                    "repair_end_time": raw_sql("NOW()"),
                    "repair_comment": comment,
                }

            result = transition_application(
                cursor=cursor,
                app_id=app_id,
                expected_status=expected_status,
                new_status=new_status,
                operator=operator,
                operator_id=operator_id,
                operation_type=f"repair_{operation}",
                comment=comment,
                update_fields=update_fields,
            )
            if not result["ok"]:
                if result["reason"] == "not_found":
                    return jsonify({"msg": "申请不存在"}), 404
                return jsonify({"msg": "申请状态已变化，请刷新后重试"}), 409

        return jsonify({"msg": f"检修{operation}操作完成"}), 200
    except Exception as exc:
        logger.exception("检修操作失败")
        return jsonify({"msg": "检修操作失败", "error": str(exc)}), 500
@bp.route("/api/power-on-apply", methods=["POST"])
@login_required(role="electrician")
def power_on_apply():
    """Apply for power-on after repair and self tag release."""
    data = request.get_json() or {}
    user = g.user
    applicant = user.get("realname") or user.get("username")
    applicant_id = user.get("id")
    app_id = data.get("id")
    reason = data.get("comment") or data.get("reason") or data.get("power_on_reason")
    power_on_time = data.get("power_on_time")

    if not app_id or not applicant or not applicant_id or not reason or not power_on_time:
        return jsonify({"msg": "必填信息不能为空"}), 400

    try:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT id, deviceId, status FROM applications WHERE id = %s", (app_id,))
            current_app = cursor.fetchone()
            if not current_app:
                return jsonify({"msg": "工单不存在"}), 404
            if current_app["status"] != "repair_completed":
                return jsonify({"msg": "仅检修完成的工单允许申请送电"}), 400

            device_id = current_app["deviceId"]
            released_count = release_tag_record(
                application_id=app_id,
                device_id=device_id,
                electrician_id=applicant_id,
                electrician_name=applicant,
                comment=reason,
                cursor=cursor,
            )
            if released_count <= 0:
                return jsonify({"msg": "仅挂牌电工本人可申请解牌/送电"}), 400

            remaining_tags = count_active_tags(device_id, cursor=cursor)
            active_tags = get_active_tags_by_device(device_id, cursor=cursor)
            write_application_log(
                cursor,
                app_id,
                applicant,
                applicant_id,
                "tag_release",
                reason,
                "repair_completed",
                "repair_completed",
            )

            if remaining_tags > 0:
                return jsonify(
                    {
                        "msg": f"已解除本人挂牌，但设备仍有 {remaining_tags} 个未解除挂牌，暂不能进入送电审批",
                        "id": app_id,
                        "power_on_ready": False,
                        "remaining_active_tags": active_tags,
                    }
                ), 200

            result = transition_application(
                cursor=cursor,
                app_id=app_id,
                expected_status="repair_completed",
                new_status="power_on_applied",
                operator=applicant,
                operator_id=applicant_id,
                operation_type="power_on_apply",
                comment=reason,
                update_fields={
                    "power_on_applicant": applicant,
                    "power_on_applicant_id": applicant_id,
                    "power_on_apply_time": raw_sql("NOW()"),
                    "power_on_time": power_on_time,
                },
            )
            if not result["ok"]:
                if result["reason"] == "not_found":
                    return jsonify({"msg": "工单不存在"}), 404
                return jsonify({"msg": "申请状态已变化，请刷新后重试"}), 409

            notify_dispatchers_new_application(app_id, applicant, device_id, reason)
            notify_applicant_confirmation(app_id, applicant_id)

        return jsonify(
            {
                "msg": "本人挂牌已解除，且设备无剩余挂牌，送电申请提交成功",
                "id": app_id,
                "power_on_ready": True,
                "remaining_active_tags": [],
            }
        ), 200
    except Exception as exc:
        logger.exception("送电申请失败")
        return jsonify({"msg": "提交失败", "error": str(exc)}), 500
@bp.route("/api/notifications", methods=["GET"])
@login_required()
def get_notifications():
    """Return notifications for the current user."""
    user = g.user
    try:
        notifications = get_user_notifications(user.get("id"))
        return jsonify(notifications), 200
    except Exception as exc:
        return jsonify({"msg": "获取通知失败", "error": str(exc)}), 500


@bp.route("/api/notifications/<int:notification_id>/read", methods=["PUT"])
@login_required()
def mark_notification_read_route(notification_id):
    """Mark a notification as read."""
    user = g.user
    try:
        success = mark_notification_read(notification_id, user.get("id"))
        if success:
            return jsonify({"msg": "标记成功"}), 200
        return jsonify({"msg": "标记失败"}), 500
    except Exception as exc:
        return jsonify({"msg": "标记失败", "error": str(exc)}), 500


@bp.route("/api/device-status", methods=["GET"])
@login_required()
def get_device_status_api():
    """Return device status enriched with master data."""
    try:
        status_map = get_device_status()
        device_meta = {item["device_id"]: item for item in get_active_devices()}
        signal_map = get_signal_points_map(list(device_meta.keys()))
        device_ids = sorted(set(device_meta.keys()) | set(status_map.keys()))
        tag_count_map = {}

        if device_ids:
            placeholders = ",".join(["%s"] * len(device_ids))
            with get_db_cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT device_id, COUNT(*) AS active_tag_count
                    FROM device_tag_records
                    WHERE tag_status = 'active'
                      AND device_id IN ({placeholders})
                    GROUP BY device_id
                    """,
                    device_ids,
                )
                tag_count_map = {
                    row["device_id"]: int(row["active_tag_count"] or 0)
                    for row in cursor.fetchall()
                }
        devices = []

        for device_id in device_ids:
            status = status_map.get(device_id, {})
            meta = device_meta.get(device_id, {})
            signal_info = signal_map.get(
                device_id,
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
            workflow_tag_count = tag_count_map.get(device_id, 0)
            signal_tag_count = status.get("active_tag_count")
            active_tag_count = int(signal_tag_count if signal_tag_count is not None else workflow_tag_count)
            devices.append(
                {
                    "device_id": device_id,
                    "device_name": meta.get("device_name") or f"设备-{device_id}",
                    "power_room": meta.get("power_room"),
                    "cabinet": meta.get("cabinet"),
                    "line_name": meta.get("line_name"),
                    "active_tag_count": active_tag_count,
                    "workflow_tag_count": workflow_tag_count,
                    "signal_tag_count": int(signal_tag_count or 0),
                    "signal_points_count": signal_info.get("signal_points_count", 0),
                    "remote_local_signal": signal_info.get("remote_local_signal"),
                    "power_feedback_signal": signal_info.get("power_feedback_signal"),
                    "tag_count_signal": signal_info.get("tag_count_signal"),
                    "fault_signal": signal_info.get("fault_signal"),
                    "remote_switch_binding": signal_info.get("remote_switch_binding"),
                    "has_signal_config": signal_info.get("has_signal_config", False),
                    "status": status,
                }
            )

        return jsonify(devices), 200
    except Exception as exc:
        logger.exception("获取设备状态失败")
        return jsonify({"msg": "获取设备状态失败", "error": str(exc)}), 500


@bp.route("/api/device-history", methods=["GET"])
@login_required()
def get_device_history_api():
    """Return device history."""
    try:
        return jsonify(get_device_history()), 200
    except Exception:
        logger.exception("获取设备历史失败")
        return jsonify({"msg": "获取设备历史失败"}), 500


@bp.route("/api/device-alerts", methods=["GET"])
@login_required()
def get_device_alerts_api():
    """Return device alerts."""
    try:
        device_status = get_device_status()
        alerts = []
        for device_id, status in device_status.items():
            status_code = status.get("status")
            if status_code in ["error", "offline", "warning"]:
                alerts.append(
                    {
                        "device_id": device_id,
                        "status": status_code,
                        "message": f"设备 {device_id} 状态异常: {status_code}",
                        "timestamp": status.get("last_update"),
                    }
                )
        return jsonify(alerts), 200
    except Exception:
        logger.exception("获取设备告警失败")
        return jsonify({"msg": "获取设备告警失败"}), 500


@bp.route("/api/device-control", methods=["POST"])
@login_required()
def device_control_api():
    """Legacy control endpoint removed from the platform."""
    return (
        jsonify(
            {
                "msg": "当前系统不再负责停送电执行，请在线下执行后结合设备监控页面的 OPC UA 状态确认现场结果。",
            }
        ),
        410,
    )
