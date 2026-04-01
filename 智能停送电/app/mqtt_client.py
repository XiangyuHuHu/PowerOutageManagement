import json
import logging
import os
import re
import time

import paho.mqtt.client as mqtt
from zeroconf import ServiceBrowser, Zeroconf

# MQTT config
MQTT_BROKER = os.environ.get("MQTT_BROKER", "192.168.1.123")
MQTT_PORT = int(os.environ.get("MQTT_PORT", 1883))
MQTT_TOPIC = os.environ.get("MQTT_TOPIC", "devices/+/status")
MQTT_USERNAME = os.environ.get("MQTT_USERNAME")
MQTT_PASSWORD = os.environ.get("MQTT_PASSWORD")

# In-memory cache
DEVICE_STATUS = {}
DEVICE_HISTORY = []
logger = logging.getLogger(__name__)


def on_connect(client, userdata, flags, rc):
    """MQTT connect callback."""
    logger.info("Connected MQTT broker: %s:%s", MQTT_BROKER, MQTT_PORT)
    topics = [t.strip() for t in MQTT_TOPIC.split(",") if t.strip()]
    for topic in topics:
        client.subscribe(topic)
        logger.info("Subscribed topic: %s", topic)


def on_message(client, userdata, msg):
    """MQTT message callback."""
    payload = msg.payload.decode(errors="ignore")
    logger.debug("Received MQTT message, topic=%s", msg.topic)

    try:
        data = json.loads(payload)
        logger.debug("Payload(JSON): %s", json.dumps(data, ensure_ascii=False))
        process_device_message(data, msg.topic)
    except json.JSONDecodeError:
        logger.warning("Payload(raw non-JSON): %s", payload)


def _value_to_int(value):
    """Convert value to 0/1-like int where possible."""
    if value is None:
        return None

    if isinstance(value, bool):
        return 1 if value else 0

    if isinstance(value, (int, float)):
        return 1 if value != 0 else 0

    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "on", "yes", "y", "powered", "tagged"}:
            return 1
        if normalized in {"0", "false", "off", "no", "n", "unpowered", "untagged"}:
            return 0
        try:
            return 1 if float(normalized) != 0 else 0
        except Exception:
            return None

    return None


def _value_to_count(value):
    """Convert values to integer counts where possible."""
    if value is None:
        return None

    if isinstance(value, bool):
        return 1 if value else 0

    if isinstance(value, int):
        return value

    if isinstance(value, float):
        return int(value)

    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "on", "yes", "y", "powered", "tagged"}:
            return 1
        if normalized in {"false", "off", "no", "n", "unpowered", "untagged"}:
            return 0
        try:
            return int(float(normalized))
        except Exception:
            return None

    return None


def _iter_tag_pairs(payload):
    """
    Extract (tag_name, value) pairs from flexible payloads.

    Supports:
    1) flat dict map
    2) list entries like {"items": [{"id"/"tag"/"name": "...", "value"/"v": ...}]}
    """
    pairs = []

    if not isinstance(payload, dict):
        return pairs

    for key, value in payload.items():
        if isinstance(key, str) and not isinstance(value, (dict, list, tuple)):
            pairs.append((key, value))

    for container_key in ("items", "tags", "values", "data"):
        container = payload.get(container_key)
        if not isinstance(container, list):
            continue

        for item in container:
            if not isinstance(item, dict):
                continue
            tag = item.get("id") or item.get("item_id") or item.get("tag") or item.get("name")
            value = item.get("value", item.get("v"))
            if tag is not None:
                pairs.append((str(tag), value))

    return pairs


def _extract_device_id(data, topic):
    device_id = data.get("device_id") or data.get("deviceId") or data.get("id") or data.get("device")
    if device_id:
        return str(device_id)

    if topic:
        match = re.match(r"^devices/([^/]+)/status$", topic)
        if not match:
            match = re.match(r"^device/([^/]+)/status$", topic)
        if match:
            return match.group(1)

    return "unknown"


def _normalize_status_fields(data, topic):
    """Normalize payload to internal fields used by the system."""
    device_id = _extract_device_id(data, topic)
    status = data.get("status", data.get("state", "unknown"))
    timestamp = data.get("timestamp", data.get("ts", time.time()))

    power_status = data.get("power_status", data.get("powerStatus"))
    tag_status = data.get("tag_status", data.get("tagStatus"))
    active_tag_count = data.get("active_tag_count", data.get("activeTagCount"))
    if active_tag_count is not None:
        active_tag_count = _value_to_count(active_tag_count)
    electrician_name = data.get("electrician_name", data.get("electricianName"))

    power_signal = None
    lock_signals = []
    tag_count_signal = None

    for tag_name, raw_value in _iter_tag_pairs(data):
        low_tag = tag_name.lower()

        if ("带电" in tag_name) or ("甯︾數" in tag_name) or ("powered" in low_tag):
            value = _value_to_int(raw_value)
            if value is not None:
                power_signal = value

        if ("挂牌" in tag_name) or ("鎸傜墝" in tag_name) or ("tag_count" in low_tag) or ("tagcount" in low_tag):
            count_value = _value_to_count(raw_value)
            if count_value is not None:
                tag_count_signal = count_value

        if ("挂锁" in tag_name) or ("鎸傞攣" in tag_name) or ("挂牌" in tag_name) or ("鎸傜墝" in tag_name) or ("lock" in low_tag) or ("tag" in low_tag):
            value = _value_to_int(raw_value)
            if value is not None:
                lock_signals.append(value)

    if power_status is None and power_signal is not None:
        power_status = "powered" if power_signal == 1 else "unpowered"

    if active_tag_count is None and tag_count_signal is not None:
        active_tag_count = tag_count_signal

    if active_tag_count is not None and tag_status is None:
        tag_status = "tagged" if int(active_tag_count) > 0 else "untagged"

    if tag_status is None and lock_signals:
        tag_status = "tagged" if any(v == 1 for v in lock_signals) else "untagged"

    if status == "unknown" and (power_status in ("powered", "unpowered") or tag_status in ("tagged", "untagged")):
        status = "online"

    return device_id, status, timestamp, power_status, tag_status, electrician_name, active_tag_count


