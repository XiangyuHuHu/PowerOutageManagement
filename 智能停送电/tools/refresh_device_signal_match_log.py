#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""扫描 0601 XLSX 与低压后台 CSV，生成 DEVICE_SIGNAL_MATCH_LOG.md。"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.database import get_db_cursor, init_database
from app.signal_match_log import DEFAULT_MD, analyze_equipment_rows, write_match_log_md
from tools.sync_kep_signal_points_from_csv import collect_tag_items
from tools.sync_low_voltage_protection_from_csv import DEFAULT_DIR, DEFAULT_FILES, load_low_voltage_rows

DEFAULT_XLSX = Path(r"d:\金海泽地\金正泰\洗煤厂设备新0601.xlsx")


def _devices_from_seed():
    from app.database import REAL_DEVICE_SEED
    from app.kep_opcua_address import parse_equipment_parts

    devices = [{"device_id": r[0], "device_name": r[1]} for r in REAL_DEVICE_SEED]
    known = {(d["device_id"] or "").lower() for d in devices}
    return devices, known


def _merge_equipment(devices, known, equipment):
    from app.kep_opcua_address import parse_equipment_parts

    did, dname = parse_equipment_parts(equipment)
    if not did or did.lower() in known:
        return
    devices.append({"device_id": did, "device_name": dname or did})
    known.add(did.lower())


def load_devices(use_seed=False, extra_equipment=None):
    if use_seed:
        devices, known = _devices_from_seed()
        for eq in extra_equipment or []:
            _merge_equipment(devices, known, eq)
        return devices
    try:
        init_database()
        with get_db_cursor() as cursor:
            cursor.execute("SELECT device_id, device_name FROM devices WHERE is_active = TRUE")
            return cursor.fetchall()
    except Exception as exc:
        print("DB unavailable, fallback to seed + tag equipment:", exc)
        devices, known = _devices_from_seed()
        for eq in extra_equipment or []:
            _merge_equipment(devices, known, eq)
        return devices


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--xlsx", type=str, default=str(DEFAULT_XLSX))
    p.add_argument("--lv-dir", type=str, default=str(DEFAULT_DIR))
    p.add_argument("--md-out", type=str, default=str(DEFAULT_MD))
    p.add_argument("--use-seed", action="store_true")
    args = p.parse_args()

    xlsx = Path(args.xlsx)
    tag_items = collect_tag_items(xlsx) if xlsx.is_file() else []
    lv_dir = Path(args.lv_dir)
    lv_rows = []
    for name in DEFAULT_FILES:
        path = lv_dir / name
        if path.is_file():
            batch = load_low_voltage_rows(path)
            lv_rows.extend(batch)
            print(path.name, len(batch))
        else:
            print("skip", path)

    extra_eq = [i["equipment"] for i in tag_items] + [i["equipment"] for i in lv_rows]
    devices = load_devices(use_seed=args.use_seed, extra_equipment=extra_eq)
    sections = []

    if tag_items:
        rows = [{"equipment": i["equipment"], "full_tag": i["full_tag"]} for i in tag_items]
        sections.append(analyze_equipment_rows(rows, devices, "洗煤厂设备新0601（Kep 状态量）"))
        print("0601:", len(rows))
    else:
        print("skip 0601:", xlsx)

    if lv_rows:
        sections.append(analyze_equipment_rows(lv_rows, devices, "低压后台综保（通讯管理机 1–4）"))

    if not sections:
        print("no data")
        return 1

    out = write_match_log_md(sections, path=args.md_out, device_count=len(devices))
    print("written:", out)
    for sec in sections:
        print(sec["source"], "unmatched", len(sec.get("unmatched") or []), "ambiguous", len(sec.get("ambiguous") or []))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
