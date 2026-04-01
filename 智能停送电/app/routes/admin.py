import csv
import io
import logging

from flask import Blueprint, Response, g, jsonify, request
from werkzeug.security import generate_password_hash

from app.auth import login_required
from app.database import get_db_cursor
from app.services.batch_approval_service import process_batch_approval
from app.services.authz_service import (
    DEFAULT_FUNCTION_PERMISSIONS,
    set_user_function_permissions,
    set_user_room_scopes,
)

bp = Blueprint("admin", __name__)
logger = logging.getLogger(__name__)


FUNCTION_PERMISSION_OPTIONS = [
    {"code": "approval_center", "label": "审批中心"},
    {"code": "batch_approval", "label": "批量审批"},
    {"code": "batch_management", "label": "大检修批次"},
    {"code": "device_monitor", "label": "设备监控"},
    {"code": "notifications", "label": "通知"},
    {"code": "stats", "label": "统计"},
    {"code": "user_management", "label": "用户管理"},
    {"code": "apply", "label": "停电申请"},
    {"code": "repair", "label": "检修处理"},
    {"code": "power_on_apply", "label": "送电申请"},
]


TERMINAL_BATCH_APPLICATION_STATUSES = {"completed", "rejected", "power_on_rejected"}
IN_PROGRESS_BATCH_APPLICATION_STATUSES = {"approved", "verified", "repairing", "repair_completed", "power_on_applied"}


def build_batch_summary(items):
    total_devices = len(items)
    generated_count = sum(1 for item in items if item.get("application_id"))
    pending_approval_count = sum(1 for item in items if item.get("application_status") == "pending")
    in_progress_count = sum(1 for item in items if item.get("application_status") in IN_PROGRESS_BATCH_APPLICATION_STATUSES)
    completed_count = sum(1 for item in items if item.get("application_status") == "completed")
    rejected_count = sum(1 for item in items if item.get("application_status") in ("rejected", "power_on_rejected"))
    risk_count = sum(1 for item in items if int(item.get("active_tag_count") or 0) > 0)
    blocked_count = sum(1 for item in items if item.get("is_blocked"))
    terminal_count = sum(1 for item in items if item.get("application_status") in TERMINAL_BATCH_APPLICATION_STATUSES)
    ungenerated_count = sum(1 for item in items if not item.get("application_id"))

    return {
        "total_devices": total_devices,
        "generated_count": generated_count,
        "pending_approval_count": pending_approval_count,
        "in_progress_count": in_progress_count,
        "completed_count": completed_count,
        "rejected_count": rejected_count,
        "risk_count": risk_count,
        "blocked_count": blocked_count,
        "terminal_count": terminal_count,
        "ungenerated_count": ungenerated_count,
        "can_complete": generated_count > 0 and terminal_count == total_devices and risk_count == 0 and ungenerated_count == 0,
    }


def derive_batch_status(items):
    summary = build_batch_summary(items)
    if summary["generated_count"] == 0:
        return "draft", summary
    if summary["can_complete"]:
        return "completed", summary
    if summary["in_progress_count"] > 0 or summary["completed_count"] > 0 or summary["rejected_count"] > 0:
        return "in_progress", summary
    return "generated", summary


def load_batch_items(cursor, batch_id):
    cursor.execute(
        """
        SELECT
            d.batch_id,
            d.device_id,
            d.application_id,
            d.item_status,
            dm.device_name,
            dm.power_room,
            dm.cabinet,
            a.status AS application_status,
            a.applicant,
            a.reason,
            a.created_at AS application_created_at,
            a.power_off_time,
            a.power_on_time,
            COALESCE(tag_summary.active_tag_count, 0) AS active_tag_count
        FROM maintenance_batch_devices d
        LEFT JOIN devices dm ON dm.device_id = d.device_id
        LEFT JOIN applications a ON a.id = d.application_id
        LEFT JOIN (
            SELECT device_id, COUNT(*) AS active_tag_count
            FROM device_tag_records
            WHERE tag_status = 'active'
            GROUP BY device_id
        ) tag_summary ON tag_summary.device_id = d.device_id
        WHERE d.batch_id = %s
        ORDER BY dm.sort_order ASC, d.device_id ASC
        """,
        (batch_id,),
    )
    items = cursor.fetchall()

    device_ids = [item["device_id"] for item in items if item.get("device_id")]
    tag_names = {}
    if device_ids:
        placeholders = ",".join(["%s"] * len(device_ids))
        cursor.execute(
            f"""
            SELECT device_id, electrician_name
            FROM device_tag_records
            WHERE tag_status = 'active'
              AND device_id IN ({placeholders})
            ORDER BY tag_time ASC, id ASC
            """,
            device_ids,
        )
        for row in cursor.fetchall():
            tag_names.setdefault(row["device_id"], []).append(row["electrician_name"])

    for item in items:
        item["active_tag_names"] = tag_names.get(item["device_id"], [])
        item["is_blocked"] = item.get("application_status") in ("repair_completed", "power_on_applied") and int(item.get("active_tag_count") or 0) > 0

    return items


