# 智能停送电系统 - 项目结构建议 V2.0

## 📊 当前结构分析

### 现有结构
```
app/
├── __init__.py              # Flask应用初始化
├── auth.py                  # 认证装饰器
├── database.py              # 数据库连接
├── mqtt_client.py           # MQTT客户端
├── notifications.py         # 通知模块
├── routes/                  # 路由层
│   ├── api.py              # ⚠️ 主要API（可能过于庞大）
│   ├── admin.py            # 管理员路由
│   ├── auth.py             # 认证路由
│   ├── mp.py               # 小程序路由
│   └── static.py           # 静态文件
├── services/                # ✅ 服务层（新创建）
│   ├── mqtt_service.py     # MQTT数据服务
│   └── workflow_service.py # 工作流服务
└── migrations/              # ✅ 数据库迁移
    └── v2_migration.py
```

### ⚠️ 存在的问题

1. **routes/api.py 可能过大**
   - 包含所有业务API（停电、送电、审批、检修等）
   - 随着功能增加会越来越臃肿
   - 难以维护和定位

2. **业务逻辑分散**
   - 部分逻辑在routes中
   - 部分逻辑在services中
   - 缺少统一的业务服务层

3. **缺少模型层**
   - 没有数据模型定义
   - 数据库操作分散在各处

4. **核心功能混杂**
   - database.py、mqtt_client.py 等核心功能在app根目录
   - 可以归类到core/目录

---

## ✅ 建议的新结构

```
app/
├── __init__.py              # Flask应用初始化
│
├── core/                    # 🔧 核心功能模块
│   ├── __init__.py
│   ├── database.py          # 数据库连接管理
│   ├── mqtt_client.py       # MQTT客户端
│   ├── auth.py              # 认证装饰器
│   └── config.py            # 配置管理
│
├── services/                # 💼 业务服务层（业务逻辑）
│   ├── __init__.py
│   ├── mqtt_service.py      # MQTT数据服务
│   ├── workflow_service.py  # 工作流服务
│   ├── operation_service.py # 操作服务（停送电操作）
│   ├── approval_service.py  # 审批服务
│   └── notification_service.py # 通知服务
│
├── routes/                  # 🌐 路由层（API端点）
│   ├── __init__.py
│   ├── auth.py              # 认证相关API
│   ├── operations.py        # 停送电操作API
│   ├── approvals.py         # 审批API
│   ├── admin.py             # 管理员API
│   ├── mp.py                # 小程序API
│   └── static.py            # 静态文件服务
│
├── models/                  # 📊 数据模型层（可选，后续ORM用）
│   ├── __init__.py
│   ├── user.py              # 用户模型
│   ├── operation.py         # 操作模型
│   └── step.py              # 步骤模型
│
├── migrations/              # 📦 数据库迁移
│   ├── __init__.py
│   ├── v2_migration.py
│   └── ...
│
└── utils/                   # 🛠️ 工具函数
    ├── __init__.py
    ├── validators.py        # 数据验证
    └── helpers.py           # 辅助函数
```

---

## 📋 详细模块职责

### 1. core/ - 核心功能模块
**职责**：系统基础设施，不涉及业务逻辑

| 文件 | 职责 |
|------|------|
| `database.py` | 数据库连接、连接池管理 |
| `mqtt_client.py` | MQTT客户端连接、消息接收 |
| `auth.py` | 认证装饰器、权限检查 |
| `config.py` | 配置加载、环境变量管理 |

### 2. services/ - 业务服务层
**职责**：业务逻辑处理，数据库操作，不涉及HTTP

| 文件 | 职责 |
|------|------|
| `mqtt_service.py` | MQTT数据查询、设备状态管理 |
| `workflow_service.py` | 工作流状态机、步骤管理 |
| `operation_service.py` | 停送电操作业务逻辑 |
| `approval_service.py` | 审批业务逻辑 |
| `notification_service.py` | 通知业务逻辑 |

### 3. routes/ - 路由层
**职责**：HTTP请求处理、参数验证、调用服务层

| 文件 | 职责 | API端点示例 |
|------|------|------------|
| `auth.py` | 登录、注册、登出 | `/api/login`, `/api/register` |
| `operations.py` | 停电申请、送电申请 | `/api/power-apply`, `/api/power-on-apply` |
| `approvals.py` | 审批相关 | `/api/power-off-approve`, `/api/power-on-approve` |
| `admin.py` | 管理员功能 | `/api/users`, `/api/system/metrics` |
| `mp.py` | 小程序API | `/api/mp/*` |
| `static.py` | 静态文件、页面路由 | `/`, `/*.html` |

### 4. models/ - 数据模型层（可选）
**职责**：数据模型定义（如果使用ORM如SQLAlchemy）

### 5. migrations/ - 数据库迁移
**职责**：数据库结构变更脚本

### 6. utils/ - 工具函数
**职责**：通用工具函数、验证器、辅助函数

---

## 🔄 重构建议

### 阶段1：拆分routes/api.py

**当前问题**：
- `api.py`包含所有业务API（停电、送电、审批、检修等）
- 预计新增功能后会有15+个端点

**建议拆分**：
```
routes/api.py (删除)
  ↓
routes/
  ├── operations.py    # 停送电操作相关
  │   - /api/power-apply
  │   - /api/power-on-apply
  │   - /api/electrician-verify
  │   - /api/repair-operation
  │   - /api/tag-operation
  │   - /api/complete-operation
  │   - /api/report-fault
  │
  └── approvals.py     # 审批相关
      - /api/power-off-approve
      - /api/power-on-approve
      - /api/application/<id>
```

### 阶段2：移动核心功能到core/

**当前**：
- `app/database.py`
- `app/mqtt_client.py`
- `app/auth.py`
- `app/notifications.py`

**建议**：
```
app/
  ├── core/
  │   ├── database.py
  │   ├── mqtt_client.py
  │   ├── auth.py
  │   └── config.py
  │
  └── services/
      └── notification_service.py  # notifications.py 改名为service
```

### 阶段3：创建operation_service.py

**职责**：操作相关的业务逻辑
- 创建停电申请
- 创建送电申请
- 支持多人申请
- 操作步骤管理

---

## 📊 模块依赖关系

```
routes/          # HTTP层
    ↓ 调用
services/        # 业务逻辑层
    ↓ 调用
core/            # 基础设施层
    ↓ 使用
database/        # 数据库
```

---

## 🎯 重构优先级

### 高优先级（立即）
1. ✅ **拆分routes/api.py** → `operations.py` + `approvals.py`
2. ✅ **创建operation_service.py** → 封装操作业务逻辑

### 中优先级（后续）
3. ⏳ 移动核心功能到`core/`
4. ⏳ 创建`utils/`工具函数模块

### 低优先级（可选）
5. ⏳ 创建`models/`层（如果使用ORM）
6. ⏳ 完善配置管理

---

## 📝 建议的拆分方案

### 方案A：渐进式重构（推荐）
- 保持现有结构，先拆分`api.py`
- 逐步移动文件到新位置
- 影响最小，风险最低

### 方案B：一次性重构
- 一次性完成所有重组
- 需要更新所有import
- 影响较大，但结构更清晰

---

## 🤔 你的选择？

建议采用**方案A（渐进式）**，原因：
1. ✅ 风险低，可以逐步验证
2. ✅ 不影响现有功能
3. ✅ 便于团队协作
4. ✅ 可以边重构边开发新功能

**建议先从拆分`routes/api.py`开始**，这样：
- 新功能代码更清晰
- 便于后续扩展
- 不影响现有代码
