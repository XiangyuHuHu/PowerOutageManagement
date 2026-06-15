"""
审批相关路由。
"""

import csv
import io
import logging

from flask import Blueprint, Response, g, jsonify, request

from app.auth import login_required, user_room_filter_clause
from app.database import get_db_cursor
from app.services.batch_approval_service import process_batch_approval
from app.services.room_names import db_values_for_room_group
from app.notifications import notify_approval_result
from app.services.application_flow_service import get_application, raw_sql, transition_application, write_application_log
from app.services.tag_service import count_active_tags, create_tag_record, get_active_tags_by_device, get_tag_records_by_application

bp = Blueprint("approvals", __name__)
logger = logging.getLogger(__name__)


DETAIL_SELECT_SQL = """
    SELECT
        a.*,
        u.realname AS applicant_realname,
        u.role AS applicant_role,
        d.device_name,
        d.power_room,
        d.cabinet,
        d.area_code,
        d.line_name
    FROM applications a
    LEFT JOIN users u ON a.applicant_id = u.id
    LEFT JOIN devices d ON d.device_id = a.deviceId
    WHERE a.id = %s
"""


def _conflict_response():
    return jsonify({"msg": "申请状态已变化，请刷新后重试"}), 409


@bp.route("/api/power-off-approve", methods=["POST"])
@login_required(role="dispatcher")
def power_off_approve():
    data = request.get_json() or {}
    app_id = data.get("id")
    approve_action = data.get("action")
    comment = (data.get("comment") or "").strip()

    if approve_action not in ("approve", "reject"):
        return jsonify({"msg": "审批动作不正确"}), 400
    if approve_action == "reject" and not comment:
        return jsonify({"msg": "驳回时必须填写审批意见"}), 400

    user = g.user
    approver = user.get("realname") or user.get("username")
    approver_id = user.get("id")
    new_status = "approved" if approve_action == "approve" else "rejected"

    try:
        with get_db_cursor() as cursor:
            cursor.execute(
                """
                SELECT a.deviceId, a.applicant_id, a.applicant, u.role AS applicant_role
                FROM applications a
                LEFT JOIN users u ON u.id = a.applicant_id
                WHERE a.id = %s
                """,
                (app_id,),
            )
            application = cursor.fetchone()
            if not application:
                return jsonify({"msg": "申请不存在"}), 404

            result = transition_application(
                cursor=cursor,
                app_id=app_id,
                expected_status="pending",
                new_status=new_status,
                operator=approver,
                operator_id=approver_id,
                operation_type="power_off_approve",
                comment=comment,
                update_fields={
                    "power_off_approver": approver,
                    "power_off_approver_id": approver_id,
                    "power_off_approve_time": raw_sql("NOW()"),
                    "power_off_approve_comment": comment,
                },
            )
            if not result["ok"]:
                if result["reason"] == "not_found":
                    return jsonify({"msg": "申请不存在"}), 404
                return _conflict_response()

            if approve_action == "approve" and application.get("applicant_id") and application.get("applicant_role") == "electrician":
                create_tag_record(
                    app_id,
                    application["deviceId"],
                    application["applicant_id"],
                    application.get("applicant") or approver,
                    cursor=cursor,
                )
                write_application_log(
                    cursor,
                    app_id,
                    "系统自动挂牌",
                    0,
                    "auto_tag_create",
                    "停电审批通过后，系统已自动建立申请人挂牌记录",
                    "approved",
                    "approved",
                )

            if application.get("applicant_id"):
                notify_approval_result(
                    app_id,
                    application["applicant_id"],
                    approve_action == "approve",
                    approver,
                    comment,
                )

        return jsonify({"msg": "审批完成", "status": new_status}), 200
    except Exception as exc:
        logger.exception("停电审批异常")
        return jsonify({"msg": "审批失败", "error": str(exc)}), 500


