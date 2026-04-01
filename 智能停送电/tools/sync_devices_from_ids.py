import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.database import get_db_cursor, init_database


def load_device_ids(path: Path):
    seen = set()
    result = []
    for line in path.read_text(encoding="utf-8").splitlines():
        value = line.strip()
        if not value:
            continue
        key = value.upper()
        if key in seen:
            continue
        seen.add(key)
        result.append(value)
    return result


def load_existing_devices():
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            SELECT id, device_id, is_active, sort_order
            FROM devices
            ORDER BY sort_order ASC, id ASC
            """
        )
        return cursor.fetchall()


def sync_missing_devices(device_ids):
    existing_rows = load_existing_devices()
    existing_map = {row["device_id"].upper(): row for row in existing_rows}
    next_sort = max([int(row.get("sort_order") or 0) for row in existing_rows] or [0]) + 10

    inserts = []
    reactivations = []
    for device_id in device_ids:
        row = existing_map.get(device_id.upper())
        if not row:
            inserts.append(
                (
                    device_id,
                    device_id,
                    "待补充分组",
                    "待补充柜号",
                    "auto-import",
                    "待补充线路",
                    next_sort,
                    True,
                )
            )
            next_sort += 10
        elif not row.get("is_active"):
            reactivations.append(device_id)

    with get_db_cursor() as cursor:
        if inserts:
            cursor.executemany(
                """
                INSERT INTO devices
                (device_id, device_name, power_room, cabinet, area_code, line_name, sort_order, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                inserts,
            )
        if reactivations:
            cursor.executemany(
                "UPDATE devices SET is_active = TRUE WHERE device_id = %s",
                [(device_id,) for device_id in reactivations],
            )

    return len(inserts), len(reactivations)


def main():
    parser = argparse.ArgumentParser(description="Ensure device ids from a text file exist in devices table.")
    parser.add_argument("--devices-file", required=True, help="设备编号 txt 文件，一行一个")
    args = parser.parse_args()

    file_path = Path(args.devices_file)
    if not file_path.exists():
        raise SystemExit(f"设备文件不存在: {file_path}")

    init_database()
    device_ids = load_device_ids(file_path)
    inserted, reactivated = sync_missing_devices(device_ids)
    print(f"设备总数(去重后): {len(device_ids)}")
    print(f"新增设备: {inserted}")
    print(f"重新启用设备: {reactivated}")


if __name__ == "__main__":
    main()
