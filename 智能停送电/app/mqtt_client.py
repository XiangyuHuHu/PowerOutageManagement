import paho.mqtt.client as mqtt
import json
import time
import os
from zeroconf import ServiceBrowser, Zeroconf

# MQTT 配置
MQTT_BROKER = os.environ.get('MQTT_BROKER', '192.168.1.123')
MQTT_PORT = int(os.environ.get('MQTT_PORT', 1883))
MQTT_TOPIC = "devices/+/status"

# 设备状态存储
DEVICE_STATUS = {}
DEVICE_HISTORY = []

def on_connect(client, userdata, flags, rc):
    """MQTT连接回调"""
    print(f"✅ 已连接到 MQTT Broker：{MQTT_BROKER}:{MQTT_PORT}")
    client.subscribe(MQTT_TOPIC)
    print(f"📡 已订阅主题：{MQTT_TOPIC}")

def on_message(client, userdata, msg):
    """MQTT消息回调"""
    payload = msg.payload.decode(errors='ignore')
    print(f"📥 收到 MQTT 消息：\n  Topic   : {msg.topic}")
    
    try:
        data = json.loads(payload)
        print(f"  Payload : JSON 格式\n{json.dumps(data, indent=2, ensure_ascii=False)}\n")
        process_device_message(data)
    except json.JSONDecodeError:
        print(f"  Payload : 原始字符串（非 JSON）\n{payload}\n")

def process_device_message(data):
    """处理设备状态消息"""
    try:
        device_id = data.get('device_id', data.get('deviceId', 'unknown'))
        status = data.get('status', 'unknown')
        timestamp = data.get('timestamp', time.time())
        
        # 更新设备状态
        DEVICE_STATUS[device_id] = {
            'status': status,
            'last_update': timestamp,
            'data': data
        }
        
        # 添加到历史记录（保留最近100条）
        history_entry = {
            'device_id': device_id,
            'status': status,
            'timestamp': timestamp,
            'data': data
        }
        DEVICE_HISTORY.append(history_entry)
        
        if len(DEVICE_HISTORY) > 100:
            DEVICE_HISTORY.pop(0)
        
        print(f"📊 设备状态更新: {device_id} -> {status}")
        
        # 检查设备告警
        check_device_alerts(device_id, status, data)
        
    except Exception as e:
        print(f"处理设备消息失败: {e}")

def check_device_alerts(device_id, status, data):
    """检查设备告警"""
    if status in ['error', 'offline', 'warning']:
        print(f"⚠️  设备告警: {device_id} - {status}")
        # 这里可以添加告警通知逻辑

def start_mqtt_listener():
    """启动MQTT监听器"""
    global mqtt_client
    
    try:
        mqtt_client = mqtt.Client()
        mqtt_client.on_connect = on_connect
        mqtt_client.on_message = on_message
        
        # 尝试连接MQTT Broker
        try:
            mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
            print(f"🔗 正在连接MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
            
            def mqtt_loop():
                mqtt_client.loop_forever()
            
            import threading
            mqtt_thread = threading.Thread(target=mqtt_loop, daemon=True)
            mqtt_thread.start()
            print("✅ MQTT监听器已启动")
            
        except Exception as e:
            print(f"❌ MQTT连接失败: {e}")
            print("🔍 尝试自动发现MQTT Broker...")
            discover_mqtt_broker()
            
    except Exception as e:
        print(f"❌ 启动MQTT监听器失败: {e}")

def discover_mqtt_broker():
    """自动发现MQTT Broker"""
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
                print(f"🔍 发现MQTT服务: {address}:{port}")
                # 这里可以更新MQTT_BROKER和MQTT_PORT
    
    try:
        listener = MQTTListener()
        print("🔍 正在搜索MQTT服务...")
    except Exception as e:
        print(f"❌ MQTT服务发现失败: {e}")

def get_device_status():
    """获取设备状态"""
    return DEVICE_STATUS

def get_device_history():
    """获取设备历史"""
    return DEVICE_HISTORY 