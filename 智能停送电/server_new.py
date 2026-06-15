#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import webbrowser
import time
import socket
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app():
    """创建Flask应用"""
    from app import create_app
    app = create_app()

    # 初始化数据库
    from app.database import init_database
    init_database()

    # 启动设备数据监听器（支持 mqtt / opcua / both；与 docker-compose 一致默认 opcua 接 KepServer）
    source = os.environ.get('DEVICE_DATA_SOURCE', 'opcua').strip().lower()
    if source in ('mqtt', 'both'):
        from app.mqtt_client import start_mqtt_listener
        start_mqtt_listener()
        logger.info("Device data source enabled: MQTT")

    if source in ('opcua', 'both'):
        from app.opcua_client import start_opcua_listener
        start_opcua_listener()
        logger.info("Device data source enabled: OPC UA")

    if source not in ('mqtt', 'opcua', 'both'):
        logger.warning(
            "Unknown DEVICE_DATA_SOURCE=%s, fallback to mqtt", source
        )
        from app.mqtt_client import start_mqtt_listener
        start_mqtt_listener()

    return app


def open_browser():
    """自动打开浏览器"""
    time.sleep(1)
    webbrowser.open("http://localhost:5050")


def get_ip():
    """获取本机IP"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = 'localhost'
    finally:
        s.close()
    return ip


if __name__ == '__main__':
    app = create_app()

    # 获取本机IP
    ip = get_ip()
    port = 5050

    print(f"🚀 启动智能停送电系统...")
    print(f"📱 本地访问: http://localhost:{port}")
    print(f"🌐 局域网访问: http://{ip}:{port}")

    # 自动打开浏览器
    import threading
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()

    # 启动应用
    app.run(host='0.0.0.0', port=port, debug=False)
