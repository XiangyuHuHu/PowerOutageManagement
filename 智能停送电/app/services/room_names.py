"""
系统图 / 配电室名称与设备监控页一致：台账里可能出现的别名映射到规范名，便于分组与批量审批。
"""

# 与 web_pages/device_monitor.html 中 ROOM_LABEL_MAP 保持一致
ROOM_LABEL_MAP = {
    "产品仓660V系统图": "主厂房660V系统图四",
    "选煤厂二号配电室": "选煤厂660V系统图",
}


def canonicalize_power_room(name: str | None) -> str:
    """将台账中的 power_room 转为卡片展示用的规范系统图名。"""
    if not name:
        return ""
    n = str(name).strip()
    return ROOM_LABEL_MAP.get(n, n)


def db_values_for_room_group(canonical_or_raw: str) -> list[str]:
    """
    批量审批等场景：某张系统图卡片可能对应多条不同的台账字符串
    （例如「主厂房660V系统图四」与「产品仓660V系统图」应一并处理）。
    返回用于 SQL IN (...) 的去重列表。
    """
    if not canonical_or_raw:
        return []
    key = str(canonical_or_raw).strip()
    if not key:
        return []
    aliases = [k for k, v in ROOM_LABEL_MAP.items() if v == key]
    out = [key] + aliases
    seen: set[str] = set()
    return [x for x in out if not (x in seen or seen.add(x))]
