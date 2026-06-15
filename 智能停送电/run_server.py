#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""运行服务器脚本"""
import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == '__main__':
    try:
        print("=" * 50)
        print("正在启动智能停送电系统...")
        print("=" * 50)
        
        # 导入并运行server_new
        from server_new import create_app, get_ip
        import webbrowser
        import time
        import threading
        
        app = create_app()
        
        # 获取本机IP
        ip = get_ip()
        port = 5050
        
        print(f"\n🚀 启动智能停送电系统...")
        print(f"📱 本地访问: http://localhost:{port}")
        print(f"🌐 局域网访问: http://{ip}:{port}")
        
        # 自动打开浏览器
        def open_browser():
            time.sleep(1)
            webbrowser.open("http://localhost:5050")
        
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
        
        # 启动应用
        print("\n" + "=" * 50)
        print("服务器已启动，按 Ctrl+C 停止")
        print("=" * 50 + "\n")
        
        app.run(host='0.0.0.0', port=port, debug=False)
        
    except KeyboardInterrupt:
        print("\n\n正在关闭服务器...")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
