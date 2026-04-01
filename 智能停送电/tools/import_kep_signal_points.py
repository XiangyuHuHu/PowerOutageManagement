import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.database import get_db_cursor, init_database

POWER_PREFIX = "ns=2;s=洗煤厂PLC.洗煤厂设备新."


def load_device_ids(path: Path):
    lines = path.read_text(encoding="utf-8").splitlines()
    return [line.strip() for line in lines if line.strip()]


def load_active_device_map():
    with get_db_cursor() as cursor:
        cursor.execute("SELECT device_id FROM devices WHERE is_active = TRUE ORDER BY device_id ASC")
        rows = cursor.fetchall()
    return {row["device_id"].upper(): row["device_id"] for row in rows}


def build_signal_rows(device_ids):
    rows = []
    for device_id in device_ids:
        rows.append(
            {
                "device_id": device_id,
                "signal_type": "power_feedback",
                "signal_name": "带电",
                "signal_address": f"{POWER_PREFIX}{device_id}.带电",
                "data_type": "bool",
                "source_system": "kepserver",
                "source_sheet": "KepServer",
                "description": "实时带电状态，True=带电，False=不带电",
                "is_active": True,
            }
        )
        rows.append(
            {
                "device_id": device_id,
                "signal_type": "tag_count",
                "signal_name": "挂牌",
                "signal_address": f"{POWER_PREFIX}{device_id}.挂牌",
                "data_type": "int",
                "source_system": "kepserver",
                "source_sheet": "KepServer",
                "description": "实时挂牌数量",
                "is_active": True,
            }
        )
    return rows


def import_signal_rows(rows):
    sql = """
        INSERT INTO device_signal_points
        (device_id, signal_type, signal_name, signal_address, data_type, source_system, source_sheet, description, is_active)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            signal_address = VALUES(signal_address),
            data_type = VALUES(data_type),
            source_system = VALUES(source_system),
            source_sheet = VALUES(source_sheet),
            description = VALUES(description),
            is_active = VALUES(is_active)
    """
    params = [
        (
            row["device_id"],
            row["signal_type"],
            row["signal_name"],
            row["signal_address"],
            row["data_type"],
            row["source_system"],
            row["source_sheet"],
            row["description"],
            bool(row["is_active"]),
        )
        for row in rows
    ]
    with get_db_cursor() as cursor:
        cursor.executemany(sql, params)


def main():
    parser = argparse.ArgumentParser(description="Import KepServer power/tag signal points for existing active devices.")
    parser.add_argument("--devices-file", required=True, help="Path to a txt file containing one device id per line.")
    args = parser.parse_args()

    file_path = Path(args.devices_file)
    if not file_path.exists():
        raise SystemExit(f"设备文件不存在: {file_path}")

    init_database()
    raw_ids = load_device_ids(file_path)
    active_map = load_active_device_map()

    matched = []
    missing = []
    seen = set()
    for raw_id in raw_ids:
        key = raw_id.upper()
        if key in seen:
            continue
        seen.add(key)
        actual_id = active_map.get(key)
        if actual_id:
            matched.append(actual_id)
        else:
            missing.append(raw_id)

    rows = build_signal_rows(matched)
    import_signal_rows(rows)

    print(f"原始设备数: {len(raw_ids)}")
    print(f"匹配活动设备: {len(matched)}")
    print(f"导入信号点数: {len(rows)}")
    print(f"未匹配设备数: {len(missing)}")
    if missing:
        print("未匹配设备示例: " + ", ".join(missing[:20]))


if __name__ == "__main__":
    main()
