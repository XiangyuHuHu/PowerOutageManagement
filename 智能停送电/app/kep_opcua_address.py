"""KepServer OPC UA NodeId helpers (洗煤厂设备新0601 Tag Name)."""
from __future__ import annotations

import hashlib
import os
import re

KEP_ITEM_PREFIX = "洗煤厂PLC.洗煤厂设备新"
LOW_VOLTAGE_ROOT = "低压后台"
OPCUA_NAMESPACE = int(os.environ.get("OPCUA_NS", "2"))
# Excel Tag Name 后缀 -> 内部 signal_type（与洗煤厂设备新0601.xlsx 一致）
TAG_SUFFIX_TO_SIGNAL = {
    "带电": "power_feedback",
    "挂牌": "tag_count",
    "过热": "overheat",
    "急停": "emergency_stop",
    "漏电": "leakage",
    "运行": "run_status",
    "电源": "power_supply",
    "综保故障": "protection_fault",
}

SIGNAL_SUFFIX = {signal_type: suffix for suffix, signal_type in TAG_SUFFIX_TO_SIGNAL.items()}

# 当前 CSV/综保点位：全部参与 OPC 采集（后续接入更多综保模拟量时扩展 TAG_SUFFIX_TO_SIGNAL 即可）
MONITORED_SIGNAL_TYPES = frozenset(TAG_SUFFIX_TO_SIGNAL.values())

FAULT_SIGNAL_TYPES = frozenset(
    {"protection_fault", "emergency_stop", "leakage", "overheat"}
)

SIGNAL_TYPE_LABELS = {
    "power_feedback": "带电反馈",
    "tag_count": "挂牌数量",
    "overheat": "过热",
    "emergency_stop": "急停",
    "leakage": "漏电",
    "run_status": "运行状态",
    "power_supply": "电源",
    "protection_fault": "综保故障",
    "remote_local": "远程/就地",
    "trip_feedback": "分闸反馈",
    "close_feedback": "合闸反馈",
    "fault_feedback": "故障反馈",
    "remote_switch_binding": "远程分合闸绑定",
}

# 综保模拟量测点 -> 内部 signal_type（同设备内唯一）
PROTECTION_METRIC_TO_SIGNAL = {
    "A相电流": "ia",
    "B相电流": "ib",
    "C相电流": "ic",
    "Ab线电压": "u_ab",
    "Bc线电压": "u_bc",
    "Ca线电压": "u_ca",
    "AB线电压": "u_ab",
    "BC线电压": "u_bc",
    "CA线电压": "u_ca",
    "总有功功率": "p_active",
    "总无功功率": "q_reactive",
    "总视在功率": "s_apparent",
    "总功率因数": "pf",
    "功率因数": "pf",
    "正向有功电能示值": "energy_kwh",
    "反向有功电能示值": "energy_kwh_rev",
    "系统频率F": "freq",
    "I0低压侧": "i0_low",
    "I0高压侧": "i0_high",
    "漏电流": "leakage_a",
    "合位置": "breaker_close",
    "分位置": "breaker_open",
}

STATUS_SIGNAL_TYPES = frozenset(TAG_SUFFIX_TO_SIGNAL.values())
PROTECTION_SIGNAL_TYPES = frozenset(PROTECTION_METRIC_TO_SIGNAL.values())


def equipment_label(device_id, device_name):
    did = (device_id or "").strip()
    dname = (device_name or "").strip()
    if not did and not dname:
        return ""
    if not dname:
        return did
    if not did:
        return dname
    if dname.startswith(did) or did in dname:
        return dname
    return f"{did}{dname}"


def build_tag_name(device_id, device_name, signal_type):
    suffix = SIGNAL_SUFFIX.get(signal_type)
    if not suffix:
        return None
    label = equipment_label(device_id, device_name)
    if not label:
        return None
    return f"{label}.{suffix}"


