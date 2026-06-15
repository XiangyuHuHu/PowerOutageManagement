@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

echo ========================================
echo   智能停送电 - 本机运行（无 Docker）
echo ========================================
echo.

where python >nul 2>&1
if errorlevel 1 (
  echo [错误] 未在 PATH 中找到 python，请先安装 Python 3.11+ 并勾选「Add to PATH」。
  pause
  exit /b 1
)

echo [1/2] 安装/更新依赖 ^(shared\requirements.txt^) ...
python -m pip install -r "shared\requirements.txt"
if errorlevel 1 (
  echo [错误] pip 安装失败。
  pause
  exit /b 1
)

echo [2/2] 启动服务 ^(按 Ctrl+C 可停止^) ...
echo.
echo 提示：本机 MySQL 时请在项目目录复制 .env.example 为 .env ，并将 DB_HOST 改为 127.0.0.1 （不要用 docker 里的 mysql）。
echo 浏览器访问: http://127.0.0.1:5050  或  http://本机IP:5050
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "& { Set-Location -LiteralPath '%CD%'; $f = Join-Path (Get-Location) '.env'; if (Test-Path -LiteralPath $f) { Get-Content -LiteralPath $f -Encoding UTF8 | ForEach-Object { $line = $_.Trim(); if ($line -ne '' -and -not $line.StartsWith('#')) { $i = $line.IndexOf('='); if ($i -gt 0) { $k = $line.Substring(0, $i).Trim(); $v = $line.Substring($i + 1).Trim(); [Environment]::SetEnvironmentVariable($k, $v, 'Process') } } } } else { Write-Host '[提示] 未找到 .env，使用程序内置默认数据库连接（见 app\database.py）。' -ForegroundColor Yellow }; python server_new.py }"

set ERR=%ERRORLEVEL%
echo.
if %ERR% neq 0 echo [进程已退出，代码 %ERR%]
pause
exit /b %ERR%