def sync_batch_status(cursor, batch_id):
    items = load_batch_items(cursor, batch_id)
    next_status, summary = derive_batch_status(items)
    cursor.execute(
        """
        UPDATE maintenance_batches
        SET batch_status = %s
        WHERE id = %s
        """,
        (next_status, batch_id),
    )
    return next_status, summary, items


@bp.route("/api/users", methods=["GET"])
@login_required(role="admin")
def get_users():
    try:
        with get_db_cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    u.id,
                    u.username,
                    u.realname,
                    u.role,
                    u.created_at,
                    GROUP_CONCAT(DISTINCT urs.power_room ORDER BY urs.power_room SEPARATOR '||') AS room_scopes,
                    GROUP_CONCAT(DISTINCT ufp.permission_code ORDER BY ufp.permission_code SEPARATOR '||') AS function_permissions
                FROM users u
                LEFT JOIN user_room_scopes urs ON urs.user_id = u.id
                LEFT JOIN user_function_permissions ufp ON ufp.user_id = u.id
                GROUP BY u.id, u.username, u.realname, u.role, u.created_at
                ORDER BY u.created_at DESC
                """
            )
            users = cursor.fetchall()

        for user in users:
            user["room_scopes"] = user["room_scopes"].split("||") if user.get("room_scopes") else []
            user["function_permissions"] = (
                user["function_permissions"].split("||")
                if user.get("function_permissions")
                else DEFAULT_FUNCTION_PERMISSIONS.get(user["role"], [])
            )
        return jsonify(users), 200
    except Exception:
        logger.exception("获取用户列表失败")
        return jsonify({"msg": "获取用户列表失败"}), 500


@bp.route("/api/permission-options", methods=["GET"])
@login_required(role="admin")
def get_permission_options():
    try:
        with get_db_cursor() as cursor:
            cursor.execute(
                """
                SELECT DISTINCT power_room
                FROM devices
                WHERE is_active = TRUE
                  AND power_room IS NOT NULL
                  AND power_room <> ''
                ORDER BY power_room ASC
                """
            )
            rooms = [row["power_room"] for row in cursor.fetchall()]
        return jsonify({"rooms": rooms, "function_permissions": FUNCTION_PERMISSION_OPTIONS}), 200
    except Exception:
        logger.exception("获取权限选项失败")
        return jsonify({"msg": "获取权限选项失败"}), 500


@bp.route("/api/users/<int:user_id>", methods=["DELETE"])
@login_required(role="admin")
def delete_user(user_id):
    try:
        with get_db_cursor() as cursor:
            cursor.execute("DELETE FROM users WHERE id = %s AND role <> 'admin'", (user_id,))
            if cursor.rowcount != 1:
                return jsonify({"msg": "管理员账号不允许删除，或用户不存在"}), 400
        return jsonify({"msg": "删除成功"}), 200
    except Exception:
        logger.exception("删除用户失败: user_id=%s", user_id)
        return jsonify({"msg": "删除失败"}), 500


@bp.route("/api/users/<int:user_id>", methods=["PUT"])
@login_required(role="admin")
def update_user(user_id):
    data = request.get_json() or {}
    realname = (data.get("realname") or "").strip()
    role = data.get("role")
    password = (data.get("password") or "").strip()
    room_scopes = data.get("room_scopes") or []
    function_permissions = data.get("function_permissions") or []

    if not realname or role not in ("admin", "dispatcher", "electrician", "user"):
        return jsonify({"msg": "用户信息不完整"}), 400

    try:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
            if not cursor.fetchone():
                return jsonify({"msg": "用户不存在"}), 404

            if password:
                cursor.execute(
                    """
                    UPDATE users
                    SET realname = %s, role = %s, password = %s
                    WHERE id = %s
                    """,
                    (realname, role, generate_password_hash(password), user_id),
                )
            else:
                cursor.execute(
                    """
                    UPDATE users
                    SET realname = %s, role = %s
                    WHERE id = %s
                    """,
                    (realname, role, user_id),
                )

            if role == "admin":
                room_scopes = []
                function_permissions = DEFAULT_FUNCTION_PERMISSIONS["admin"]
            elif not function_permissions:
                function_permissions = DEFAULT_FUNCTION_PERMISSIONS.get(role, [])

            set_user_room_scopes(cursor, user_id, room_scopes)
            set_user_function_permissions(cursor, user_id, function_permissions)

        return jsonify({"msg": "更新成功"}), 200
    except Exception:
        logger.exception("更新用户失败: user_id=%s", user_id)
        return jsonify({"msg": "更新失败"}), 500


@bp.route("/api/system/metrics", methods=["GET"])
@login_required(role="admin")
def get_system_metrics():
    try:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS total FROM applications")
            app_count = cursor.fetchone()["total"]

            cursor.execute("SELECT COUNT(*) AS total FROM users")
            user_count = cursor.fetchone()["total"]

            cursor.execute("SELECT COUNT(*) AS today FROM applications WHERE DATE(created_at) = CURDATE()")
            today_count = cursor.fetchone()["today"]

        return jsonify(
            {
                "applications": app_count,
                "users": user_count,
                "today_applications": today_count,
            }
        ), 200
    except Exception:
        logger.exception("获取系统指标失败")
        return jsonify({"msg": "获取系统指标失败"}), 500


@bp.route("/api/maintenance-batches", methods=["GET"])
@login_required(role="admin")
def get_maintenance_batches():
    try:
        power_room = (request.args.get("power_room") or "").strip()
        batch_status = (request.args.get("batch_status") or "").strip()
        keyword = (request.args.get("keyword") or "").strip()

        where_clauses = ["1 = 1"]
        params = []
        if power_room:
            where_clauses.append("b.power_room = %s")
            params.append(power_room)
        if batch_status:
            where_clauses.append("b.batch_status = %s")
            params.append(batch_status)
        if keyword:
            where_clauses.append("(b.batch_name LIKE %s OR b.description LIKE %s)")
            params.extend([f"%{keyword}%", f"%{keyword}%"])

        with get_db_cursor() as cursor:
            cursor.execute(
                f"""
                SELECT
                    b.*,
                    COUNT(d.id) AS device_count,
                    SUM(CASE WHEN d.application_id IS NOT NULL THEN 1 ELSE 0 END) AS generated_count,
                    SUM(CASE WHEN a.status = 'pending' THEN 1 ELSE 0 END) AS pending_count,
                    SUM(CASE WHEN a.status IN ('approved', 'verified', 'repairing', 'repair_completed', 'power_on_applied') THEN 1 ELSE 0 END) AS in_progress_count,
                    SUM(CASE WHEN a.status = 'completed' THEN 1 ELSE 0 END) AS completed_count,
                    SUM(CASE WHEN a.status IN ('rejected', 'power_on_rejected') THEN 1 ELSE 0 END) AS rejected_count,
                    SUM(CASE WHEN COALESCE(tag_summary.active_tag_count, 0) > 0 THEN 1 ELSE 0 END) AS risk_count
                FROM maintenance_batches b
                LEFT JOIN maintenance_batch_devices d ON d.batch_id = b.id
                LEFT JOIN applications a ON a.id = d.application_id
                LEFT JOIN (
                    SELECT device_id, COUNT(*) AS active_tag_count
                    FROM device_tag_records
                    WHERE tag_status = 'active'
                    GROUP BY device_id
                ) tag_summary ON tag_summary.device_id = d.device_id
                WHERE {' AND '.join(where_clauses)}
                GROUP BY b.id
                ORDER BY b.created_at DESC
                """,
                params,
            )
            batches = cursor.fetchall()

        summary = {
            "total_batches": len(batches),
            "generated_batches": sum(1 for batch in batches if batch.get("batch_status") == "generated"),
            "draft_batches": sum(1 for batch in batches if batch.get("batch_status") == "draft"),
            "device_count": sum(int(batch.get("device_count") or 0) for batch in batches),
            "pending_count": sum(int(batch.get("pending_count") or 0) for batch in batches),
            "in_progress_count": sum(int(batch.get("in_progress_count") or 0) for batch in batches),
            "completed_count": sum(int(batch.get("completed_count") or 0) for batch in batches),
            "risk_count": sum(int(batch.get("risk_count") or 0) for batch in batches),
        }
        return jsonify({"items": batches, "summary": summary}), 200
    except Exception:
        logger.exception("获取大检修批次失败")
        return jsonify({"msg": "获取大检修批次失败"}), 500

@bp.route("/api/maintenance-batches", methods=["POST"])
@login_required(role="admin", permission="batch_management")
def create_maintenance_batch():
    data = request.get_json() or {}
    batch_name = (data.get("batch_name") or "").strip()
    power_room = (data.get("power_room") or "").strip()
    description = (data.get("description") or "").strip()
    planned_start_time = data.get("planned_start_time")
    planned_end_time = data.get("planned_end_time")
    reason = (data.get("reason") or "").strip()
    device_ids = data.get("device_ids") or []

    if not batch_name or not power_room or not reason or not device_ids:
        return jsonify({"msg": "批次名称、配电室、停电原因和设备清单不能为空"}), 400

    creator = g.user.get("realname") or g.user.get("username")
    creator_id = g.user.get("id")

    try:
        with get_db_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO maintenance_batches
                (batch_name, power_room, batch_status, description, planned_start_time, planned_end_time, created_by_id, created_by_name)
                VALUES (%s, %s, 'draft', %s, %s, %s, %s, %s)
                """,
                (batch_name, power_room, description, planned_start_time, planned_end_time, creator_id, creator),
            )
            batch_id = cursor.lastrowid

            normalized_device_ids = sorted(set(device_ids))
            for device_id in normalized_device_ids:
                cursor.execute(
                    """
                    INSERT INTO maintenance_batch_devices (batch_id, device_id)
                    VALUES (%s, %s)
                    """,
                    (batch_id, device_id),
                )

            created_applications = []
            for device_id in normalized_device_ids:
                cursor.execute(
                    """
                    INSERT INTO applications
                    (applicant, applicant_id, deviceId, reason, operation_task, ticket_template,
                     power_off_time, power_on_time, status, batch_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'pending', %s)
                    """,
                    (
                        creator,
                        creator_id,
                        device_id,
                        reason,
                        f"大检修批次：{batch_name}",
                        "",
                        planned_start_time or "",
                        planned_end_time or "",
                        batch_id,
                    ),
                )
                application_id = cursor.lastrowid
                created_applications.append(application_id)

                cursor.execute(
                    """
                    UPDATE maintenance_batch_devices
                    SET application_id = %s, item_status = 'generated'
                    WHERE batch_id = %s AND device_id = %s
                    """,
                    (application_id, batch_id, device_id),
                )

                cursor.execute(
                    """
                    INSERT INTO application_logs
                    (application_id, operator, operator_id, operation_type, operation_comment, old_status, new_status)
                    VALUES (%s, %s, %s, 'create', %s, '', 'pending')
                    """,
                    (application_id, creator, creator_id, f"批次建单：{batch_name}"),
                )

            cursor.execute(
                """
                UPDATE maintenance_batches
                SET batch_status = 'generated'
                WHERE id = %s
                """,
                (batch_id,),
            )
            sync_batch_status(cursor, batch_id)

        return jsonify({"msg": "大检修批次创建成功", "batch_id": batch_id, "application_ids": created_applications}), 200
    except Exception:
        logger.exception("创建大检修批次失败")
        return jsonify({"msg": "创建大检修批次失败"}), 500