def build_nodeid(tag_name, namespace=None, item_prefix=None):
    ns = OPCUA_NAMESPACE if namespace is None else namespace
    tag = (tag_name or "").strip()
    if not tag:
        raise ValueError("tag_name empty")
    if tag.startswith("ns="):
        return tag
    prefix = item_prefix or KEP_ITEM_PREFIX
    return f"ns={ns};s={prefix}.{tag}"


def build_low_voltage_nodeid(comm_machine, full_tag, namespace=None):
    """低压后台 NodeId：ns=2;s=低压后台.通讯管理机N.{设备}.{测点}"""
    machine = (comm_machine or "").strip()
    tag = (full_tag or "").strip()
    if not machine or not tag:
        raise ValueError("comm_machine or full_tag empty")
    prefix = f"{LOW_VOLTAGE_ROOT}.{machine}"
    return build_nodeid(tag, namespace=namespace, item_prefix=prefix)


def parse_low_voltage_tag(tag_name):
    raw = (tag_name or "").strip()
    if not raw or "." not in raw or raw.isdigit():
        return None
    equipment, metric = raw.rsplit(".", 1)
    equipment, metric = equipment.strip(), metric.strip()
    if not equipment or not metric:
        return None
    return equipment, metric


def protection_metric_to_signal_type(metric_name):
    metric = (metric_name or "").strip()
    if not metric:
        return "prot_unknown"
    if metric in PROTECTION_METRIC_TO_SIGNAL:
        return PROTECTION_METRIC_TO_SIGNAL[metric]
    if metric in TAG_SUFFIX_TO_SIGNAL:
        return TAG_SUFFIX_TO_SIGNAL[metric]
    if re.match(r"^DI\d+$", metric, re.I):
        return f"di_{metric[2:].lower()}"
    if metric.startswith("报警"):
        tail = metric[2:] or "x"
        return f"alarm_{tail}"
    digest = hashlib.md5(metric.encode("utf-8")).hexdigest()[:10]
    return f"prot_{digest}"


# CSV/台账 device_id 大小写别名（仅明确等价的编号，111aL 与 111AL 不互通）
DEVICE_ID_ALIASES = {
    "127F": "127f",
    "128F": "128f",
    "129F": "129f",
    "130F": "130f",
    "131F": "131f",
    "132F": "132f",
    "902F": "902f",
    "903F": "903f",
}


def _find_device_by_id(devices, device_id):
    target = (device_id or "").strip()
    if not target:
        return None
    for row in devices:
        if (row.get("device_id") or "").strip() == target:
            return row
    alias = DEVICE_ID_ALIASES.get(target) or DEVICE_ID_ALIASES.get(target.upper())
    if alias:
        for row in devices:
            if (row.get("device_id") or "").strip() == alias:
                return row
    return None


def _shorter_prefix_blocked(parsed_id, candidate_did):
    """解析出的 device_id 更长时，禁止用短编号前缀抢匹配（如 128 抢 128F）。"""
    pid = (parsed_id or "").strip()
    cid = (candidate_did or "").strip()
    if not pid or not cid or len(pid) <= len(cid):
        return False
    return pid.lower().startswith(cid.lower())


