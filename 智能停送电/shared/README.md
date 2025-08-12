# 智能停送电系统 - 共享部分

## 📁 目录结构

```
shared/
├── database.sql          # 数据库结构和初始数据
├── requirements.txt      # Python依赖包
└── common/              # 公共工具和配置
    ├── airport.js       # 机场相关工具
    ├── graceChecker.js  # 表单验证工具
    ├── html-parser.js   # HTML解析工具
    └── ...
```

## 🔧 使用说明

### 数据库
- `database.sql`: 包含所有表结构和初始数据
- 支持MySQL 8.0+
- 字符编码: utf8mb4

### 依赖管理
- `requirements.txt`: Python后端依赖
- 包含Flask、PyMySQL、MQTT等核心依赖

### 公共工具
- `common/`: 前端和后端共用的工具函数
- 包含验证、解析、工具类等

## 📋 部署说明

1. **数据库初始化**
   ```bash
   mysql -u root -p < database.sql
   ```

2. **Python依赖安装**
   ```bash
   pip install -r requirements.txt
   ```

3. **公共工具使用**
   - 前端项目可直接引用common目录
   - 后端项目可导入common模块 