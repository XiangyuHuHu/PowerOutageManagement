# 智能停送电系统 - 项目结构

## 📁 完整目录结构

```
智能停送电/
├── 📁 shared/                    # 共享部分
│   ├── 📄 database.sql          # 数据库结构和初始数据
│   ├── 📄 requirements.txt      # Python依赖包
│   ├── 📄 README.md            # 共享部分说明
│   └── 📁 common/              # 公共工具和配置
│       ├── 📄 airport.js       # 机场相关工具
│       ├── 📄 graceChecker.js  # 表单验证工具
│       ├── 📄 html-parser.js   # HTML解析工具
│       └── ...
│
├── 📁 web-backend/              # Web后端
│   ├── 📄 server.py            # Flask主应用
│   ├── 📄 Dockerfile           # Docker构建文件
│   ├── 📄 docker-compose.yml   # Docker编排文件
│   ├── 📄 requirements.txt     # Python依赖
│   ├── 📄 README.md           # Web后端说明
│   ├── 📁 web_pages/          # Web前端页面
│   │   ├── 📄 login.html      # 登录页面
│   │   ├── 📄 register.html   # 注册页面
│   │   ├── 📄 admin.html      # 管理员页面
│   │   ├── 📄 user_management.html # 用户管理页面
│   │   ├── 📄 stats.html      # 统计页面
│   │   ├── 📄 approval.html   # 审批页面
│   │   ├── 📄 apply.html      # 申请页面
│   │   ├── 📄 repair.html     # 检修页面
│   │   ├── 📄 detail.html     # 详情页面
│   │   └── ...
│   ├── 📁 grafana/            # Grafana配置
│   ├── 📄 prometheus.yml      # Prometheus配置
│   ├── 📄 docker-compose-monitoring.yml # 监控服务编排
│   ├── 📄 docker-compose-simple.yml # 简化服务编排
│   ├── 📁 flask_session/      # Flask会话文件
│   ├── 📄 flask-dashboard.json # Flask仪表板配置
│   ├── 📄 test-api.py         # API测试文件
│   ├── 📄 test-db.py          # 数据库测试文件
│   └── 📄 test-local.py       # 本地功能测试
│
├── 📁 miniprogram/              # 小程序端
│   ├── 📄 App.vue             # 应用入口
│   ├── 📄 main.js             # 主入口
│   ├── 📄 pages.json          # 页面配置
│   ├── 📄 manifest.json       # 应用配置
│   ├── 📄 package.json        # Node.js依赖
│   ├── 📄 uni.scss           # 全局样式
│   ├── 📄 README.md          # 小程序说明
│   ├── 📁 pages/             # 页面文件
│   │   ├── 📁 index/         # 首页
│   │   ├── 📁 login/         # 登录页
│   │   ├── 📁 apply/         # 申请页
│   │   ├── 📁 approval/      # 审批页
│   │   ├── 📁 repair/        # 检修页
│   │   ├── 📁 poweroff/      # 停电页
│   │   ├── 📁 power_on_apply/ # 送电申请页
│   │   ├── 📁 approval_history/ # 审批历史页
│   │   ├── 📁 about/         # 关于页
│   │   ├── 📁 admin/         # 管理员页
│   │   ├── 📁 dispatcher_home/ # 调度员首页
│   │   ├── 📁 electrician_home/ # 电工首页
│   │   ├── 📁 error/         # 错误页
│   │   ├── 📁 test/          # 测试页
│   │   └── ...
│   ├── 📁 components/        # 组件
│   │   ├── 📁 page-head/     # 页面头部
│   │   ├── 📁 page-foot/     # 页面底部
│   │   ├── 📁 product/       # 产品组件
│   │   ├── 📁 u-link/        # 链接组件
│   │   ├── 📁 u-charts/      # 图表组件
│   │   └── ...
│   ├── 📁 store/             # 状态管理
│   │   ├── 📄 index.js       # Store入口
│   │   └── 📄 counter.js     # 计数器
│   ├── 📁 static/            # 静态资源
│   │   ├── 📁 icons/         # 图标
│   │   ├── 📁 image/         # 图片
│   │   ├── 📁 font/          # 字体
│   │   └── ...
│   ├── 📁 uni_modules/       # uni-app模块
│   ├── 📁 wxcomponents/      # 微信小程序组件
│   ├── 📁 platforms/         # 平台相关
│   ├── 📁 unpackage/         # 打包文件
│   ├── 📁 windows/           # 窗口配置
│   ├── 📁 hybrid/            # 混合应用
│   └── ...
│
├── 📄 README.md               # 项目总说明
├── 📄 PROJECT_STRUCTURE.md    # 项目结构说明
├── 📄 LICENSE                 # 许可证
└── 📄 changelog.md           # 更新日志
```

