#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import webbrowser
import time
import socket
from datetime import datetime
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus指标定义
REQUEST_COUNT = Counter('flask_requests_total', 'Total Flask requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('flask_request_duration_seconds', 'Flask request duration')
ACTIVE_CONNECTIONS = Gauge('flask_active_connections', 'Active connections')

# 系统监控数据
SYSTEM_METRICS = {
    'total_requests': 0,
    'successful_requests': 0,
    'failed_requests': 0,
    'active_users': set(),
    'last_activity': {}
}

def create_app():
    """创建Flask应用"""
    from app import create_app
    app = create_app()
    
    # 初始化数据库
    from app.database import init_database
    init_database()
    
    # 启动MQTT监听器
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
    print(f"📊 监控面板: http://localhost:9090")
    print(f"📈 可视化面板: http://localhost:3000")
    print(f"🔧 系统指标: http://localhost:{port}/metrics")
    
    # 自动打开浏览器
    import threading
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    # 启动应用
    app.run(host='0.0.0.0', port=port, debug=False) 