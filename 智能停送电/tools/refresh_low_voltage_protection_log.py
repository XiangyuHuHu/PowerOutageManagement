#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成低压后台综保数据对接情况文档 LOW_VOLTAGE_PROTECTION_INTEGRATION.md"""
import argparse
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.kep_opcua_address import (
    PROTECTION_METRIC_TO_SIGNAL,
    build_low_voltage_nodeid,
    classify_equipment_match,
    equipment_label,
    protection_metric_to_signal_type,
    resolve_equipment_to_device,
)
from tools.sync_low_voltage_protection_from_csv import (
    DEFAULT_DIR,
    DEFAULT_FILES,
    load_low_voltage_rows,
)

DEFAULT_MD = ROOT / "LOW_VOLTAGE_PROTECTION_INTEGRATION.md"
SOURCE_NAME = "低压后台综保（通讯管理机 1–4）"
RISKY_PREFIX_CI = {"prefix_ci", "case_label"}


def load_devices():
    try:
        from app.database import get_db_cursor, init_database
        init_database()
        with get_db_cursor() as cursor:
            cursor.execute("SELECT device_id, device_name FROM devices WHERE is_active = TRUE")
            return cursor.fetchall(), "database"
    except Exception as exc:
        from app.database import REAL_DEVICE_SEED
        devices = [{"device_id": r[0], "device_name": r[1]} for r in REAL_DEVICE_SEED]
        return devices, f"fallback(seed only): {exc}"


def load_lv_rows(lv_dir):
    rows = []
    per_file = {}
    for name in DEFAULT_FILES:
        path = lv_dir / name
        if not path.is_file():
            per_file[name] = 0
            continue
        batch = load_low_voltage_rows(path)
        per_file[name] = len(batch)
        rows.extend(batch)
    return rows, per_file


def analyze(rows, devices):
    unmatched_tags = []
    ambiguous = {}
    exact = prefix = 0
    per_machine = Counter()
    per_metric = Counter()
    per_device = Counter()
    per_machine_devices = defaultdict(set)
    signal_types = Counter()

    for item in rows:
        per_machine[item["comm_machine"]] += 1
        per_metric[item["metric"]] += 1
        dev, kind, note = classify_equipment_match(item["equipment"], devices)
        if kind == "exact":
            exact += 1
        else:
            prefix += 1
        if not dev or not dev.get("device_id"):
            unmatched_tags.append(item)
            continue
        did = dev["device_id"]
        per_device[did] += 1
        per_machine_devices[item["comm_machine"]].add(did)
        st = protection_metric_to_signal_type(item["metric"])
        signal_types[st] += 1
        if kind not in {"exact"}:
            key = item["equipment"]
            if key not in ambiguous:
                ambiguous[key] = {
                    "equipment": item["equipment"],
                    "matched_device_id": did,
                    "matched_label": equipment_label(did, dev.get("device_name")),
                    "kind": kind,
                    "note": note,
                    "full_tag": item["full_tag"],
                    "comm_machine": item["comm_machine"],
                    "point_count": 0,
                }
            ambiguous[key]["point_count"] += 1

    risky = [v for v in ambiguous.values() if v["kind"] in RISKY_PREFIX_CI]
    multi_target = defaultdict(list)
    for v in ambiguous.values():
        multi_target[v["equipment"][:6]].append(v)

    return {
        "exact": exact,
        "prefix": prefix,
        "unmatched_tags": unmatched_tags,
        "ambiguous": sorted(ambiguous.values(), key=lambda x: (x["kind"], x["matched_device_id"], x["equipment"])),
        "risky": sorted(risky, key=lambda x: x["equipment"]),
        "per_machine": per_machine,
        "per_metric": per_metric,
        "per_device": per_device,
        "per_machine_devices": per_machine_devices,
        "signal_types": signal_types,
        "matched_devices": len(per_device),
    }


def md_table(headers, rows):
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(c) for c in row) + " |")
    return lines


