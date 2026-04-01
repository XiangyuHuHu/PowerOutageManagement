# 智能停送电系统 — Docker 安装与部署说明

本文说明如何将本项目**整体文件夹**复制到其他电脑后，用 Docker Compose 一键启动（MySQL + Flask 后端 + Prometheus + Grafana）。

---

## 1. 是否「打包整个文件夹 + docker compose up」即可？

**基本可以。** 满足下面条件即可在新机器上部署：

| 条件 | 说明 |
|------|------|
| 已安装 Docker | 必须；推荐 **Docker Desktop**（Windows/macOS）或 **Docker Engine + Compose 插件**（Linux） |
| 保留项目结构 | 至少包含 `docker-compose.yml`、`Dockerfile`、`app/`、`web_pages/`、`shared/`、`server_new.py` 等，与仓库一致 |
| 首次构建会拉镜像 | 需能访问 Docker Hub（`python`、`mysql`、`prometheus`、`grafana` 等） |
| 网络与端口 | 本机 **5050、3307、9090、3000** 未被占用（见下文「默认端口」） |

**不需要**在新机器上单独安装 Python 虚拟环境来跑后端；镜像内会 `pip install` 依赖并启动服务。

可选：复制前可删除本机开发产生的目录以减小体积（**不是必须**）：

- `智能停送电/.venv/`、`__pycache__/`、`flask_session/`（会话文件，生产环境由容器内重新生成）

---

## 2. 环境要求

- **操作系统**：Windows 10/11（Docker Desktop）、常见 Linux 发行版、macOS（Docker Desktop）
- **内存**：建议 ≥ 4GB 可用内存（同时跑 MySQL、Flask、Prometheus、Grafana）
- **磁盘**：首次拉镜像与构建约需数 GB 空间

---

## 3. 安装步骤（新电脑）

### 3.1 安装 Docker

- **Windows / macOS**：安装并启动 [Docker Desktop](https://www.docker.com/products/docker-desktop/)，确保托盘图标显示为 **Running**。
- **Linux**：安装 Docker Engine 与 Compose 插件，并把当前用户加入 `docker` 组（或按需使用 `sudo`）。

### 3.2 复制项目

将整个 **`智能停送电`** 目录（或你仓库中的对应根目录，内含 `docker-compose.yml`）复制到目标电脑任意位置，例如：

- `D:\部署\智能停送电\`
- 或 Linux：`/opt/power-control/`

### 3.3（推荐）配置环境变量

1. 进入项目根目录（与 `docker-compose.yml` 同级）。
2. 复制示例文件并重命名：

   ```bash
   copy .env.example .env
   ```

   Linux/macOS：

   ```bash
   cp .env.example .env
   ```

3. 用文本编辑器编辑 **`.env`**，至少确认或修改：

   - `MYSQL_ROOT_PASSWORD`、`DB_PASSWORD`：数据库密码（需与 `docker-compose` 中引用一致）。
   - `SECRET_KEY`：生产环境请改为随机长字符串。
   - `MQTT_BROKER`、`MQTT_PORT`：若 MQTT 跑在**宿主机**，Windows/macOS 上常用 `host.docker.internal`（`docker-compose.yml` 里已有默认示例）。
   - `DEVICE_DATA_SOURCE`、`OPCUA_*`：若使用 OPC UA 采集现场信号，请按现场 KepServer/PLC 修改 `OPCUA_ENDPOINT`、节点列表、账号等。

> 说明：若未创建 `.env`，Compose 会使用 `docker-compose.yml` 里 `${VAR:-默认值}` 的默认值；生产环境**务必**用 `.env` 改掉默认密码与密钥。

### 3.4 启动服务

在项目根目录执行：

```bash
docker compose up -d --build
```

- 首次会**构建** `flask-backend` 镜像并**拉取** MySQL、Prometheus、Grafana 等镜像，可能需要几分钟。
- 仅重启后端（已构建过镜像时）可用：

  ```bash
  docker compose up -d --build flask-backend
  ```

### 3.5 查看运行状态

```bash
docker compose ps
docker logs power_backend --tail 50
```

`power_backend` 日志无持续 `Traceback`，且 `docker compose ps` 中各服务为 `Up` 即表示基本正常。

---

## 4. 默认端口与服务

| 服务 | 容器名 | 宿主机端口 | 说明 |
|------|--------|------------|------|
| Web / API | `power_backend` | **5050** | 浏览器访问：`http://本机IP:5050` |
| MySQL | `power_mysql` | **3307** → 容器 3306 | 外部工具连库时用 `3307` |
| Prometheus | `power_prometheus` | **9090** | 指标界面 |
| Grafana | `power_grafana` | **3000** | 默认账号见 `docker-compose.yml` 中 `GF_SECURITY_ADMIN_*` |

防火墙或云安全组需放行上述端口（按实际对外开放范围配置）。

---

## 5. 数据库说明

- 首次启动 **MySQL** 且数据卷为空时，会自动执行 `shared/database.sql` 初始化表结构。
- 数据保存在 Docker 卷 **`mysql_data`** 中；**删除卷会清空数据库**（升级或迁移前请备份）。

---

## 6. Windows 特别说明：项目路径含中文或过长

少数环境下 Docker 对**含中文或特殊字符的路径**映射不稳定。若出现构建失败、卷挂载异常，可将整个项目复制到**纯英文短路径**后再执行 `docker compose up`，例如：

`C:\deploy\power-control\`

---

## 7. 常见问题

**Q：执行 `docker compose up` 提示端口被占用？**  
A：修改 `docker-compose.yml` 中对应服务的 `ports` 左侧宿主机端口，或关闭占用该端口的程序。

**Q：后端一直重启？**  
A：执行 `docker logs power_backend` 查看报错；常见原因包括数据库未就绪、`.env` 与 `DB_*` 不一致、代码与镜像未同步（需在同一目录 `--build` 重建）。

**Q：MQTT / OPC UA 连不上现场设备？**  
A：确认容器内能访问目标 IP（桥接网络下 `host.docker.internal` 仅指向宿主机）；OPC UA 需检查 `OPCUA_ENDPOINT`、安全策略与证书是否与 KepServer 一致。

**Q：换电脑后想用原数据库数据？**  
A：需迁移 Docker 卷或使用 `mysqldump` 导出后在目标机导入；不建议只拷文件夹里的 `mysql_data` 除非你了解卷存储位置与版本兼容。

---

## 8. 停止与卸载

```bash
docker compose down
```

仅停止容器；数据卷仍保留。若需**删除命名卷**（会清空 MySQL 等持久化数据）：

```bash
docker compose down -v
```

---

## 9. 小结

1. 安装并启动 **Docker**。  
2. 复制**完整项目目录**到新电脑。  
3.（推荐）复制 `.env.example` 为 `.env` 并修改密码与业务相关配置。  
4. 在项目根目录执行 **`docker compose up -d --build`**。  
5. 浏览器访问 **`http://<服务器IP>:5050`**，按系统说明登录与使用。

按上述步骤即可完成「整包拷贝 + Docker 部署」；若你方有固定内网 IP、统一 MQTT/OPC 地址，可把 `.env` 模板预填好再分发，减少现场改配置时间。