def _match_equipment(equipment, devices):
    eq = (equipment or "").strip()
    if not eq:
        return None, "unmatched", "空设备名"

    by_label = {equipment_label(r["device_id"], r["device_name"]): r for r in devices}
    by_label_ci = {k.lower(): v for k, v in by_label.items()}
    if eq in by_label:
        return by_label[eq], "exact", "标签完全一致"

    parsed_id, parsed_name = parse_equipment_parts(eq)
    dev = _find_device_by_id(devices, parsed_id)
    if dev:
        return dev, "id_only", f"解析 device_id 匹配 {parsed_id}"

    if eq.lower() in by_label_ci:
        return by_label_ci[eq.lower()], "case_label", "标签仅大小写不同"

    by_id_sorted = sorted(devices, key=lambda r: len(r["device_id"] or ""), reverse=True)
    for row in by_id_sorted:
        did = (row.get("device_id") or "").strip()
        if not did or not eq.startswith(did):
            continue
        if parsed_id and _shorter_prefix_blocked(parsed_id, did):
            continue
        return row, "prefix", f"前缀匹配 {did}"
    for row in by_id_sorted:
        did = (row.get("device_id") or "").strip()
        if not did or not eq.lower().startswith(did.lower()):
            continue
        if parsed_id and _shorter_prefix_blocked(parsed_id, did):
            continue
        return row, "prefix_ci", f"前缀匹配(忽略大小写) {did}"

    if parsed_id:
        return (
            {"device_id": parsed_id, "device_name": parsed_name or parsed_id},
            "new_device",
            "台账无此设备，需新建或补别名",
        )
    return None, "unmatched", "无法解析设备段"


def classify_equipment_match(equipment, devices):
    """返回 (device_dict|None, match_kind, note)。kind: exact|case_label|prefix|prefix_ci|id_only|new_device|unmatched"""
    return _match_equipment(equipment, devices)


def resolve_equipment_to_device(equipment, devices):
    """将综保 CSV 设备段匹配到已有 devices 台账（解析 device_id 优先于短前缀）。"""
    dev, kind, _ = _match_equipment(equipment, devices)
    if kind == "unmatched":
        return None
    return dev


def is_low_voltage_nodeid(nodeid):
    raw = (nodeid or "").strip()
    return f"{LOW_VOLTAGE_ROOT}." in raw


def parse_equipment_parts(equipment):
    """从 Kep Tag 设备段解析 device_id 与 device_name，例如 111AL风扇电机。"""
    raw = (equipment or "").strip()
    if not raw:
        return "", ""
    match = re.match(r"^([0-9A-Za-z][0-9A-Za-z\-_.]*)(.*)$", raw)
    if match:
        device_id = match.group(1)
        device_name = (match.group(2) or "").strip() or device_id
        return device_id, device_name
    return raw, raw


def parse_tag_name(tag_name):
    raw = (tag_name or "").strip()
    if not raw or "." not in raw:
        return None
    equipment, suffix = raw.rsplit(".", 1)
    equipment, suffix = equipment.strip(), suffix.strip()
    if suffix not in TAG_SUFFIX_TO_SIGNAL:
        return None
    return equipment, suffix


def _extract_tag_from_nodeid(nodeid):
    raw = (nodeid or "").strip()
    prefix = f"ns={OPCUA_NAMESPACE};s={KEP_ITEM_PREFIX}."
    if raw.startswith(prefix):
        return raw[len(prefix) :]
    if raw.startswith(f"{KEP_ITEM_PREFIX}."):
        return raw[len(KEP_ITEM_PREFIX) + 1 :]
    return None


def normalize_signal_address(device_id, device_name, signal_type, stored_address=None):
    raw = (stored_address or "").strip()
    if raw.startswith("ns=") and is_low_voltage_nodeid(raw):
        return raw
    expected_tag = build_tag_name(device_id, device_name, signal_type)
    if not expected_tag:
        return raw or None
    if raw:
        tag_part = _extract_tag_from_nodeid(raw) or raw
        if tag_part and not tag_part.startswith("ns="):
            parsed = parse_tag_name(tag_part)
            if parsed and TAG_SUFFIX_TO_SIGNAL.get(parsed[1]) == signal_type:
                expected_equipment = equipment_label(device_id, device_name)
                if parsed[0] == expected_equipment:
                    return build_nodeid(tag_part)
                return build_nodeid(expected_tag)
            suffix_pattern = "|".join(re.escape(item) for item in TAG_SUFFIX_TO_SIGNAL.keys())
            if re.match(rf"^[^.]+\.({suffix_pattern})$", tag_part):
                return build_nodeid(expected_tag)
    return build_nodeid(expected_tag)
