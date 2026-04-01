from app.database import get_db_cursor


DEFAULT_FUNCTION_PERMISSIONS = {
    "admin": [
        "approval_center",
        "batch_approval",
        "device_monitor",
        "notifications",
        "stats",
        "user_management",
        "batch_management",
    ],
    "dispatcher": [
        "approval_center",
        "batch_approval",
        "device_monitor",
        "notifications",
    ],
    "electrician": [
        "apply",
        "repair",
        "power_on_apply",
        "device_monitor",
        "notifications",
    ],
    "user": ["apply"],
}


def ensure_user_authz_defaults(cursor, user_id, role):
    cursor.execute(
        "SELECT permission_code FROM user_function_permissions WHERE user_id = %s",
        (user_id,),
    )
    existing_codes = {row["permission_code"] for row in cursor.fetchall()}
    for code in DEFAULT_FUNCTION_PERMISSIONS.get(role, []):
        if code in existing_codes:
            continue
        cursor.execute(
            """
            INSERT INTO user_function_permissions (user_id, permission_code)
            VALUES (%s, %s)
            """,
            (user_id, code),
        )


def get_user_function_permissions(user_id):
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            SELECT permission_code
            FROM user_function_permissions
            WHERE user_id = %s
            ORDER BY permission_code ASC
            """,
            (user_id,),
        )
        return [row["permission_code"] for row in cursor.fetchall()]


def get_user_room_scopes(user_id):
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            SELECT power_room
            FROM user_room_scopes
            WHERE user_id = %s
            ORDER BY power_room ASC
            """,
            (user_id,),
        )
        return [row["power_room"] for row in cursor.fetchall()]


def set_user_function_permissions(cursor, user_id, permission_codes):
    cursor.execute("DELETE FROM user_function_permissions WHERE user_id = %s", (user_id,))
    for code in sorted(set(permission_codes)):
        cursor.execute(
            """
            INSERT INTO user_function_permissions (user_id, permission_code)
            VALUES (%s, %s)
            """,
            (user_id, code),
        )


def set_user_room_scopes(cursor, user_id, room_names):
    cursor.execute("DELETE FROM user_room_scopes WHERE user_id = %s", (user_id,))
    for room in sorted({room.strip() for room in room_names if room and room.strip()}):
        cursor.execute(
            """
            INSERT INTO user_room_scopes (user_id, power_room)
            VALUES (%s, %s)
            """,
            (user_id, room),
        )
