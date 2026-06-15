"""统一把时间戳规范为 ISO 本地时间字符串，避免前端把秒级 Unix 时间当成毫秒解析成 1970 年。"""
from datetime import datetime, timezone


def normalize_timestamp_to_iso(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        dt = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        return dt.astimezone().isoformat(timespec="seconds")
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        if text.isdigit():
            return normalize_timestamp_to_iso(int(text))
        try:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone().isoformat(timespec="seconds")
        except ValueError:
            return text
    try:
        num = float(value)
    except (TypeError, ValueError):
        return None
    if num <= 0:
        return None
    seconds = num / 1000.0 if num >= 1e12 else num
    try:
        return datetime.fromtimestamp(seconds).isoformat(timespec="seconds")
    except (OSError, OverflowError, ValueError):
        return None
