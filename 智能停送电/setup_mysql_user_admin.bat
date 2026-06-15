@echo off
chcp 65001 >nul
REM 一键：创建 MySQL 用户 admin / admin，并授权 power_control 库（本机 localhost）
REM 用法：双击运行，或 cmd 里执行；会提示输入 root 密码一次

set MYSQL_BIN=C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe
if not exist "%MYSQL_BIN%" (
  echo [错误] 未找到 %MYSQL_BIN%
  echo 请编辑本 bat，把 MYSQL_BIN 改成你机器上 mysql.exe 的路径。
  pause
  exit /b 1
)

echo 即将执行（需输入 MySQL root 密码）：
echo   创建用户 admin@localhost ，密码 admin
echo   授予 power_control 库全部权限
echo.
"%MYSQL_BIN%" -u root -p -e "CREATE USER IF NOT EXISTS 'admin'@'localhost' IDENTIFIED BY 'admin'; GRANT ALL PRIVILEGES ON power_control.* TO 'admin'@'localhost'; FLUSH PRIVILEGES;"
if errorlevel 1 (
  echo.
  echo [失败] 若提示用户已存在，可改用下面语句（先登录 mysql 后执行）：
  echo   ALTER USER 'admin'@'localhost' IDENTIFIED BY 'admin';
  pause
  exit /b 1
)
echo.
echo [成功] 请在项目目录的 .env 中设置：
echo   DB_USER=admin
echo   DB_PASSWORD=admin
echo   DB_HOST=127.0.0.1
echo   DB_NAME=power_control
pause
