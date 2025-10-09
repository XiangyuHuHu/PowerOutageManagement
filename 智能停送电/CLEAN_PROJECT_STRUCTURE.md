# 智能停送电系统 - 清理后项目结构

## 📁 项目结构概览

```
智能停送电/
├── 📁 app/                    # 新版本模块化应用
│   ├── 📁 routes/            # 路由模块
│   ├── __init__.py           # 应用初始化
│   ├── auth.py               # 认证模块
│   ├── database.py           # 数据库模块
│   ├── mqtt_client.py        # MQTT客户端
│   └── notifications.py      # 通知模块
├── 📁 web_pages/             # Web端页面
│   ├── login.html            # 登录页面
│   ├── admin.html            # 管理员主页
│   ├── device_monitor.html   # 设备监控
│   ├── notifications.html    # 系统通知
│   └── ...                   # 其他页面
├── 📁 miniprogram/           # 小程序端
│   ├── 📁 pages/            # 页面文件
│   ├── 📁 components/       # 组件
│   └── ...                   # 其他小程序文件
├── 📁 shared/               # 共享资源
│   ├── 📁 common/           # 公共组件
│   ├── database.sql         # 数据库脚本
│   └── requirements.txt     # 依赖文件
├── 📁 grafana/              # Grafana配置
├── 📁 data/                 # 数据目录
├── 📁 flask_session/        # Flask会话文件
├── 📁 .venv/                # Python虚拟环境
├── server.py                # 原版服务器（保留）
├── server_new.py            # 新版本服务器入口
├── docker-compose.yml       # Docker编排
├── Dockerfile               # Docker镜像
├── prometheus.yml           # Prometheus配置
└── README.md               # 项目说明
```

## 🧹 已清理的文件

### ✅ 删除的重复文件
- `web-backend/` 整个目录（重复的web后端）
- `test.py`, `test2.py`, `test3.py` （测试文件）
- `test-api.py`, `test-db.py`, `test-local.py` （测试文件）
- `cookies.txt`, `cookies1.txt`, `cookies2.txt` （临时文件）
- `docker-compose-simple.yml` （简化版Docker配置）
- `docker-compose-monitoring.yml` （监控版Docker配置）
- `flask-dashboard.json` （临时配置文件）
- `mosquitto.conf` （MQTT配置文件）
- 根目录的 `database.sql` （重复，保留shared/中的）
- 根目录的 `requirements.txt` （重复，保留shared/中的）

### ✅ 删除的临时文档
- 多个重复的功能实现总结文档
- 修复总结文档（保留核心文档）

## 🎯 当前项目特点

### 📱 双端支持
- **Web端**：完整的Web管理系统
- **小程序端**：移动端应用

### 🔧 技术栈
- **后端**：Flask + MySQL + MQTT
- **前端**：Vue.js + Element Plus
- **部署**：Docker + Docker Compose
- **监控**：Prometheus + Grafana

### 🚀 运行方式
1. **外部运行**：`python server_new.py`
2. **Docker运行**：`docker compose up --build`

## 📋 保留的核心文件

### 🔧 服务器文件
- `server.py` - 原版服务器（功能完整）
- `server_new.py` - 新版本服务器（模块化）

### 📄 配置文件
- `docker-compose.yml` - Docker编排
- `Dockerfile` - Docker镜像
- `prometheus.yml` - 监控配置

### 📚 文档文件
- `README.md` - 项目说明
- `PROJECT_STRUCTURE.md` - 详细结构说明
- `项目重构总结.md` - 重构过程
- `MQTT功能扩展总结.md` - MQTT功能说明

## 🎉 清理效果

✅ **文件数量减少**：删除了约20个重复/临时文件  
✅ **结构更清晰**：去除了web-backend重复目录  
✅ **文档更简洁**：删除了重复的总结文档  
✅ **功能完整**：保留了所有核心功能文件  

现在项目结构更加简洁明了，便于维护和开发！ 