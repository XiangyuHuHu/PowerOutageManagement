@echo off
chcp 65001 >nul
REM 始终在本 bat 所在目录生成 .env（无需手动 cd 路径）
cd /d "%~dp0"

(
echo DB_HOST=127.0.0.1
echo DB_PORT=3306
echo DB_USER=admin
echo DB_PASSWORD=admin
echo DB_NAME=power_control
) > ".env"

echo.
echo [完成] 已写入文件：
echo     %CD%\.env
echo.
echo 若 MySQL 账号不是 admin/admin，请用记事本打开 .env 修改后保存。
pause