def process_device_message(data, topic=None):
    """Process device status message."""
    try:
        device_id, status, timestamp, power_status, tag_status, electrician_name, active_tag_count = _normalize_status_fields(data, topic)

        last_status = DEVICE_STATUS.get(device_id, {})

        DEVICE_STATUS[device_id] = {
            "status": status,
            "power_status": power_status,
            "tag_status": tag_status,
            "active_tag_count": int(active_tag_count or 0),
            "electrician_name": electrician_name,
            "last_update": timestamp,
            "data": data,
        }

        from app.services.mqtt_service import save_device_status_history, update_device_status

        update_device_status(
            device_id=device_id,
            power_status=power_status,
            tag_status=tag_status,
            active_tag_count=active_tag_count,
            electrician_name=electrician_name,
            status_data=data,
        )

        if should_save_history(last_status, power_status, tag_status, active_tag_count):
            save_device_status_history(
                device_id=device_id,
                power_status=power_status,
                tag_status=tag_status,
                active_tag_count=active_tag_count,
                electrician_name=electrician_name,
                status_data=data,
            )

        history_entry = {
            "device_id": device_id,
            "status": status,
            "power_status": power_status,
            "tag_status": tag_status,
            "active_tag_count": int(active_tag_count or 0),
            "electrician_name": electrician_name,
            "timestamp": timestamp,
            "data": data,
        }
        DEVICE_HISTORY.append(history_entry)

        if len(DEVICE_HISTORY) > 100:
            DEVICE_HISTORY.pop(0)

        logger.info(
            "Device status updated: %s -> %s (power=%s, tag=%s, tag_count=%s, electrician=%s)",
            device_id,
            status,
            power_status,
            tag_status,
            active_tag_count,
            electrician_name,
        )

        check_device_alerts(device_id, status, data)

    except Exception:
        logger.exception("Failed to process MQTT message")


def should_save_history(last_status, power_status, tag_status, active_tag_count=None):
    """Save history only on important state changes."""
    last_power = last_status.get("power_status")
    last_tag = last_status.get("tag_status")
    last_count = int(last_status.get("active_tag_count") or 0)
    current_count = int(active_tag_count or 0)
    return (power_status != last_power) or (tag_status != last_tag) or (current_count != last_count)


def check_device_alerts(device_id, status, data):
    """Check device alerts."""
    if status in ["error", "offline", "warning"]:
        logger.warning("Alert device status: %s - %s", device_id, status)


def start_mqtt_listener():
    """Start MQTT listener."""
    global mqtt_client

    try:
        mqtt_client = mqtt.Client()
        if MQTT_USERNAME:
            mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        mqtt_client.on_connect = on_connect
        mqtt_client.on_message = on_message

        try:
            mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
            logger.info("Connecting MQTT broker: %s:%s", MQTT_BROKER, MQTT_PORT)

            def mqtt_loop():
                mqtt_client.loop_forever()

            import threading

            mqtt_thread = threading.Thread(target=mqtt_loop, daemon=True)
            mqtt_thread.start()
            logger.info("MQTT listener started")

        except Exception:
            logger.exception("MQTT connection failed")
            logger.info("Trying to discover MQTT broker...")
            discover_mqtt_broker()

    except Exception:
        logger.exception("Failed to start MQTT listener")


def discover_mqtt_broker():
    """Discover MQTT broker with zeroconf."""

    class MQTTListener:
        def __init__(self):
            self.zeroconf = Zeroconf()
            self.browser = ServiceBrowser(self.zeroconf, "_mqtt._tcp.local.", self)

        def remove_service(self, zeroconf, type, name):
            pass

        def add_service(self, zeroconf, type, name):
            info = zeroconf.get_service_info(type, name)
            if info:
                address = info.parsed_addresses()[0]
                port = info.port
                logger.info("Discovered MQTT service: %s:%s", address, port)

    try:
        MQTTListener()
        logger.info("Searching MQTT service...")
    except Exception:
        logger.exception("MQTT service discovery failed")


def get_device_status():
    """Get current device status cache."""
    return DEVICE_STATUS


def get_device_history():
    """Get device history cache."""
    return DEVICE_HISTORY


if __name__ == "__main__":
    print("MQTT test tool")
    print("=" * 50)
    print(f"MQTT Broker: {MQTT_BROKER}")
    print(f"MQTT Port: {MQTT_PORT}")
    print(f"Subscribe topic: {MQTT_TOPIC}")
    print("=" * 50)
    print("\nPress Ctrl+C to exit\n")

    try:
        start_mqtt_listener()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nBye")
    except Exception as exc:
        print(f"Run failed: {exc}")
