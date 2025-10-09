# Docker配置更新说明

## 🔧 更新内容

由于项目文件结构清理，Docker配置文件已更新以适应新的文件位置。

### 📁 文件路径变更

#### **docker-compose.yml 更新**
```yaml
# 更新前
- ./database.sql:/docker-entrypoint-initdb.d/database.sql

# 更新后  
- ./shared/database.sql:/docker-entrypoint-initdb.d/database.sql
```

#### **Dockerfile 更新**
```dockerfile
# 更新前
COPY requirements.txt ./
COPY common ./common
CMD ["python", "server.py"]

# 更新后
COPY shared/requirements.txt ./
COPY shared/common ./common
COPY server_new.py ./
COPY app ./app
CMD ["python", "server_new.py"]
```

### 🎯 更新原因

1. **数据库文件位置**：
   - 原来：`./database.sql`
   - 现在：`./shared/database.sql`
   - 原因：避免重复，统一放在shared目录

2. **依赖文件位置**：
   - 原来：`./requirements.txt`
   - 现在：`./shared/requirements.txt`
   - 原因：避免重复，统一放在shared目录

3. **公共组件位置**：
   - 原来：`./common`
   - 现在：`./shared/common`
   - 原因：避免重复，统一放在shared目录

4. **新增文件**：
   - 添加：`server_new.py`（新版本服务器）
   - 添加：`app/`（模块化应用目录）
   - 原因：支持新的模块化架构

5. **启动文件变更**：
   - 原来：`CMD ["python", "server.py"]`
   - 现在：`CMD ["python", "server_new.py"]`
   - 原因：使用新的模块化服务器

### ✅ 验证更新

#### **文件存在性检查**
```bash
# 检查数据库文件
ls -la shared/database.sql

# 检查依赖文件  
ls -la shared/requirements.txt

# 检查公共组件
ls -la shared/common/
```

#### **Docker构建测试**
```bash
# 测试Docker构建
docker build -t power-control-test .

# 测试Docker Compose
docker compose config
```

### 🚀 运行方式

#### **外部运行（推荐）**
```bash
# 激活虚拟环境
source .venv/bin/activate

# 运行新版本服务器
python server_new.py
```

#### **Docker运行**
```bash
# 构建并启动所有服务
docker compose up --build

# 后台运行
docker compose up --build -d
```

### 📋 服务端口

- **Web应用**：http://localhost:5050
- **Prometheus监控**：http://localhost:9090  
- **Grafana可视化**：http://localhost:3000
- **MySQL数据库**：localhost:3307

### 🔍 故障排除

#### **常见问题**
1. **文件不存在错误**：
   ```bash
   # 检查文件是否存在
   ls -la shared/database.sql
   ls -la shared/requirements.txt
   ```

2. **Docker构建失败**：
   ```bash
   # 清理Docker缓存
   docker system prune -a
   # 重新构建
   docker compose up --build
   ```

3. **数据库连接失败**：
   ```bash
   # 检查MySQL容器状态
   docker compose ps
   # 查看MySQL日志
   docker compose logs mysql
   ```

### 🎉 更新完成

✅ **文件路径已更新**：适应新的项目结构  
✅ **Docker配置已优化**：支持模块化架构  
✅ **功能保持完整**：所有服务正常运行  
✅ **文档已更新**：包含详细的更新说明  

现在Docker配置已经完全适配新的项目结构！ 