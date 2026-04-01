# 测试说明

## 🔍 快速测试步骤

由于命令行路径编码问题，建议在IDE中直接运行测试。

### 方法1：运行测试脚本（推荐）

1. **在IDE中打开** `test_import.py`
2. **运行脚本**（右键 → Run 或 F5）
3. **检查输出**，应该看到所有导入成功

### 方法2：启动Flask应用

1. **在IDE中打开** `server_new.py`
2. **运行脚本**
3. **访问** http://localhost:5050
4. **检查是否正常启动**

### 方法3：Python命令行测试

在项目根目录（`智能停送电/`）下运行：

```python
# 测试导入
python -c "from app import create_app; app = create_app(); print('Success')"

# 或者交互式测试
python
>>> from app import create_app
>>> app = create_app()
>>> print('App created successfully')
```

## ✅ 预期结果

### 测试脚本应该输出：
```
==================================================
测试模块导入...
==================================================

1. 测试核心模块...
✅ app.create_app 导入成功
✅ app.database 导入成功
✅ app.auth 导入成功

2. 测试路由模块...
✅ app.routes.operations 导入成功
✅ app.routes.approvals 导入成功
...

3. 测试服务模块...
✅ app.services.mqtt_service 导入成功
✅ app.services.workflow_service 导入成功
✅ app.services.operation_service 导入成功

4. 测试创建Flask应用...
✅ Flask应用创建成功

5. 检查注册的路由...
✅ 共注册了 XX 个路由

6. 检查关键路由...
✅ /api/power-apply
✅ /api/power-on-apply
✅ /api/power-off-approve
✅ /api/power-on-approve
✅ /api/list
✅ /api/application/<app_id>
✅ /api/login

==================================================
✅ 所有测试通过！
==================================================
```

### Flask应用启动应该看到：
```
🚀 启动智能停送电系统...
📱 本地访问: http://localhost:5050
🌐 局域网访问: http://...
```

## ⚠️ 可能的问题

### 1. 导入错误
**错误信息**：`ModuleNotFoundError: No module named 'app.routes.operations'`

**原因**：可能 `api.py` 还在，导致冲突

**解决**：检查 `app/routes/` 目录，如果 `api.py` 存在且 `operations.py` 和 `approvals.py` 也存在，可以：
- 重命名 `api.py` 为 `api.py.old`（备份）
- 或删除 `api.py`（如果确认不再需要）

### 2. 蓝图注册错误
**错误信息**：`AttributeError: module 'app.routes.operations' has no attribute 'bp'`

**原因**：蓝图名称错误

**检查**：
- `operations.py` 中应该有：`bp = Blueprint('operations', __name__)`
- `approvals.py` 中应该有：`bp = Blueprint('approvals', __name__)`

### 3. 数据库连接错误
**错误信息**：数据库连接失败

**解决**：
- 检查MySQL是否运行
- 检查环境变量或数据库配置
- 可以先注释掉数据库相关代码进行测试

## 📋 检查清单

- [ ] 所有文件已创建（operations.py, approvals.py）
- [ ] `app/__init__.py` 已更新（导入operations和approvals）
- [ ] 没有语法错误（运行linter检查）
- [ ] 测试脚本可以运行
- [ ] Flask应用可以启动
- [ ] 关键API端点可以访问