def render(rows, devices, device_source, per_file, stats, lv_dir):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total = len(rows)
    unmatched_eq = len({r["equipment"] for r in stats["unmatched_tags"]})
    amb = stats["ambiguous"]

    lines = [
        "# 低压后台综保数据对接情况",
        "",
        f"> 自动生成于 {now}。台账来源：{device_source}",
        "",
        "本文档专门记录 **低压后台四个通讯管理机 CSV** 与系统 `devices` / `device_signal_points` 的对接情况。",
        "",
        "相关文档：",
        "- [DEVICE_LEDGER_DESIGN.md](./DEVICE_LEDGER_DESIGN.md) — 台账设计",
        "- [DEVICE_SIGNAL_MATCH_LOG.md](./DEVICE_SIGNAL_MATCH_LOG.md) — 全量信号匹配汇总",
        "",
        "---",
        "",
        "## 1. 数据源",
        "",
        "| 项目 | 内容 |",
        "| --- | --- |",
        f"| 原始目录 | `{lv_dir}` |",
        "| 文件 | 通讯管理机1.csv ~ 通讯管理机4.csv |",
        "| Kep 根路径 | `低压后台.通讯管理机N` |",
        "| OPC NodeId 格式 | `ns=2;s=低压后台.通讯管理机N.{完整TagName}` |",
        "| 导入脚本 | `tools/sync_low_voltage_protection_from_csv.py` |",
        "| 刷新本文档 | `python tools/refresh_low_voltage_protection_log.py` |",
        "",
        "**NodeId 示例**",
        "",
        "```",
        build_low_voltage_nodeid("通讯管理机3", "127F带式给煤机风扇电机.A相电流"),
        build_low_voltage_nodeid("通讯管理机1", "11JX1原煤储煤场上检修电源.A相电流"),
        "```",
        "",
        "---",
        "",
        "## 2. 导入规模",
        "",
    ]
    lines += md_table(
        ["通讯管理机", "CSV 点位数", "关联设备数"],
        [
            (m, per_file.get(m, 0), len(stats["per_machine_devices"].get(m.replace(".csv", ""), set())))
            for m in DEFAULT_FILES
        ]
        + [("**合计**", total, stats["matched_devices"])],
    )
    lines += [
        "",
        f"- 台账活跃设备数（用于匹配）：**{len(devices)}**",
        f"- 完全标签匹配点位：**{stats['exact']}**",
        f"- 前缀/模糊匹配点位：**{stats['prefix']}**",
        f"- 未匹配 Tag 数：**{len(stats['unmatched_tags'])}**（涉及 **{unmatched_eq}** 个设备段）",
        f"- 待人工确认设备段：**{len(amb)}**",
        "",
        "---",
        "",
        "## 3. 测点类型映射",
        "",
        "CSV Tag 最后一段（测点名）映射为内部 `signal_type`，用于设备详情「综保监测」展示与 OPC 采集。",
        "",
    ]
    lines += md_table(
        ["CSV 测点名", "signal_type", "说明"],
        [(k, v, "已内置映射" if k in PROTECTION_METRIC_TO_SIGNAL else "哈希兜底") for k, v in sorted(PROTECTION_METRIC_TO_SIGNAL.items())],
    )
    lines += ["", "### 3.1 本次 CSV 实际出现的测点", ""]
    lines += md_table(
        ["测点名", "出现次数"],
        stats["per_metric"].most_common(30),
    )
    if len(stats["per_metric"]) > 30:
        lines.append(f"\n其余 {len(stats['per_metric']) - 30} 种测点略。")
    lines += [
        "",
        "---",
        "",
        "## 4. 设备匹配规则",
        "",
        "导入时按以下顺序将 CSV 设备段关联到 `devices`：",
        "",
        "1. **标签完全一致** — CSV 设备段 = `device_id`+`device_name` 组合标签",
        "2. **标签大小写不同** — 如 `128F` vs `128f`",
        "3. **最长 device_id 前缀** — 如 `127F带式给煤机风扇电机` → `127F`",
        "4. **忽略大小写前缀** — 如 `111aL...` → `111AL`",
        "5. **仅 device_id 相同** — 名称不同但编号一致",
        "6. **台账无则新建** — `power_room=低压后台`，`cabinet=通讯管理机N`（可用 `--no-ensure-devices` 关闭）",
        "",
        "---",
        "",
        "## 5. 未匹配清单",
        "",
    ]
    if not stats["unmatched_tags"]:
        lines.append("当前 **无未匹配 Tag**，所有点位均已关联到设备。")
    else:
        lines += md_table(
            ["通讯管理机", "设备段", "完整 Tag"],
            [(r["comm_machine"], r["equipment"], r["full_tag"][:70]) for r in stats["unmatched_tags"][:100]],
        )
    prefix_amb = [a for a in amb if a["kind"] not in {"new_device"}]
    new_dev_amb = [a for a in amb if a["kind"] == "new_device"]

    lines += [
        "",
        "---",
        "",
        "## 6. 待人工确认",
        "",
        "### 6.1 台账缺失（导入时会自动新建设备）",
        "",
        f"共 **{len(new_dev_amb)}** 个设备段在种子台账中不存在；正式导入时脚本会写入 `devices`（`power_room=低压后台`）。请核对是否应合并到已有设备而非新建。",
        "",
    ]
    if not new_dev_amb:
        lines.append("无。")
    else:
        lines += md_table(
            ["CSV 设备段", "将建 device_id", "点位数", "通讯管理机", "示例 Tag"],
            [(a["equipment"], a["matched_device_id"], a["point_count"], a["comm_machine"], a["full_tag"][:50]) for a in new_dev_amb],
        )

    lines += [
        "",
        "### 6.2 前缀歧义（已挂到已有设备，名称不一致）",
        "",
        f"共 **{len(prefix_amb)}** 个设备段通过前缀等方式挂到已有台账，**最可能挂错**，请优先核对。",
        "",
    ]
    if not prefix_amb:
        lines.append("无。")
    else:
        lines += md_table(
            ["CSV 设备段", "挂到 device_id", "台账标签", "匹配方式", "点位数", "示例 Tag"],
            [
                (a["equipment"], a["matched_device_id"], a["matched_label"], a["kind"], a["point_count"], a["full_tag"][:55])
                for a in prefix_amb
            ],
        )
    lines += [
        "",
        "### 6.3 高风险项（大小写/前缀歧义）",
        "",
        "这类匹配最容易挂错子设备，建议优先核对：",
        "",
    ]
    if stats["risky"]:
        lines += md_table(
            ["CSV 设备段", "实际挂到", "台账标签", "方式", "示例"],
            [
                (r["equipment"], r["matched_device_id"], r["matched_label"], r["kind"], r["full_tag"][:50])
                for r in stats["risky"]
            ],
        )
    else:
        lines.append("无。")

    # highlight known bad cases
    parent_ids = {"127", "128", "129", "130", "131", "132"}
    bad_cases = [
        a for a in prefix_amb
        if re.match(r"^1(27|28|29|30|31|32)F", a["equipment"], re.I)
        and (a["matched_device_id"] or "").lower() in parent_ids
    ]
    lines += [
        "",
        "### 6.4 疑似挂错父设备（F 子机挂到主编号）",
        "",
    ]
    if bad_cases:
        lines.append("CSV 设备名含 `128F`/`129F` 等子机编号，但可能挂到了 `128`/`129` 主设备，需重点核对：")
        lines += [""]
        lines += md_table(
            ["CSV 设备段", "当前挂到", "建议核对"],
            [(b["equipment"], b["matched_device_id"], f"是否应为 {b['equipment'][:4]} 而非 {b['matched_device_id']}") for b in bad_cases],
        )
    else:
        lines.append("未发现此类项。")

    lines += [
        "",
        "---",
        "",
        "## 7. 已对接设备（按点位数 Top 20）",
        "",
    ]
    top_devices = stats["per_device"].most_common(20)
    id_to_name = {d["device_id"]: d.get("device_name") for d in devices}
    lines += md_table(
        ["device_id", "device_name", "综保点位数"],
        [(did, id_to_name.get(did, ""), cnt) for did, cnt in top_devices],
    )
    lines += [
        "",
        "---",
        "",
        "## 8. 系统展示与采集",
        "",
        "| 环节 | 说明 |",
        "| --- | --- |",
        "| 数据表 | `device_signal_points`，`source_system=kepserver`，`source_sheet=通讯管理机N` |",
        "| 设备详情 | `device_monitor.html` → 抽屉「综保监测」「综保详细点位」 |",
        "| OPC 采集 | `app/opcua_client.py` 轮询 `signal_address LIKE 'ns=%'` 的点位 |",
        "| 历史记录 | 状态变化写入 `device_event_history` |",
        "",
        "**注意**：现场 KepServer 若超时，详情页会显示点位配置但实时值为「未上报」。",
        "",
        "---",
        "",
        "## 9. 运维命令",
        "",
        "```powershell",
        "cd 智能停送电",
        "$env:DB_HOST='127.0.0.1'; $env:DB_PORT='3307'",
        "",
        "# 重新导入（默认读四个 CSV）",
        "python tools/sync_low_voltage_protection_from_csv.py",
        "",
        "# 仅预览",
        "python tools/sync_low_voltage_protection_from_csv.py --dry-run",
        "",
        "# 刷新本文档",
        "python tools/refresh_low_voltage_protection_log.py",
        "```",
        "",
    ]
    return "\n".join(lines) + "\n"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--lv-dir", default=str(DEFAULT_DIR))
    p.add_argument("--md-out", default=str(DEFAULT_MD))
    args = p.parse_args()

    lv_dir = Path(args.lv_dir)
    rows, per_file = load_lv_rows(lv_dir)
    if not rows:
        print("no csv rows")
        return 1

    devices, source = load_devices()
    stats = analyze(rows, devices)
    md = render(rows, devices, source, per_file, stats, lv_dir)
    out = Path(args.md_out)
    out.write_text(md, encoding="utf-8")
    print("written", out)
    print("rows", len(rows), "devices", stats["matched_devices"], "ambiguous", len(stats["ambiguous"]), "unmatched", len(stats["unmatched_tags"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
