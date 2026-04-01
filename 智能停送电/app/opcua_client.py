import logging
import os
import threading
import time
from contextlib import contextmanager

from app.database import get_db_cursor

logger = logging.getLogger(__name__)

_opcua_thread = None
_stop_event = threading.Event()
_opcua_write_lock = threading.Lock()
_KEP_NODE_PREFIX = "洗煤厂PLC.洗煤厂设备新"


class _OpcuaSubscriptionHandler:
    """Subscription-first status collector with polling fallback."""

    def __init__(self, client, plan, process_device_message):
        self.client = client
        self.plan = plan
        self.process_device_message = process_device_message
        self._lock = threading.Lock()
        self._state = {}
        self._node_map = {}
        self._subscription = None

    def build_subscription(self, interval_ms):
        for item in self.plan:
            state = {
                "power_feedback": None,
                "tag_count": None,
                "timestamps": {},
                "errors": [],
            }
            self._state[item["device_id"]] = state

            if item.get("power_feedback_nodeid"):
                self._node_map[item["power_feedback_nodeid"]] = (item, "power_feedback")
            if item.get("tag_count_nodeid"):
                self._node_map[item["tag_count_nodeid"]] = (item, "tag_count")

        if not self._node_map:
            return None

        self._subscription = self.client.create_subscription(interval_ms, self)
        for nodeid in self._node_map:
            try:
                self._subscription.subscribe_data_change(self.client.get_node(nodeid))
            except Exception:
                logger.exception("OPC UA subscribe failed for node %s", nodeid)
        logger.info("OPC UA subscription created: %s monitored nodes", len(self._node_map))
        return self._subscription

    def delete_subscription(self):
        if not self._subscription:
            return
        try:
            self._subscription.delete()
        except Exception:
            pass
        self._subscription = None

    def datachange_notification(self, node, val, data):
        nodeid = node.nodeid.to_string()
        mapping = self._node_map.get(nodeid)
        if not mapping:
            return

        item, signal_type = mapping
        ts = None
        try:
            ts = data.monitored_item.Value.SourceTimestamp or data.monitored_item.Value.ServerTimestamp
        except Exception:
            ts = None

        with self._lock:
            state = self._state.setdefault(
                item["device_id"],
                {"power_feedback": None, "tag_count": None, "timestamps": {}, "errors": []},
            )
            if signal_type == "power_feedback":
                state["power_feedback"] = bool(val) if val is not None else None
            elif signal_type == "tag_count":
                state["tag_count"] = _safe_int(val, 0)

            state["timestamps"][signal_type] = str(ts) if ts else None
            state["errors"] = []

            payload = _build_payload_from_state(item, state, online=True)

        self.process_device_message(payload, topic=f"devices/{item['device_id']}/status")

    def event_notification(self, event):
        return None

    def status_change_notification(self, status):
        logger.info("OPC UA subscription status changed: %s", status)

    def sync_from_poll(self, item, payload):
        with self._lock:
            state = self._state.setdefault(
                item["device_id"],
                {"power_feedback": None, "tag_count": None, "timestamps": {}, "errors": []},
            )
            data = payload.get("data", {})
            if "power_feedback" in data:
                state["power_feedback"] = data.get("power_feedback")
            if "tag_count" in data:
                state["tag_count"] = _safe_int(data.get("tag_count"), 0)
            state["timestamps"] = data.get("timestamps", {})
            state["errors"] = data.get("errors", [])

    def emit_snapshot(self):
        with self._lock:
            snapshots = []
            for item in self.plan:
                state = self._state.get(
                    item["device_id"],
                    {"power_feedback": None, "tag_count": None, "timestamps": {}, "errors": []},
                )
                snapshots.append(_build_payload_from_state(item, state, online=True))

        for payload in snapshots:
            self.process_device_message(payload, topic=f"devices/{payload['device_id']}/status")