@bp.route("/api/maintenance-batches/<int:batch_id>", methods=["GET"])
@login_required(role="admin")
def get_maintenance_batch_detail(batch_id):
    try:
        with get_db_cursor() as cursor:
            cursor.execute(
                """
                SELECT *
                FROM maintenance_batches
                WHERE id = %s
                """,
                (batch_id,),
            )
            batch = cursor.fetchone()
            if not batch:
                return jsonify({"msg": "批次不存在"}), 404
            batch_status, summary, items = sync_batch_status(cursor, batch_id)
            batch["batch_status"] = batch_status

        return jsonify({"batch": batch, "summary": summary, "items": items}), 200
    except Exception:
        logger.exception("获取大检修批次详情失败")
        return jsonify({"msg": "获取大检修批次详情失败"}), 500


@bp.route("/api/maintenance-batches/<int:batch_id>/export", methods=["GET"])
@login_required(role="admin")
def export_maintenance_batch(batch_id):
    try:
        with get_db_cursor() as cursor:
            cursor.execute(
                """
                SELECT id
                FROM maintenance_batches
                WHERE id = %s
                """,
                (batch_id,),
            )
            if not cursor.fetchone():
                return jsonify({"msg": "批次不存在"}), 404

            cursor.execute(
                """
                SELECT batch_name
                FROM maintenance_batches
                WHERE id = %s
                """,
                (batch_id,),
            )
            batch = cursor.fetchone()
            if not batch:
                return jsonify({"msg": "批次不存在"}), 404

            cursor.execute(
                """
                SELECT
                    d.device_id,
                    dm.device_name,
                    dm.power_room,
                    dm.cabinet,
                    d.application_id,
                    a.status AS application_status,
                    a.reason,
                    a.created_at AS application_created_at,
                    a.power_off_time,
                    a.power_on_time,
                    COALESCE(tag_summary.active_tag_count, 0) AS active_tag_count
                FROM maintenance_batch_devices d
                LEFT JOIN devices dm ON dm.device_id = d.device_id
                LEFT JOIN applications a ON a.id = d.application_id
                LEFT JOIN (
                    SELECT device_id, COUNT(*) AS active_tag_count
                    FROM device_tag_records
                    WHERE tag_status = 'active'
                    GROUP BY device_id
                ) tag_summary ON tag_summary.device_id = d.device_id
                WHERE d.batch_id = %s
                ORDER BY dm.sort_order ASC, d.device_id ASC
                """,
                (batch_id,),
            )
            rows = cursor.fetchall()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "批次ID",
                "批次名称",
                "设备编号",
                "设备名称",
                "配电室",
                "柜号",
                "工单ID",
                "工单状态",
                "停电原因",
                "申请时间",
                "计划停电时间",
                "计划送电时间",
                "剩余挂牌数",
            ]
        )

        for row in rows:
            writer.writerow(
                [
                    batch_id,
                    batch["batch_name"],
                    row.get("device_id") or "",
                    row.get("device_name") or "",
                    row.get("power_room") or "",
                    row.get("cabinet") or "",
                    row.get("application_id") or "",
                    row.get("application_status") or "",
                    row.get("reason") or "",
                    row["application_created_at"].strftime("%Y-%m-%d %H:%M:%S") if row.get("application_created_at") else "",
                    row.get("power_off_time") or "",
                    row.get("power_on_time") or "",
                    int(row.get("active_tag_count") or 0),
                ]
            )

        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment; filename=batch_{batch_id}.csv"},
        )
    except Exception:
        logger.exception("导出大检修批次失败")
        return jsonify({"msg": "导出大检修批次失败"}), 500


