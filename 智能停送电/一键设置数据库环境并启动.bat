@echo off
chcp 65001 >nul
cd /d "%~dp0"

REM =============================================================================
REM 不依赖 .env 文件：直接在终端里设置 MySQL 连接（本机 admin/admin 示例）
REM 若你的账号不同，请改下面四行 set 后再运行本 bat。
REM =============================================================================
set DB_HOST=127.0.0.1
set DB_PORT=3306
set DB_USER=admin
set DB_PASSWORD=admin
set DB_NAME=power_control

echo 当前数据库环境（可在本 bat 内修改）：
echo   DB_HOST=%DB_HOST%  DB_USER=%DB_USER%  DB_NAME=%DB_NAME%
echo.

where python >nul 2>&1
if errorlevel 1 (
  echo [错误] 未找到 python
  pause
  exit /b 1
)

python -m pip install -q -r "shared\requirements.txt"
echo 正在启动...
python server_new.py
pause