@bp.route("/api/power-on-approve", methods=["POST"])
@login_required(role="dispatcher")
def power_on_approve():
    data = request.get_json() or {}
    app_id = data.get("id")
    approved = data.get("approved")
    action = data.get("action")
    if approved is None and action is not None:
        approved = action == "approve"
    comment = (data.get("comment") or "").strip()

    if approved is None:
        return jsonify({"msg": "审批动作不正确"}), 400
    if approved is False and not comment:
        return jsonify({"msg": "驳回时必须填写审批意见"}), 400

    user = g.user
    approver = user.get("realname") or user.get("username")
    approver_id = user.get("id")

    try:
        with get_db_cursor() as cursor:
            app = get_application(cursor, app_id, fields=["status", "applicant_id", "deviceId"])
            if not app:
                return jsonify({"msg": "申请不存在"}), 404
            if app["status"] != "power_on_applied":
                return jsonify({"msg": "仅送电申请中的工单可审批"}), 400

            remaining_tags = count_active_tags(app["deviceId"])
            if approved and remaining_tags > 0:
                return jsonify(
                    {
                        "msg": f"设备仍有 {remaining_tags} 个未解除挂牌，禁止送电审批通过",
                        "remaining_active_tags": get_active_tags_by_device(app["deviceId"]),
                    }
                ), 400

            new_status = "completed" if approved else "power_on_rejected"
            update_fields = {
                "power_on_approver": approver,
                "power_on_approver_id": approver_id,
                "power_on_approve_time": raw_sql("NOW()"),
                "power_on_approve_comment": comment,
            }
            if new_status == "completed":
                update_fields["completed_time"] = raw_sql("NOW()")

            result = transition_application(
                cursor=cursor,
                app_id=app_id,
                expected_status="power_on_applied",
                new_status=new_status,
                operator=approver,
                operator_id=approver_id,
                operation_type="power_on_approve",
                comment=comment,
                update_fields=update_fields,
            )
            if not result["ok"]:
                if result["reason"] == "not_found":
                    return jsonify({"msg": "申请不存在"}), 404
                return _conflict_response()

            notify_approval_result(app_id, app["applicant_id"], approved, approver, comment)

        return jsonify({"msg": "审批完成", "status": new_status}), 200
    except Exception as exc:
        logger.exception("送电审批异常")
        return jsonify({"msg": "审批失败", "error": str(exc)}), 500


@bp.route("/api/batch-approve-room", methods=["POST"])
@login_required(role="dispatcher", permission="batch_approval")
def batch_approve_room():
    data = request.get_json() or {}
    power_room = (data.get("power_room") or "").strip()
    stage = data.get("stage")
    action = data.get("action")
    comment = (data.get("comment") or "").strip()

    if not power_room:
        return jsonify({"msg": "缺少配电室"}), 400
    if stage not in ("power_off", "power_on"):
        return jsonify({"msg": "批量审批阶段不正确"}), 400
    if action not in ("approve", "reject"):
        return jsonify({"msg": "批量审批动作不正确"}), 400
    if action == "reject" and not comment:
        return jsonify({"msg": "批量驳回时必须填写意见"}), 400

    user = g.user
    room_clause, room_params = user_room_filter_clause(user, "a")
    room_keys = db_values_for_room_group(power_room)
    if not room_keys:
        return jsonify({"msg": "缺少配电室"}), 400
    scopes = user.get("room_scopes") or []
    if room_clause and not user.get("access_all_rooms"):
        allowed = set(scopes) & set(room_keys)
        if not allowed and power_room not in scopes:
            return jsonify({"msg": "无此配电室审批权限"}), 403

    approver = user.get("realname") or user.get("username")
    approver_id = user.get("id")
    target_status = "pending" if stage == "power_off" else "power_on_applied"
    try:
        with get_db_cursor() as cursor:
            in_ph = ",".join(["%s"] * len(room_keys))
            query = f"""
                SELECT a.id, a.applicant_id, a.deviceId
                FROM applications a
                LEFT JOIN devices d ON d.device_id = a.deviceId
                WHERE a.status = %s
                  AND COALESCE(d.power_room, '') IN ({in_ph})
                  {room_clause}
                ORDER BY a.created_at ASC
            """
            cursor.execute(query, [target_status, *room_keys] + room_params)
            applications = cursor.fetchall()
            if not applications:
                return jsonify({"msg": "当前配电室没有可批量处理的工单"}), 404

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

        return jsonify(
            {
                "msg": f"批量处理完成，成功 {len(processed_ids)} 条，跳过 {len(skipped)} 条",
                "processed_ids": processed_ids,
                "skipped": skipped,
                "stage": stage,
                "action": action,
                "power_room": power_room,
            }
        ), 200
    except Exception as exc:
        logger.exception("批量审批异常")
        return jsonify({"msg": "批量审批失败", "error": str(exc)}), 500