@bp.route("/api/maintenance-batches/<int:batch_id>/approve", methods=["POST"])
@login_required(permission="batch_approval")
def approve_maintenance_batch(batch_id):
    data = request.get_json() or {}
    stage = data.get("stage")
    action = data.get("action")
    comment = (data.get("comment") or "").strip()

    if stage not in ("power_off", "power_on"):
        return jsonify({"msg": "批量审批阶段不正确"}), 400
    if action not in ("approve", "reject"):
        return jsonify({"msg": "批量审批动作不正确"}), 400
    if action == "reject" and not comment:
        return jsonify({"msg": "批量驳回时必须填写意见"}), 400

    approver = g.user.get("realname") or g.user.get("username")
    approver_id = g.user.get("id")
    target_status = "pending" if stage == "power_off" else "power_on_applied"
    new_status = (
        "approved" if stage == "power_off" and action == "approve" else
        "rejected" if stage == "power_off" else
        "completed" if action == "approve" else
        "power_on_rejected"
    )

    try:
        with get_db_cursor() as cursor:
            cursor.execute(
                """
                SELECT id, batch_name, power_room
                FROM maintenance_batches
                WHERE id = %s
                """,
                (batch_id,),
            )
            batch = cursor.fetchone()
            if not batch:
                return jsonify({"msg": "批次不存在"}), 404

            cursor.execute(
                """
                SELECT a.id, a.applicant_id, a.deviceId
                FROM maintenance_batch_devices d
                INNER JOIN applications a ON a.id = d.application_id
                WHERE d.batch_id = %s
                  AND a.status = %s
                ORDER BY a.created_at ASC, a.id ASC
                """,
                (batch_id, target_status),
            )
            applications = cursor.fetchall()
            if not applications:
                return jsonify({"msg": "当前批次没有可批量处理的工单"}), 404

            process_result = process_batch_approval(
                cursor=cursor,
                applications=applications,
                stage=stage,
                action=action,
                approver=approver,
                approver_id=approver_id,
                comment=comment,
            )
            processed_ids = process_result["processed_ids"]
            skipped = process_result["skipped"]

            batch_status, _, _ = sync_batch_status(cursor, batch_id)

        return jsonify(
            {
                "msg": f"批次批量处理完成，成功 {len(processed_ids)} 条，跳过 {len(skipped)} 条",
                "batch_id": batch_id,
                "batch_name": batch["batch_name"],
                "power_room": batch["power_room"],
                "batch_status": batch_status,
                "stage": stage,
                "action": action,
                "processed_ids": processed_ids,
                "skipped": skipped,
            }
        ), 200
    except Exception as exc:
        logger.exception("批次批量审批失败: batch_id=%s", batch_id)
        return jsonify({"msg": "批次批量审批失败", "error": str(exc)}), 500