def _apply_security(client):
    policy = os.environ.get("OPCUA_SECURITY_POLICY", "None")
    mode = os.environ.get("OPCUA_SECURITY_MODE", "None")
    cert = os.environ.get("OPCUA_CERT", "")
    key = os.environ.get("OPCUA_KEY", "")
    server_cert = os.environ.get("OPCUA_SERVER_CERT", "")

    if policy.lower() == "none" and mode.lower() == "none":
        return

    if not cert or not key:
        raise RuntimeError("OPC UA 已启用安全模式，但未配置 OPCUA_CERT / OPCUA_KEY")

    parts = [policy, mode, cert, key]
    if server_cert:
        parts.append(server_cert)

    client.set_security_string(",".join(parts))


def _safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _load_tag_signal_address(device_id):
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            SELECT signal_address
            FROM device_signal_points
            WHERE device_id = %s
              AND signal_type = 'tag_count'
              AND is_active = TRUE
            ORDER BY id ASC
            LIMIT 1
            """,
            (device_id,),
        )
        row = cursor.fetchone()
    return _normalize_signal_address(device_id, "tag_count", (row or {}).get("signal_address"))


def _build_default_signal_address(device_id, signal_type):
    suffix_map = {
        "power_feedback": "带电",
        "tag_count": "挂牌",
    }
    suffix = suffix_map.get(signal_type)
    if not suffix or not device_id:
        return None
    return f"ns=2;s={_KEP_NODE_PREFIX}.{device_id}.{suffix}"


def _normalize_signal_address(device_id, signal_type, signal_address):
    raw = (signal_address or "").strip()
    if raw and "?" not in raw and "�" not in raw:
        return raw
    fallback = _build_default_signal_address(device_id, signal_type)
    if raw and fallback and raw != fallback:
        logger.warning(
            "OPC UA signal address fallback for %s/%s: %s -> %s",
            device_id,
            signal_type,
            raw,
            fallback,
        )
    return fallback


@contextmanager
def _opcua_session():
    from opcua import Client

    endpoint = os.environ.get("OPCUA_ENDPOINT", "opc.tcp://127.0.0.1:49320")
    username = os.environ.get("OPCUA_USERNAME")
    password = os.environ.get("OPCUA_PASSWORD", "")

    client = Client(endpoint, timeout=4)
    _apply_security(client)
    if username:
        client.set_user(username)
        client.set_password(password)

    client.connect()
    try:
        yield client
    finally:
        try:
            client.disconnect()
        except Exception:
            pass


def _load_signal_plan():
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            SELECT
                d.device_id,
                d.device_name,
                d.power_room,
                d.cabinet,
                dsp.signal_type,
                dsp.signal_address
            FROM devices d
            INNER JOIN device_signal_points dsp
                ON dsp.device_id = d.device_id
            WHERE d.is_active = TRUE
              AND dsp.is_active = TRUE
              AND dsp.signal_type IN ('power_feedback', 'tag_count')
              AND dsp.signal_address IS NOT NULL
              AND dsp.signal_address <> ''
            ORDER BY d.sort_order ASC, d.device_id ASC, dsp.signal_type ASC
            """
        )
        rows = cursor.fetchall()

    plan = {}
    for row in rows:
        device_id = row["device_id"]
        entry = plan.setdefault(
            device_id,
            {
                "device_id": device_id,
                "device_name": row.get("device_name"),
                "power_room": row.get("power_room"),
                "cabinet": row.get("cabinet"),
                "power_feedback_nodeid": None,
                "tag_count_nodeid": None,
            },
        )
        if row["signal_type"] == "power_feedback" and not entry["power_feedback_nodeid"]:
            entry["power_feedback_nodeid"] = _normalize_signal_address(device_id, "power_feedback", row["signal_address"])
        elif row["signal_type"] == "tag_count" and not entry["tag_count_nodeid"]:
            entry["tag_count_nodeid"] = _normalize_signal_address(device_id, "tag_count", row["signal_address"])

    return [item for item in plan.values() if item.get("power_feedback_nodeid") or item.get("tag_count_nodeid")]


