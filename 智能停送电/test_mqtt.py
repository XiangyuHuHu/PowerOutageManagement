      #!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MQTT测试脚本
用于单独测试MQTT连接和消息接收功能
"""

import os
import sys
import time
import json

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.mqtt_client import start_mqtt_listener, get_device_status, get_device_history

def print_device_status():
    """打印当前设备状态"""
    status = get_device_status()
    history = get_device_history()
    
    print("\n" + "="*50)
    print("📊 当前设备状态")
    print("="*50)
    
    if not status:
        print("暂无设备状态数据")
    else:
        for device_id, device_info in status.items():
            print(f"\n设备ID: {device_id}")
            print(f"  状态: {device_info.get('status', 'unknown')}")
            print(f"  最后更新: {device_info.get('last_update', 'unknown')}")
            if 'data' in device_info:
                print(f"  数据: {json.dumps(device_info['data'], ensure_ascii=False, indent=4)}")
    
    print(f"\n历史记录数量: {len(history)}")
    if history:
        print("\n最近5条历史记录:")
        for entry in history[-5:]:
            print(f"  - {entry.get('device_id')}: {entry.get('status')} @ {entry.get('timestamp')}")
    
    print("="*50 + "\n")

def main():
    """主函数"""
    print("🚀 MQTT测试工具")
    print("="*50)
    print(f"MQTT Broker: {os.environ.get('MQTT_BROKER', '192.168.1.123')}")
    print(f"MQTT Port: {os.environ.get('MQTT_PORT', '1883')}")
    print(f"订阅主题: {os.environ.get('MQTT_TOPIC', 'devices/+/status')}")
    print(f"用户名: {os.environ.get('MQTT_USERNAME', '(未设置)')}")
    print("="*50)
    print("\n按 Ctrl+C 退出\n")
    
    # 启动MQTT监听
    try:
        start_mqtt_listener()
        
        # 等待连接
        time.sleep(2)
        
        # 定期打印状态
        try:
            while True:
                time.sleep(5)  # 每5秒打印一次状态
                print_device_status()
        except KeyboardInterrupt:
            print("\n\n👋 退出测试")
            
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()

