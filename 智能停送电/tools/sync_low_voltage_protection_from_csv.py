#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse, csv, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from app.database import get_db_cursor, init_database
from app.kep_opcua_address import (
    build_low_voltage_nodeid, parse_equipment_parts, parse_low_voltage_tag,
    protection_metric_to_signal_type, resolve_equipment_to_device,
)
DEFAULT_DIR = Path(r"d:\\金海泽地\\金正泰\\数据\\低压后台数据")
DEFAULT_FILES = ["通讯管理机1.csv", "通讯管理机2.csv", "通讯管理机3.csv", "通讯管理机4.csv"]

def map_data_type(raw):
    text = (raw or "").strip().lower()
    if text == "boolean": return "bool"
    if text in {"short","int","integer","word","ushort"}: return "int"
    if text in {"float","double","real"}: return "float"
    return "string"

def comm_machine_from_path(path):
    name = path.stem.strip()
    return name if name.startswith("通讯管理机") else None

def load_low_voltage_rows(path):
    machine = comm_machine_from_path(path)
    if not machine: raise ValueError(path)
    for enc in ("utf-8-sig","gbk","gb18030"):
        try:
            rows = []
            with path.open(encoding=enc, newline="") as f:
                reader = csv.DictReader(f)
                col = reader.fieldnames[0] if reader.fieldnames else "Tag Name"
                for row in reader:
                    full_tag = (row.get(col) or row.get("Tag Name") or "").strip().strip('"')
                    parsed = parse_low_voltage_tag(full_tag)
                    if not parsed: continue
                    equipment, metric = parsed
                    rows.append({"comm_machine":machine,"equipment":equipment,"metric":metric,"full_tag":full_tag,
                        "plc_address":(row.get("Address") or "").strip(),"data_type":map_data_type(row.get("Data Type")),
                        "description":(row.get("Description") or "").strip() or full_tag})
            return rows
        except UnicodeDecodeError: continue
    raise RuntimeError(path)

def ensure_devices(rows, devices):
    created = 0
    known = {(d.get("device_id") or "").lower() for d in devices}
    with get_db_cursor() as cursor:
        for item in rows:
            if resolve_equipment_to_device(item["equipment"], devices): continue
            did, dname = parse_equipment_parts(item["equipment"])
            if not did or did.lower() in known: continue
            cursor.execute("INSERT INTO devices (device_id,device_name,power_room,cabinet,area_code,line_name,sort_order,is_active) VALUES (%s,%s,'低压后台',%s,'lv-protection','',9100,TRUE) ON DUPLICATE KEY UPDATE device_name=IF(device_name IS NULL OR device_name='',VALUES(device_name),device_name), is_active=TRUE", (did,dname or did,item["comm_machine"]))
            if cursor.rowcount == 1: created += 1
            known.add(did.lower()); devices.append({"device_id":did,"device_name":dname or did})
    return created

def upsert_rows(db_rows):
    sql = "INSERT INTO device_signal_points (device_id,signal_type,signal_name,signal_address,data_type,source_system,source_sheet,description,is_active) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,TRUE) ON DUPLICATE KEY UPDATE signal_address=VALUES(signal_address),data_type=VALUES(data_type),source_system=VALUES(source_system),source_sheet=VALUES(source_sheet),description=VALUES(description),is_active=TRUE"
    with get_db_cursor() as cursor: cursor.executemany(sql, db_rows)

def collect_sources(paths):
    items = []
    for path in paths:
        if not path.is_file(): print("skip", path); continue
        batch = load_low_voltage_rows(path); print(path.name, len(batch)); items.extend(batch)
    return items

def main():
    p = argparse.ArgumentParser()
    p.add_argument("sources", nargs="*")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--no-ensure-devices", action="store_true")
    p.add_argument("--sql-out", type=str)
    p.add_argument("--md-out", nargs="?", const=str(ROOT / "DEVICE_SIGNAL_MATCH_LOG.md"), default=None)
    args = p.parse_args()
    paths = []
    if args.sources:
        for src in args.sources:
            path = Path(src)
            paths.extend(sorted(path.glob("通讯管理机*.csv"))) if path.is_dir() else paths.append(path)
    else:
        paths = [DEFAULT_DIR/n for n in DEFAULT_FILES]
    tag_items = collect_sources(paths)
    if not tag_items: return 1
    if args.sql_out:
        from app.database import REAL_DEVICE_SEED
        devices = [{"device_id":r[0],"device_name":r[1]} for r in REAL_DEVICE_SEED]
    else:
        init_database()
        with get_db_cursor() as c: c.execute("SELECT device_id, device_name FROM devices WHERE is_active=TRUE"); devices = c.fetchall()
        if not args.no_ensure_devices: print("new devices", ensure_devices(tag_items, devices))
    db_rows, missing, seen = [], [], set()
    for item in tag_items:
        dev = resolve_equipment_to_device(item["equipment"], devices)
        if not dev or not dev.get("device_id"): missing.append(item["full_tag"]); continue
        st = protection_metric_to_signal_type(item["metric"])
        key = (dev["device_id"], st, item["metric"])
        if key in seen: continue
        seen.add(key)
        desc = item["description"] + (f" | Modbus:{item['plc_address']}" if item["plc_address"] else "")
        db_rows.append((dev["device_id"], st, item["metric"], build_low_voltage_nodeid(item["comm_machine"], item["full_tag"]), item["data_type"], "kepserver", item["comm_machine"], desc[:255]))
    print("points", len(seen), "devices", len({r[0] for r in db_rows}), "rows", len(db_rows), "missing", len(missing))
    if args.dry_run:
        [print("ex", r) for r in db_rows[:5]]; return 0
    if args.sql_out:
        esc=lambda s:(s or "").replace("\\","\\\\").replace("'","''"); lines=["SET NAMES utf8mb4;"]
        for device_id,st,name,nodeid,dtype,src,sheet,desc in db_rows:
            lines.append(f"INSERT INTO device_signal_points (device_id,signal_type,signal_name,signal_address,data_type,source_system,source_sheet,description,is_active) VALUES ('{esc(device_id)}','{esc(st)}','{esc(name)}','{esc(nodeid)}','{esc(dtype)}','{esc(src)}','{esc(sheet)}','{esc(desc)}',TRUE) ON DUPLICATE KEY UPDATE signal_address=VALUES(signal_address),data_type=VALUES(data_type),source_system=VALUES(source_system),source_sheet=VALUES(source_sheet),description=VALUES(description),is_active=TRUE;")
        Path(args.sql_out).write_text("\\n".join(lines)+"\\n", encoding="utf-8"); return 0
    upsert_rows(db_rows); print("done")
    from tools.refresh_low_voltage_protection_log import main as refresh_lv_log
    refresh_lv_log()
    if args.md_out:
        import sys
        from tools.refresh_device_signal_match_log import main as refresh_log
        argv_save = sys.argv
        sys.argv = ["refresh_device_signal_match_log", "--md-out", args.md_out]
        try:
            refresh_log()
        finally:
            sys.argv = argv_save
    return 0

if __name__ == "__main__": raise SystemExit(main())
