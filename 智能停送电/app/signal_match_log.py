# -*- coding: utf-8 -*-
"""设备信号导入匹配报告：写入 DEVICE_SIGNAL_MATCH_LOG.md"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from app.kep_opcua_address import classify_equipment_match, equipment_label

DEFAULT_MD = Path(__file__).resolve().parent.parent / "DEVICE_SIGNAL_MATCH_LOG.md"

AMBIGUOUS_KINDS = {"case_label", "prefix", "prefix_ci", "id_only"}
UNMATCHED_KINDS = {"unmatched", "new_device"}


def _ledger_label(dev):
    if not dev:
        return ""
    return equipment_label(dev.get("device_id") or "", dev.get("device_name") or "")


def analyze_equipment_rows(rows, devices, source_name):
    unmatched = []
    ambiguous = []
    exact_count = 0
    seen_unmatched = set()
    seen_amb = set()

    for row in rows:
        equipment = (row.get("equipment") or "").strip()
        dev, kind, note = classify_equipment_match(equipment, devices)
        if kind == "exact":
            exact_count += 1
            continue
        entry = {
            "source": source_name,
            "equipment": equipment,
            "full_tag": row.get("full_tag") or row.get("tag") or "",
            "metric": row.get("metric") or "",
            "comm_machine": row.get("comm_machine") or "",
            "matched_device_id": (dev or {}).get("device_id") or "",
            "matched_label": _ledger_label(dev),
            "kind": kind,
            "note": note,
        }
        if kind in UNMATCHED_KINDS:
            key = (source_name, equipment, kind)
            if key not in seen_unmatched:
                seen_unmatched.add(key)
                unmatched.append(entry)
        elif kind in AMBIGUOUS_KINDS:
            key = (source_name, equipment, entry["matched_device_id"], kind)
            if key not in seen_amb:
                seen_amb.add(key)
                ambiguous.append(entry)

    return {
        "source": source_name,
        "total_rows": len(rows),
        "exact_count": exact_count,
        "unmatched": unmatched,
        "ambiguous": ambiguous,
    }


def render_match_log_md(sections, device_count=None):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "# 设备信号导入匹配记录",
        "",
        f"> 自动生成于 {now}。记录 Kep/低压后台导入时**未匹配**与**待人工确认**的设备段。",
        "",
        "相关文档：[DEVICE_LEDGER_DESIGN.md](./DEVICE_LEDGER_DESIGN.md)",
        "",
    ]
    if device_count is not None:
        lines.append(f"当前台账活跃设备数：**{device_count}**")
        lines.append("")

    all_unmatched = []
    all_ambiguous = []
    for sec in sections:
        all_unmatched.extend(sec.get("unmatched") or [])
        all_ambiguous.extend(sec.get("ambiguous") or [])

    lines += [
        "## 汇总",
        "",
        "| 数据源 | 点位总数 | 完全匹配 | 待人工确认 | 未匹配 |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for sec in sections:
        u = len(sec.get("unmatched") or [])
        a = len(sec.get("ambiguous") or [])
        e = sec.get("exact_count") or 0
        t = sec.get("total_rows") or 0
        lines.append(f"| {sec['source']} | {t} | {e} | {a} | {u} |")
    lines.append(f"| **合计** | — | — | **{len(all_ambiguous)}** | **{len(all_unmatched)}** |")
    lines += ["", "---", ""]

    for sec in sections:
        lines += _render_source_section(sec)

    lines += ["---", "", "## 说明", "", _NOTES]
    return "\n".join(lines) + "\n"


_NOTES = """- **未匹配**：无法关联到 `devices` 台账，导入时该 Tag 会跳过（`--no-ensure-devices` 时 `new_device` 也算未匹配）。
- **待人工确认**：已通过前缀/大小写等方式挂到某台设备，但 CSV 设备段与台账标签不一致，请核对是否挂错设备。
- 重新生成：在项目根目录执行 `python tools/refresh_device_signal_match_log.py`。
- 导入脚本也可加 `--md-out`（默认 `DEVICE_SIGNAL_MATCH_LOG.md`）在导入后刷新本文档。"""


def _render_source_section(sec):
    source = sec["source"]
    lines = [f"## {source}", ""]

    unmatched = sec.get("unmatched") or []
    ambiguous = sec.get("ambiguous") or []

    lines += [f"### 未匹配（{len(unmatched)} 条设备段）", ""]
    if not unmatched:
        lines.append("无。")
    else:
        lines += [
            "| CSV 设备段 | 类型 | 说明 | 示例 Tag |",
            "| --- | --- | --- | --- |",
        ]
        for e in sorted(unmatched, key=lambda x: (x["kind"], x["equipment"])):
            tag = (e.get("full_tag") or "")[:80]
            lines.append(f"| {e['equipment']} | {e['kind']} | {e['note']} | {tag} |")
    lines += ["", f"### 待人工确认（{len(ambiguous)} 条设备段）", ""]
    if not ambiguous:
        lines.append("无。")
    else:
        lines += [
            "| CSV 设备段 | 挂到 device_id | 台账标签 | 匹配方式 | 说明 | 示例 Tag |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
        for e in sorted(ambiguous, key=lambda x: (x["matched_device_id"], x["equipment"])):
            tag = (e.get("full_tag") or "")[:60]
            lines.append(
                f"| {e['equipment']} | {e['matched_device_id']} | {e['matched_label']} "
                f"| {e['kind']} | {e['note']} | {tag} |"
            )
    lines.append("")
    return lines


def write_match_log_md(sections, path=None, device_count=None):
    path = Path(path or DEFAULT_MD)
    path.write_text(render_match_log_md(sections, device_count=device_count), encoding="utf-8")
    return path