def _read_value(client, nodeid):
    if not nodeid:
        return None, None, None
    node = client.get_node(nodeid)
    data_value = node.get_data_value()
    raw_value = data_value.Value.Value
    status_code = str(data_value.StatusCode)
    ts = data_value.SourceTimestamp or data_value.ServerTimestamp
    return raw_value, status_code, ts


def _build_payload_from_state(plan_item, state, online=True):
    active_tag_count = _safe_int(state.get("tag_count"), 0)
    tag_status = "tagged" if active_tag_count > 0 else "untagged"

    power_status = None
    power_value = state.get("power_feedback")
    if power_value is not None:
        power_status = "powered" if bool(power_value) else "unpowered"

    return {
        "device_id": plan_item["device_id"],
        "status": "online" if online else "warning",
        "timestamp": time.time(),
        "source": "opcua",
        "power_status": power_status,
        "tag_status": tag_status,
        "active_tag_count": active_tag_count,
        "device_name": plan_item.get("device_name"),
        "data": {
            "power_feedback": power_value,
            "tag_count": active_tag_count,
            "power_feedback_nodeid": plan_item.get("power_feedback_nodeid"),
            "tag_count_nodeid": plan_item.get("tag_count_nodeid"),
            "timestamps": state.get("timestamps", {}),
            "errors": state.get("errors", []),
        },
    }


def read_node_value(nodeid):
    if not nodeid:
        return None
    from opcua import ua

    with _opcua_session() as client:
        value, _, _ = _read_value(client, nodeid)
        if isinstance(value, ua.DataValue):
            return value.Value.Value
        return value


def write_node_value(nodeid, value, variant_type):
    if not nodeid:
        raise ValueError("缺少可写 NodeId")

    from opcua import ua

    with _opcua_write_lock:
        with _opcua_session() as client:
            node = client.get_node(nodeid)
            data_value = ua.DataValue()
            data_value.Value = ua.Variant(value, variant_type)
            node.set_attribute(ua.AttributeIds.Value, data_value)


def read_device_tag_count(device_id):
    signal_address = _load_tag_signal_address(device_id)
    if not signal_address:
        return None
    return _safe_int(read_node_value(signal_address), 0)


def write_device_tag_count(device_id, value):
    signal_address = _load_tag_signal_address(device_id)
    if not signal_address:
        return False

    from opcua import ua

    write_node_value(signal_address, _safe_int(value, 0), ua.VariantType.Int16)
    return True


def adjust_device_tag_count(device_id, delta):
    signal_address = _load_tag_signal_address(device_id)
    if not signal_address:
        return None

    current_value = _safe_int(read_node_value(signal_address), 0)
    next_value = max(0, current_value + _safe_int(delta, 0))

    from opcua import ua

    write_node_value(signal_address, next_value, ua.VariantType.Int16)
    return next_value


def _build_payload_for_device(client, plan_item):
    power_value = None
    tag_count_value = None
    status_codes = []
    timestamps = {}
    errors = []

    if plan_item.get("power_feedback_nodeid"):
        try:
            raw_value, status_code, ts = _read_value(client, plan_item["power_feedback_nodeid"])
            power_value = bool(raw_value) if raw_value is not None else None
            status_codes.append(status_code)
            timestamps["power_feedback"] = str(ts) if ts else None
        except Exception as exc:
            errors.append(f"power_feedback:{exc}")

    if plan_item.get("tag_count_nodeid"):
        try:
            raw_value, status_code, ts = _read_value(client, plan_item["tag_count_nodeid"])
            tag_count_value = _safe_int(raw_value, 0)
            status_codes.append(status_code)
            timestamps["tag_count"] = str(ts) if ts else None
        except Exception as exc:
            errors.append(f"tag_count:{exc}")

    online = bool(status_codes) and all(code == "StatusCode(Good)" for code in status_codes)
    active_tag_count = tag_count_value if tag_count_value is not None else 0
    tag_status = "tagged" if active_tag_count > 0 else "untagged"
    power_status = None
    if power_value is not None:
        power_status = "powered" if power_value else "unpowered"

    payload = {
        "device_id": plan_item["device_id"],
        "status": "online" if online else "warning",
        "timestamp": time.time(),
        "source": "opcua",
        "power_status": power_status,
        "tag_status": tag_status,
        "active_tag_count": active_tag_count,
        "device_name": plan_item.get("device_name"),
        "data": {
            "power_feedback": power_value,
            "tag_count": active_tag_count,
            "power_feedback_nodeid": plan_item.get("power_feedback_nodeid"),
            "tag_count_nodeid": plan_item.get("tag_count_nodeid"),
            "timestamps": timestamps,
            "errors": errors,
        },
    }
    return payload


