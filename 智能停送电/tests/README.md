# 测试框架说明

## 📋 测试概述

本项目采用 pytest 测试框架，包含完整的单元测试、集成测试和端到端测试。

## 🏗️ 测试结构

```
tests/
├── __init__.py              # 测试包初始化
├── conftest.py              # pytest配置和fixtures
├── test_auth.py             # 认证模块测试
├── test_applications.py     # 申请管理测试
├── test_device_monitor.py   # 设备监控测试
├── test_integration.py      # 集成测试
├── test_flask_app.py        # Flask应用测试
├── requirements-test.txt    # 测试依赖
├── pytest.ini              # pytest配置
└── README.md               # 测试说明
```

## 🚀 快速开始

### 1. 安装测试依赖

```bash
pip install -r tests/requirements-test.txt
```

### 2. 运行所有测试

```bash
# 在项目根目录运行
pytest

# 或者指定测试目录
pytest tests/
```

### 3. 运行特定测试

```bash
# 运行认证测试
pytest tests/test_auth.py

# 运行特定测试类
pytest tests/test_auth.py::TestUserAuthentication

# 运行特定测试方法
pytest tests/test_auth.py::TestUserAuthentication::test_user_registration_success
```

### 4. 运行带标记的测试

```bash
# 运行单元测试
pytest -m unit

# 运行集成测试
pytest -m integration

# 运行API测试
pytest -m api

# 运行安全测试
pytest -m security
```

## 📊 测试覆盖率

### 生成覆盖率报告

```bash
# 生成HTML覆盖率报告
pytest --cov=. --cov-report=html

# 生成终端覆盖率报告
pytest --cov=. --cov-report=term-missing

# 生成XML覆盖率报告（用于CI/CD）
pytest --cov=. --cov-report=xml
```

### 查看覆盖率报告

HTML报告生成在 `htmlcov/` 目录，用浏览器打开 `htmlcov/index.html` 查看详细报告。

## 🧪 测试类型

### 1. 单元测试 (Unit Tests)
- **位置**: 各个测试文件中的具体方法
- **标记**: `@pytest.mark.unit`
- **目的**: 测试单个函数或方法的功能
- **特点**: 快速、独立、可重复

### 2. 集成测试 (Integration Tests)
- **位置**: `test_integration.py`
- **标记**: `@pytest.mark.integration`
- **目的**: 测试多个组件之间的交互
- **特点**: 测试组件间的接口和数据流

### 3. 端到端测试 (E2E Tests)
- **位置**: `test_integration.py` 中的 `TestEndToEndWorkflow`
- **标记**: `@pytest.mark.e2e`
- **目的**: 测试完整的业务流程
- **特点**: 模拟真实用户操作

### 4. API测试
- **位置**: 各个测试文件中的API相关测试
- **标记**: `@pytest.mark.api`
- **目的**: 测试RESTful API接口
- **特点**: 测试HTTP请求和响应

## 🔧 测试配置

### pytest.ini 配置说明

```ini
[tool:pytest]
testpaths = tests                    # 测试目录
python_files = test_*.py            # 测试文件模式
python_classes = Test*              # 测试类模式
python_functions = test_*           # 测试函数模式
addopts =                           # 默认选项
    -v                              # 详细输出
    --tb=short                      # 简短回溯
    --cov=.                         # 覆盖率收集
    --cov-report=html              # HTML覆盖率报告
    --cov-fail-under=80            # 覆盖率最低要求80%
```

### 测试标记 (Markers)

- `unit`: 单元测试
- `integration`: 集成测试
- `e2e`: 端到端测试
- `slow`: 慢速测试
- `auth`: 认证测试
- `api`: API测试
- `database`: 数据库测试
- `mqtt`: MQTT测试
- `security`: 安全测试

## 🎯 测试数据

### Fixtures 说明

测试数据通过 pytest fixtures 提供：

- `sample_user_data`: 示例用户数据
- `sample_application_data`: 示例申请数据
- `sample_device_data`: 示例设备数据
- `admin_user_data`: 管理员用户数据
- `dispatcher_user_data`: 调度员用户数据
- `electrician_user_data`: 电工用户数据

### 使用示例

```python
def test_user_registration(self, client, sample_user_data):
    """测试用户注册"""
    response = client.post('/api/register', 
                         data=json.dumps(sample_user_data),
                         content_type='application/json')
    assert response.status_code == 201
```

## 🔍 测试技巧

### 1. 调试测试

```bash
# 在失败时进入调试器
pytest --pdb

# 显示局部变量
pytest -l

# 显示最慢的测试
pytest --durations=10
```

### 2. 并行运行测试

```bash
# 安装pytest-xdist
pip install pytest-xdist

# 并行运行测试
pytest -n auto
```

### 3. 生成测试报告

```bash
# 安装pytest-html
pip install pytest-html

# 生成HTML报告
pytest --html=report.html
```

## 🚨 常见问题

### 1. 数据库连接问题

确保测试数据库配置正确：

```python
# 在 conftest.py 中配置测试数据库
@pytest.fixture(scope="session")
def test_db_config():
    return {
        'host': 'localhost',
        'user': 'test_user',
        'password': 'test_password',
        'database': 'test_power_control'
    }
```

### 2. MQTT连接问题

测试中使用模拟MQTT客户端：

```python
@pytest.fixture(scope="function")
def mock_mqtt_client():
    mock_client = Mock()
    mock_client.connect.return_value = 0
    return mock_client
```

### 3. 测试数据清理

使用 `scope="function"` 确保每个测试都有干净的环境：

```python
@pytest.fixture(scope="function")
def clean_database():
    # 清理测试数据
    yield
    # 测试后清理
```

## 📈 持续集成

### GitHub Actions 示例

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.8
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r tests/requirements-test.txt
    - name: Run tests
      run: |
        pytest --cov=. --cov-report=xml
    - name: Upload coverage
      uses: codecov/codecov-action@v1
```

## 📝 最佳实践

1. **测试命名**: 使用描述性的测试名称
2. **测试独立性**: 每个测试应该独立运行
3. **测试数据**: 使用 fixtures 提供测试数据
4. **覆盖率**: 保持80%以上的代码覆盖率
5. **测试速度**: 单元测试应该快速运行
6. **错误处理**: 测试异常情况和边界条件
7. **文档**: 为复杂的测试添加注释

## 🔄 测试维护

### 添加新测试

1. 在相应的测试文件中添加测试方法
2. 使用适当的标记分类测试
3. 确保测试覆盖新的功能
4. 更新测试文档

### 更新测试

1. 当API接口变更时更新相关测试
2. 当数据结构变更时更新测试数据
3. 定期检查和更新测试依赖

### 测试审查

1. 代码审查时包含测试代码
2. 确保测试覆盖所有关键路径
3. 验证测试的有效性和准确性