@bp.route("/api/application/<int:app_id>", methods=["GET"])
@login_required()
def get_application_detail(app_id):
    user = g.user
    user_id = user.get("id")
    role = user.get("role")

    try:
        with get_db_cursor() as cursor:
            if role not in ["admin", "dispatcher"]:
                cursor.execute("SELECT applicant_id FROM applications WHERE id = %s", (app_id,))
                app = cursor.fetchone()
                if not app or app["applicant_id"] != user_id:
                    return jsonify({"msg": "无权查看此申请"}), 403

            query = DETAIL_SELECT_SQL
            params = [app_id]
            room_clause, room_params = user_room_filter_clause(user, "a")
            if role == "dispatcher" and room_clause:
                query += room_clause
                params.extend(room_params)

            cursor.execute(query, params)
            application = cursor.fetchone()
            if not application:
                return jsonify({"msg": "申请不存在"}), 404

            cursor.execute(
                """
                SELECT *
                FROM application_logs
                WHERE application_id = %s
                ORDER BY operation_time DESC, id DESC
                """,
                (app_id,),
            )
            logs = cursor.fetchall()

        tag_records = get_tag_records_by_application(app_id)
        application["logs"] = logs
        application["tag_records"] = tag_records
        application["active_tag_count"] = count_active_tags(application["deviceId"])
        application["active_tags"] = get_active_tags_by_device(application["deviceId"])

        return jsonify({"application": application, "logs": logs, "tag_records": tag_records}), 200
    except Exception as exc:
        logger.exception("获取申请详情异常")
        return jsonify({"msg": "获取详情失败", "error": str(exc)}), 500


@bp.route("/api/approval-history", methods=["GET"])
@login_required()
def get_approval_history():
    user = g.user
    role = user.get("role")
    user_id = user.get("id")

    query = """
        SELECT
            l.id AS log_id,
            l.application_id,
            l.operator,
            l.operator_id,
            l.operation_type,
            l.operation_comment,
            l.old_status,
            l.new_status,
            l.operation_time,
            a.applicant,
            a.applicant_id,
            a.deviceId,
            a.reason,
            a.status AS current_status,
            a.batch_id,
            d.device_name,
            d.power_room,
            d.cabinet,
            b.batch_name
        FROM application_logs l
        INNER JOIN applications a ON a.id = l.application_id
        LEFT JOIN devices d ON d.device_id = a.deviceId
        LEFT JOIN maintenance_batches b ON b.id = a.batch_id
        WHERE 1 = 1
    """
    params = []

    if role == "electrician":
        query += " AND (a.applicant_id = %s OR l.operator_id = %s)"
        params.extend([user_id, user_id])
    elif role not in ("admin", "dispatcher"):
        query += " AND a.applicant_id = %s"
        params.append(user_id)

    room_clause, room_params = user_room_filter_clause(user, "a")
    query += room_clause
    params.extend(room_params)

    application_id = request.args.get("application_id")
    device_id = request.args.get("device_id")
    operation_type = request.args.get("operation_type")
    batch_id = request.args.get("batch_id")

    if application_id:
        query += " AND l.application_id = %s"
        params.append(application_id)
    if device_id:
        query += " AND a.deviceId LIKE %s"
        params.append(f"%{device_id}%")
    if operation_type:
        query += " AND l.operation_type = %s"
        params.append(operation_type)
    if batch_id:
        query += " AND a.batch_id = %s"
        params.append(batch_id)

    query += " ORDER BY l.operation_time DESC, l.id DESC"

    try:
        with get_db_cursor() as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()
        return jsonify(rows), 200
    except Exception as exc:
        logger.exception("获取审批记录异常")
        return jsonify({"msg": "获取审批记录失败", "error": str(exc)}), 500


