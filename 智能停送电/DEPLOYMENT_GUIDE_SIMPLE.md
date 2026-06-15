# 现场部署说明（精简版）

## 1. 适用范围

本方案用于现场服务器部署智能停送电系统的精简生产版，只包含：

- MySQL 数据库
- Flask 后端
- Web 前端（由 Flask 直接托管）

主仓库默认 `docker-compose.yml` 与之一致（无独立监控栈）。若现场设备状态已通过 KEPServer/OPC UA 接入，本方案已足够支撑业务运行。

---

## 2. 部署方式

推荐使用 Docker Compose 精简版：

- 配置文件：[docker-compose.prod.yml](./docker-compose.prod.yml)
- 环境变量模板：[.env.prod.example](./.env.prod.example)

---

## 3. 部署前准备

服务器需要提前安装：

- Docker Engine
- Docker Compose

建议环境：

- Linux 服务器
- 2 CPU / 4 GB 内存起
- 预留 20 GB 以上磁盘

---

## 4. 文件准备

将项目目录上传到服务器后，至少保留这些内容：

- `Dockerfile`
- `docker-compose.prod.yml`
- `.env.prod`
- `app/`
- `web_pages/`
- `shared/database.sql`
- `server_new.py`

---

## 5. 环境变量配置

先复制模板：

```bash
cp .env.prod.example .env.prod
```

然后至少修改以下配置：

```env
MYSQL_ROOT_PASSWORD=你的数据库密码
DB_PASSWORD=你的数据库密码
SECRET_KEY=你的Flask密钥
OPCUA_ENDPOINT=opc.tcp://现场KEPServer地址:49320
DEVICE_DATA_SOURCE=opcua
```

如果现场使用 MQTT，则改为：

```env
DEVICE_DATA_SOURCE=mqtt
MQTT_BROKER=现场MQTT地址
MQTT_PORT=1883
```

如果两种都要：

```env
DEVICE_DATA_SOURCE=both
```

---

## 6. 启动方式

在项目目录执行：

```bash
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d --build
```

查看状态：

```bash
docker compose --env-file .env.prod -f docker-compose.prod.yml ps
```

查看后端日志：

```bash
docker compose --env-file .env.prod -f docker-compose.prod.yml logs -f flask-backend
```

查看数据库日志：

```bash
docker compose --env-file .env.prod -f docker-compose.prod.yml logs -f mysql
```

---

## 7. 访问地址

默认端口：

- 业务系统：`http://服务器IP:5050`
- MySQL 映射端口：`3307`

如果修改了 `.env.prod` 中的 `APP_PORT` 或 `MYSQL_PORT`，按修改后的端口访问。

---

## 8. 升级方式

代码更新后执行：

```bash
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d --build
```

---

## 9. 停止方式

```bash
docker compose --env-file .env.prod -f docker-compose.prod.yml down
```

注意：

- `down` 不会删除 MySQL 数据卷
- 数据仍保留在 `mysql_data` 中

---

## 10. 备份建议

至少备份以下内容：

- `.env.prod`
- MySQL 数据卷
- 项目代码目录

建议定期导出数据库：

```bash
docker exec power_mysql mysqldump -uroot -p你的密码 power_control > power_control_backup.sql
```

---

## 11. 现场建议

第一次到现场建议只跑这两个服务：

- `mysql`
- `flask-backend`

先把以下链路打通：

1. 页面可访问
2. 数据库正常初始化
3. KEPServer / OPC UA 可连接
4. 设备状态能进入系统
5. 停送电申请、审批、检修、送电流程正常

等业务稳定后，再决定是否增加运维监控组件。