def _listen_loop():
    endpoint = os.environ.get("OPCUA_ENDPOINT", "opc.tcp://127.0.0.1:49320")
    username = os.environ.get("OPCUA_USERNAME")
    password = os.environ.get("OPCUA_PASSWORD", "")
    poll_interval = float(os.environ.get("OPCUA_POLL_INTERVAL", "1"))
    fallback_poll_interval = float(os.environ.get("OPCUA_FALLBACK_POLL_INTERVAL", "15"))
    plan_refresh_interval = float(os.environ.get("OPCUA_PLAN_REFRESH_INTERVAL", "60"))
    subscription_interval_ms = int(os.environ.get("OPCUA_SUBSCRIPTION_INTERVAL_MS", "500"))

    try:
        from opcua import Client
    except Exception:
        logger.exception("未安装 opcua 依赖，无法启动 OPC UA 监听")
        return

    logger.info("OPC UA listener config: endpoint=%s interval=%ss", endpoint, poll_interval)

    while not _stop_event.is_set():
        client = Client(endpoint, timeout=4)
        try:
            _apply_security(client)
            if username:
                client.set_user(username)
                client.set_password(password)

            client.connect()
            logger.info("OPC UA connected: %s", endpoint)

            from app.mqtt_client import process_device_message

            plan = _load_signal_plan()
            last_refresh = time.time()
            last_fallback_poll = 0.0
            logger.info("OPC UA signal plan loaded: %s devices", len(plan))

            handler = _OpcuaSubscriptionHandler(client, plan, process_device_message)
            handler.build_subscription(subscription_interval_ms)

            while not _stop_event.is_set():
                now = time.time()

                if now - last_refresh >= plan_refresh_interval:
                    refreshed_plan = _load_signal_plan()
                    last_refresh = now
                    if refreshed_plan != plan:
                        logger.info("OPC UA signal plan changed, rebuild subscriptions: %s devices", len(refreshed_plan))
                        plan = refreshed_plan
                        handler.delete_subscription()
                        handler = _OpcuaSubscriptionHandler(client, plan, process_device_message)
                        handler.build_subscription(subscription_interval_ms)
                    else:
                        logger.info("OPC UA signal plan refreshed with no changes: %s devices", len(refreshed_plan))

                if (now - last_fallback_poll) >= fallback_poll_interval:
                    for item in plan:
                        if _stop_event.is_set():
                            break
                        try:
                            payload = _build_payload_for_device(client, item)
                            handler.sync_from_poll(item, payload)
                            process_device_message(payload, topic=f"devices/{item['device_id']}/status")
                        except Exception:
                            logger.exception("OPC UA fallback poll failed for device %s", item["device_id"])
                    last_fallback_poll = now

                _stop_event.wait(poll_interval)
        except Exception:
            logger.exception("OPC UA read loop error, retry in 5s")
            _stop_event.wait(5)
        finally:
            try:
                if "handler" in locals() and handler:
                    handler.delete_subscription()
            except Exception:
                pass
            try:
                client.disconnect()
            except Exception:
                pass


def start_opcua_listener():
    global _opcua_thread
    if _opcua_thread and _opcua_thread.is_alive():
        logger.info("OPC UA listener already running")
        return

    _stop_event.clear()
    _opcua_thread = threading.Thread(target=_listen_loop, daemon=True, name="opcua-listener")
    _opcua_thread.start()
    logger.info("OPC UA listener started")


def stop_opcua_listener():
    _stop_event.set()
