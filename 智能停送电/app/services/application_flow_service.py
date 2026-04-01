import logging

logger = logging.getLogger(__name__)


def raw_sql(expression):
    return {"__raw_sql__": expression}


def get_application(cursor, app_id, fields=None):
    selected_fields = ", ".join(fields) if fields else "*"
    cursor.execute(f"SELECT {selected_fields} FROM applications WHERE id = %s", (app_id,))
    return cursor.fetchone()


def write_application_log(cursor, app_id, operator, operator_id, operation_type, comment, old_status, new_status):
    cursor.execute(
        """
        INSERT INTO application_logs
        (application_id, operator, operator_id, operation_type, operation_comment, old_status, new_status)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (app_id, operator, operator_id, operation_type, comment, old_status, new_status),
    )


def transition_application(
    cursor,
    app_id,
    expected_status,
    new_status,
    operator,
    operator_id,
    operation_type,
    comment="",
    update_fields=None,
):
    """
    Perform a guarded state transition and write a matching application log.

    Returns:
      dict: {"ok": bool, "application": row|None, "reason": str|None}
    """
    application = get_application(cursor, app_id)
    if not application:
        return {"ok": False, "application": None, "reason": "not_found"}
    if application["status"] != expected_status:
        return {"ok": False, "application": application, "reason": "status_mismatch"}

    updates = {"status": new_status}
    if update_fields:
        updates.update(update_fields)

    assignments = []
    params = []
    for field, value in updates.items():
        if isinstance(value, dict) and "__raw_sql__" in value:
            assignments.append(f"{field} = {value['__raw_sql__']}")
            continue
        assignments.append(f"{field} = %s")
        params.append(value)

    params.extend([app_id, expected_status])
    cursor.execute(
        f"""
        UPDATE applications
        SET {", ".join(assignments)}
        WHERE id = %s
          AND status = %s
        """,
        params,
    )

    if cursor.rowcount != 1:
        logger.warning("Application transition lost race: app_id=%s expected=%s new=%s", app_id, expected_status, new_status)
        return {"ok": False, "application": application, "reason": "status_mismatch"}

    write_application_log(cursor, app_id, operator, operator_id, operation_type, comment, expected_status, new_status)
    application["status"] = new_status
    return {"ok": True, "application": application, "reason": None}