@bp.route("/api/completed-applications-history", methods=["GET"])
@login_required()
def get_completed_applications_history():
    user = g.user
    role = user.get("role")
    user_id = user.get("id")

    query = """
        SELECT
            a.id,
            a.applicant,
            a.applicant_id,
            a.deviceId,
            a.reason,
            a.status,
            a.power_off_time,
            a.power_on_time,
            a.created_at,
            a.completed_time,
            a.power_off_approver,
            a.power_off_approve_time,
            a.power_on_approver,
            a.power_on_approve_time,
            a.batch_id,
            d.device_name,
            d.power_room,
            d.cabinet,
            d.line_name,
            b.batch_name,
            COALESCE(tag_summary.active_tag_count, 0) AS active_tag_count
        FROM applications a
        LEFT JOIN devices d ON d.device_id = a.deviceId
        LEFT JOIN maintenance_batches b ON b.id = a.batch_id
        LEFT JOIN (
            SELECT device_id, COUNT(*) AS active_tag_count
            FROM device_tag_records
            WHERE tag_status = 'active'
            GROUP BY device_id
        ) tag_summary ON tag_summary.device_id = a.deviceId
        WHERE a.status = 'completed'
    """
    params = []

    if role == "electrician":
        query += " AND (a.applicant_id = %s OR a.electrician_verifier_id = %s OR a.repair_operator_id = %s)"
        params.extend([user_id, user_id, user_id])
    elif role not in ("admin", "dispatcher"):
        query += " AND a.applicant_id = %s"
        params.append(user_id)

    room_clause, room_params = user_room_filter_clause(user, "a")
    query += room_clause
    params.extend(room_params)

    application_id = (request.args.get("application_id") or "").strip()
    device_id = (request.args.get("device_id") or "").strip()
    keyword = (request.args.get("keyword") or "").strip()
    batch_id = (request.args.get("batch_id") or "").strip()
    applicant = (request.args.get("applicant") or "").strip()
    date_from = (request.args.get("date_from") or "").strip()
    date_to = (request.args.get("date_to") or "").strip()

    if application_id:
        query += " AND a.id = %s"
        params.append(application_id)
    if device_id:
        query += " AND a.deviceId LIKE %s"
        params.append(f"%{device_id}%")
    if batch_id:
        query += " AND a.batch_id = %s"
        params.append(batch_id)
    if applicant:
        query += " AND a.applicant LIKE %s"
        params.append(f"%{applicant}%")
    if keyword:
        query += """
            AND (
                a.deviceId LIKE %s
                OR COALESCE(d.device_name, '') LIKE %s
                OR COALESCE(d.power_room, '') LIKE %s
                OR COALESCE(d.cabinet, '') LIKE %s
                OR COALESCE(a.reason, '') LIKE %s
            )
        """
        like = f"%{keyword}%"
        params.extend([like, like, like, like, like])
    if date_from:
        query += " AND DATE(COALESCE(a.completed_time, a.created_at)) >= %s"
        params.append(date_from)
    if date_to:
        query += " AND DATE(COALESCE(a.completed_time, a.created_at)) <= %s"
        params.append(date_to)

    query += " ORDER BY COALESCE(a.completed_time, a.created_at) DESC, a.id DESC"

    try:
        with get_db_cursor() as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()
        return jsonify(rows), 200
    except Exception as exc:
        logger.exception("获取已完成工单历史异常")
        return jsonify({"msg": "获取已完成工单历史失败", "error": str(exc)}), 500


@bp.route("/api/export/applications", methods=["GET"])
@login_required(role="admin")
def export_applications():
    try:
        with get_db_cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    a.*,
                    u.realname AS applicant_realname,
                    d.device_name,
                    d.power_room,
                    d.cabinet
                FROM applications a
                LEFT JOIN users u ON a.applicant_id = u.id
                LEFT JOIN devices d ON d.device_id = a.deviceId
                ORDER BY a.created_at DESC
                """
            )
            applications = cursor.fetchall()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "ID",
                "申请人",
                "设备编号",
                "设备名称",
                "配电室",
                "柜号",
                "原因",
                "状态",
                "停电时间",
                "送电时间",
                "申请时间",
                "停电审批人",
                "停电审批时间",
                "停电审批意见",
                "送电审批人",
                "送电审批时间",
                "送电审批意见",
            ]
        )

        for app in applications:
            writer.writerow(
                [
                    app["id"],
                    app["applicant_realname"] or app["applicant"],
                    app["deviceId"],
                    app.get("device_name") or "",
                    app.get("power_room") or "",
                    app.get("cabinet") or "",
                    app["reason"],
                    app["status"],
                    app["power_off_time"],
                    app["power_on_time"],
                    app["created_at"].strftime("%Y-%m-%d %H:%M:%S") if app["created_at"] else "",
                    app.get("power_off_approver") or "",
                    app["power_off_approve_time"].strftime("%Y-%m-%d %H:%M:%S") if app.get("power_off_approve_time") else "",
                    app.get("power_off_approve_comment") or "",
                    app.get("power_on_approver") or "",
                    app["power_on_approve_time"].strftime("%Y-%m-%d %H:%M:%S") if app.get("power_on_approve_time") else "",
                    app.get("power_on_approve_comment") or "",
                ]
            )

        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=applications.csv"},
        )
    except Exception as exc:
        logger.exception("导出申请数据异常")
        return jsonify({"msg": "导出失败", "error": str(exc)}), 500