## 🔄 文件分类说明

### 📁 shared/ - 共享部分
**用途**: 前后端共用的资源
- **数据库**: 表结构、初始数据、索引
- **依赖**: Python包依赖列表
- **工具**: 公共工具函数和配置

### 📁 web-backend/ - Web后端
**用途**: Web应用的后端服务和前端页面
- **服务**: Flask应用、API接口、数据库操作
- **页面**: HTML页面、CSS样式、JavaScript
- **部署**: Docker配置、监控配置
- **测试**: 各种测试文件

### 📁 miniprogram/ - 小程序端
**用途**: 移动端应用（小程序、H5、APP）
- **页面**: Vue页面文件
- **组件**: 可复用组件
- **配置**: 应用配置、页面路由
- **资源**: 静态资源文件

## 🔗 各部分关系

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   shared/       │    │  web-backend/   │    │  miniprogram/   │
│                 │    │                 │    │                 │
│ • database.sql  │◄───┤ • server.py     │    │ • pages/        │
│ • requirements  │    │ • web_pages/    │    │ • components/   │
│ • common/       │    │ • Dockerfile    │    │ • store/        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
   ┌─────────────────────────────────────────────────────────────┐
   │                    数据库 (MySQL)                           │
   │  • users (用户表)                                          │
   │  • applications (申请表)                                   │
   │  • application_logs (操作日志)                            │
   │  • notifications (通知表)                                  │
   └─────────────────────────────────────────────────────────────┘
```

## 🚀 开发流程

### 1. 数据库变更
```bash
# 修改共享数据库文件
vim shared/database.sql

# 更新Web后端API
vim web-backend/server.py

# 更新小程序页面
vim miniprogram/pages/xxx/xxx.vue
```

### 2. 添加新功能
```bash
# 1. 数据库表
shared/database.sql

# 2. 后端API
web-backend/server.py

# 3. Web页面
web-backend/web_pages/xxx.html

# 4. 小程序页面
miniprogram/pages/xxx/xxx.vue
```

### 3. 部署流程
```bash
# Web端部署
cd web-backend
docker compose up -d

# 小程序发布
cd miniprogram
# 使用HBuilderX发布
```

## 📋 开发规范

### 文件命名
- **数据库**: 小写字母，下划线分隔
- **Python**: 小写字母，下划线分隔
- **JavaScript**: 驼峰命名
- **Vue组件**: 短横线分隔
- **HTML**: 小写字母，下划线分隔

### 目录结构
- **按功能分组**: 相关文件放在同一目录
- **按类型分组**: 页面、组件、工具分别存放
- **按平台分组**: Web端、小程序端分别存放

### 版本控制
- **共享部分**: 数据库变更需要同步更新
- **Web端**: 独立开发和部署
- **小程序端**: 独立开发和发布

## 🔧 配置说明

### 环境配置
```bash
# 开发环境
DEV_API=http://localhost:5050

# 生产环境
PROD_API=https://your-domain.com

# 测试环境
TEST_API=https://test-domain.com
```

### 数据库配置
```bash
# 本地开发
DB_HOST=localhost
DB_PORT=3306

# Docker环境
DB_HOST=mysql
DB_PORT=3306
```

### 权限配置
```javascript
// 角色权限映射
const ROLE_PERMISSIONS = {
  admin: ['all'],
  dispatcher: ['approval', 'history'],
  electrician: ['apply', 'repair'],
  user: ['apply', 'view']
}
```

---

**智能停送电系统** - 让电力管理更智能、更高效！ 