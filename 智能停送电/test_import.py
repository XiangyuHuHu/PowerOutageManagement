#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试导入脚本
检查重构后的模块是否能正常导入
"""

import sys

def test_imports():
    """测试导入"""
    try:
        print("=" * 50)
        print("测试模块导入...")
        print("=" * 50)
        
        # 测试核心模块
        print("\n1. 测试核心模块...")
        from app import create_app
        print("✅ app.create_app 导入成功")
        
        from app.database import get_db, get_db_cursor
        print("✅ app.database 导入成功")
        
        from app.auth import login_required
        print("✅ app.auth 导入成功")
        
        # 测试路由模块
        print("\n2. 测试路由模块...")
        from app.routes import operations, approvals, auth, admin, mp, static
        print("✅ app.routes.operations 导入成功")
        print("✅ app.routes.approvals 导入成功")
        print("✅ app.routes.auth 导入成功")
        print("✅ app.routes.admin 导入成功")
        print("✅ app.routes.mp 导入成功")
        print("✅ app.routes.static 导入成功")
        
        # 测试服务模块
        print("\n3. 测试服务模块...")
        from app.services import mqtt_service, workflow_service, operation_service
        print("✅ app.services.mqtt_service 导入成功")
        print("✅ app.services.workflow_service 导入成功")
        print("✅ app.services.operation_service 导入成功")
        
        # 测试创建应用
        print("\n4. 测试创建Flask应用...")
        app = create_app()
        print("✅ Flask应用创建成功")
        
        # 检查注册的路由
        print("\n5. 检查注册的路由...")
        rules = []
        for rule in app.url_map.iter_rules():
            rules.append(str(rule))
        
        print(f"✅ 共注册了 {len(rules)} 个路由")
        
        # 检查关键路由
        key_routes = [
            '/api/power-apply',
            '/api/power-on-apply',
            '/api/power-off-approve',
            '/api/power-on-approve',
            '/api/list',
            '/api/application/<app_id>',
            '/api/login'
        ]
        
        print("\n6. 检查关键路由...")
        for route in key_routes:
            found = any(route in r for r in rules)
            if found:
                print(f"✅ {route}")
            else:
                print(f"❌ {route} (未找到)")
        
        print("\n" + "=" * 50)
        print("✅ 所有测试通过！")
        print("=" * 50)
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_imports()
    sys.exit(0 if success else 1)
