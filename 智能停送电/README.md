# 智能停送电系统

一套完整的智能停送电管理系统，支持Web端和小程序端，采用前后端分离架构。

## 📁 项目结构

```
智能停送电/
├── shared/                    # 共享部分
│   ├── database.sql          # 数据库结构
│   ├── requirements.txt      # Python依赖
│   └── common/              # 公共工具
├── web-backend/              # Web后端
│   ├── server.py            # Flask应用
│   ├── web_pages/           # Web前端页面
│   ├── Dockerfile           # Docker配置
│   └── docker-compose.yml   # 容器编排
└── miniprogram/              # 小程序端
    ├── pages/               # 页面文件
    ├── components/          # 组件
    ├── store/              # 状态管理
    └── static/             # 静态资源
```

## 🚀 快速开始

### 1. 环境准备
```bash
# 安装Python依赖
cd shared
pip install -r requirements.txt

# 安装Node.js依赖
cd miniprogram
npm install
```

### 2. 数据库初始化
```bash
# 创建数据库
mysql -u root -p
CREATE DATABASE power_control CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# 导入数据
mysql -u root -p power_control < shared/database.sql
```

### 3. 启动Web后端
```bash
cd web-backend
python server.py
```

### 4. 启动小程序
```bash
cd miniprogram
# 使用HBuilderX打开项目
# 或使用命令行构建
uni build
```

## 📱 功能特性

### 用户管理
- ✅ 用户注册/登录
- ✅ 角色权限管理
- ✅ 用户信息管理
- ✅ 密码修改

### 申请管理
- ✅ 停电申请提交
- ✅ 送电申请提交
- ✅ 申请状态跟踪
- ✅ 申请历史查看

### 审批流程
- ✅ 申请审批处理
- ✅ 审批历史记录
- ✅ 审批状态更新
- ✅ 审批意见管理

### 检修管理
- ✅ 检修任务管理
- ✅ 检修进度跟踪
- ✅ 检修报告提交
- ✅ 检修状态更新

### 系统功能
- ✅ 数据统计展示
- ✅ 系统监控
- ✅ 数据导出
- ✅ 消息通知

## 🔧 技术栈

### 后端技术
- **Python**: Flask框架
- **数据库**: MySQL 8.0
- **消息队列**: MQTT
- **监控**: Prometheus + Grafana
- **容器化**: Docker + Docker Compose

### 前端技术
- **Web端**: Vue.js + Element-Plus
- **小程序**: uni-app框架
- **状态管理**: Vuex
- **UI组件**: uni-ui

### 开发工具
- **IDE**: HBuilderX / VS Code
- **调试**: Chrome DevTools / 微信开发者工具
- **版本控制**: Git

## 📊 部署说明

### Web端部署
```bash
cd web-backend
docker compose up -d
```

访问地址：
- Web应用: http://localhost:5050
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000

### 小程序部署
1. 微信小程序：上传到微信公众平台
2. H5版本：部署到Web服务器
3. APP版本：打包发布到应用商店

## 🔍 开发指南

### 添加新功能
1. 在`shared/database.sql`中添加数据库表
2. 在`web-backend/server.py`中添加API接口
3. 在`web-backend/web_pages/`中添加Web页面
4. 在`miniprogram/pages/`中添加小程序页面

### 数据库变更
1. 修改`shared/database.sql`
2. 更新相关API接口
3. 测试数据一致性

### API接口规范
- 统一使用RESTful风格
- 返回JSON格式数据
- 包含状态码和消息
- 支持分页和筛选

## 📝 配置说明

### 环境变量
```bash
# 数据库配置
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=power_control

# MQTT配置
MQTT_BROKER=localhost
MQTT_PORT=1883

# 应用配置
FLASK_ENV=development
SECRET_KEY=your_secret_key
```

### 权限配置
```javascript
// 角色权限
const ROLE_PERMISSIONS = {
  admin: ['all'],
  dispatcher: ['approval', 'history'],
  electrician: ['apply', 'repair'],
  user: ['apply', 'view']
}
```

## 🐛 常见问题

### 数据库连接问题
1. 检查MySQL服务是否启动
2. 确认数据库用户名密码正确
3. 检查数据库字符集设置

### 字符编码问题
1. 确保数据库使用utf8mb4字符集
2. 检查Flask应用字符编码设置
3. 验证前端页面meta标签设置

### Docker部署问题
1. 检查Docker服务是否启动
2. 确认端口映射正确
3. 查看容器日志排查问题

## 📞 技术支持

- 项目文档: [查看详细文档](docs/)
- 问题反馈: [提交Issue](issues/)
- 技术交流: [加入讨论](discussions/)

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🤝 贡献指南

欢迎提交 Pull Request 来改进项目！

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

---

**智能停送电系统** - 让电力管理更智能、更高效！

