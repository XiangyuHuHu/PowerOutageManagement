import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.database import get_db_cursor, init_database


def load_rows(path: Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        return [data]
    return data


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
    params = []
    for row in rows:
        params.append(
            (
                row.get("device_id"),
                row.get("signal_type"),
                row.get("signal_name"),
                row.get("signal_address"),
                row.get("data_type") or "bool",
                row.get("source_system") or "plc",
                row.get("source_sheet"),
                row.get("description"),
                bool(row.get("is_active", True)),
            )
        )

    with get_db_cursor() as cursor:
        cursor.executemany(sql, params)


def main():
    parser = argparse.ArgumentParser(description="Import normalized signal point seed data into device_signal_points.")
    parser.add_argument(
        "--input",
        default=str(Path(__file__).resolve().parents[1] / "data" / "signal_points_seed.json"),
        help="Path to the normalized signal points JSON file.",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")

    init_database()
    rows = load_rows(input_path)
    import_signal_rows(rows)
    print(f"Imported {len(rows)} signal rows from {input_path}")


if __name__ == "__main__":
    main()
