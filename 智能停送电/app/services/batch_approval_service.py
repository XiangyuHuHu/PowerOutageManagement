from app.notifications import notify_approval_result
from app.services.application_flow_service import raw_sql, transition_application
from app.services.tag_service import count_active_tags


def build_batch_approval_meta(stage, action, approver, approver_id, comment):
    new_status = (
        "approved" if stage == "power_off" and action == "approve" else
        "rejected" if stage == "power_off" else
        "completed" if action == "approve" else
        "power_on_rejected"
    )

    if stage == "power_off":
        return {
            "new_status": new_status,
            "expected_status": "pending",
            "operation_type": "power_off_approve",
            "update_fields": {
                "power_off_approver": approver,
                "power_off_approver_id": approver_id,
                "power_off_approve_time": raw_sql("NOW()"),
                "power_off_approve_comment": comment,
            },
        }

    update_fields = {
        "power_on_approver": approver,
        "power_on_approver_id": approver_id,
        "power_on_approve_time": raw_sql("NOW()"),
        "power_on_approve_comment": comment,
    }
    if new_status == "completed":
        update_fields["completed_time"] = raw_sql("NOW()")

    return {
        "new_status": new_status,
        "expected_status": "power_on_applied",
        "operation_type": "power_on_approve",
        "update_fields": update_fields,
    }


def process_batch_approval(cursor, applications, stage, action, approver, approver_id, comment):
    meta = build_batch_approval_meta(stage, action, approver, approver_id, comment)
    processed_ids = []
    skipped = []

    for app in applications:
        if stage == "power_on" and action == "approve":
            remaining_tags = count_active_tags(app["deviceId"], cursor=cursor)
            if remaining_tags > 0:
                skipped.append(
                    {
                        "id": app["id"],
                        "deviceId": app["deviceId"],
                        "reason": f"仍有 {remaining_tags} 个有效挂牌",
                    }
                )
                continue

        result = transition_application(
            cursor=cursor,
            app_id=app["id"],
            expected_status=meta["expected_status"],
            new_status=meta["new_status"],
            operator=approver,
            operator_id=approver_id,
            operation_type=meta["operation_type"],
            comment=comment,
            update_fields=meta["update_fields"],
        )
        if not result["ok"]:
            skipped.append({"id": app["id"], "deviceId": app["deviceId"], "reason": "状态已变化"})
            continue

        notify_approval_result(app["id"], app["applicant_id"], action == "approve", approver, comment)
        processed_ids.append(app["id"])

    return {
        "processed_ids": processed_ids,
        "skipped": skipped,
        "new_status": meta["new_status"],
    }