@bp.route("/api/maintenance-batches/<int:batch_id>/close", methods=["POST"])
@login_required(role="admin", permission="batch_management")
def close_maintenance_batch(batch_id):
    try:
        with get_db_cursor() as cursor:
            cursor.execute(
                """
                SELECT id, batch_name, batch_status
                FROM maintenance_batches
                WHERE id = %s
                """,
                (batch_id,),
            )
            batch = cursor.fetchone()
            if not batch:
                return jsonify({"msg": "批次不存在"}), 404

            next_status, summary, items = sync_batch_status(cursor, batch_id)
            if next_status != "completed":
                blockers = []
                if summary["ungenerated_count"] > 0:
                    blockers.append(f"还有 {summary['ungenerated_count']} 台设备未生成工单")
                if summary["pending_approval_count"] > 0:
                    blockers.append(f"还有 {summary['pending_approval_count']} 条待停电审批工单")
                if summary["in_progress_count"] > 0:
                    blockers.append(f"还有 {summary['in_progress_count']} 条处理中工单")
                if summary["risk_count"] > 0:
                    blockers.append(f"还有 {summary['risk_count']} 台设备存在有效挂牌")
                if not blockers:
                    blockers.append("当前批次未达到完成条件")
                return jsonify(
                    {
                        "msg": "当前批次暂不能完成",
                        "batch_id": batch_id,
                        "batch_status": next_status,
                        "summary": summary,
                        "blockers": blockers,
                    }
                ), 400

        return jsonify(
            {
                "msg": "批次已完成",
                "batch_id": batch_id,
                "batch_name": batch["batch_name"],
                "batch_status": "completed",
                "summary": summary,
                "item_count": len(items),
            }
        ), 200
    except Exception as exc:
        logger.exception("完成大检修批次失败: batch_id=%s", batch_id)
        return jsonify({"msg": "完成大检修批次失败", "error": str(exc)}), 500

