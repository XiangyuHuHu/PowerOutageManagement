import pytest
import os
import sys
import tempfile
import shutil
from unittest.mock import Mock, patch

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

@pytest.fixture
def app():
    """创建Flask应用实例"""
    from server import app
    
    # 配置测试环境
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['SESSION_TYPE'] = 'filesystem'
    
    # 使用测试数据库
    app.config['DB_HOST'] = 'localhost'
    app.config['DB_USER'] = 'test_user'
    app.config['DB_PASSWORD'] = 'test_password'
    app.config['DB_NAME'] = 'test_power_control'
    
    return app

@pytest.fixture
def client(app):
    """创建Flask测试客户端"""
    return app.test_client()

# 测试配置
@pytest.fixture(scope="session")
def test_config():
    """测试配置"""
    return {
        'TESTING': True,
        'SECRET_KEY': 'test-secret-key',
        'DB_HOST': 'localhost',
        'DB_USER': 'test_user',
        'DB_PASSWORD': 'test_password',
        'DB_NAME': 'test_power_control',
        'MQTT_BROKER': 'localhost',
        'MQTT_PORT': 1883,
        'FLASK_ENV': 'testing'
    }

@pytest.fixture(scope="session")
def test_db_config():
    """测试数据库配置"""
    return {
        'host': 'localhost',
        'user': 'test_user',
        'password': 'test_password',
        'database': 'test_power_control',
        'charset': 'utf8mb4',
        'cursorclass': 'DictCursor'
    }

@pytest.fixture(scope="function")
def temp_dir():
    """临时目录"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture(scope="function")
def mock_mqtt_client():
    """模拟MQTT客户端"""
    mock_client = Mock()
    mock_client.connect.return_value = 0
    mock_client.subscribe.return_value = (0, 0)
    mock_client.publish.return_value = (0, 0)
    mock_client.disconnect.return_value = 0
    return mock_client

@pytest.fixture(scope="function")
def mock_db_connection():
    """模拟数据库连接"""
    mock_conn = Mock()
    mock_cursor = Mock()
    mock_conn.cursor.return_value = mock_cursor
    return mock_conn, mock_cursor

@pytest.fixture(scope="function")
def sample_user_data():
    """示例用户数据"""
    return {
        'username': 'testuser',
        'password': 'testpass123',
        'email': 'test@example.com',
        'role': 'user',
        'department': '测试部门',
        'phone': '13800138000'
    }

@pytest.fixture(scope="function")
def sample_application_data():
    """示例申请数据"""
    return {
        'user_id': 1,
        'application_type': 'power_off',
        'device_id': 'DEV001',
        'reason': '设备检修',
        'start_time': '2024-01-01 10:00:00',
        'end_time': '2024-01-01 18:00:00',
        'status': 'pending'
    }

@pytest.fixture(scope="function")
def sample_device_data():
    """示例设备数据"""
    return {
        'device_id': 'DEV001',
        'device_name': '测试设备1',
        'device_type': 'transformer',
        'location': '变电站A',
        'status': 'online',
        'last_maintenance': '2024-01-01'
    }

@pytest.fixture(scope="function")
def admin_user_data():
    """管理员用户数据"""
    return {
        'username': 'admin',
        'password': 'admin123',
        'email': 'admin@example.com',
        'role': 'admin',
        'department': '管理部',
        'phone': '13900139000'
    }

@pytest.fixture(scope="function")
def dispatcher_user_data():
    """调度员用户数据"""
    return {
        'username': 'dispatcher',
        'password': 'dispatcher123',
        'email': 'dispatcher@example.com',
        'role': 'dispatcher',
        'department': '调度部',
        'phone': '13700137000'
    }

@pytest.fixture(scope="function")
def electrician_user_data():
    """电工用户数据"""
    return {
        'username': 'electrician',
        'password': 'electrician123',
        'email': 'electrician@example.com',
        'role': 'electrician',
        'department': '检修部',
        'phone': '13600136000'
    }
