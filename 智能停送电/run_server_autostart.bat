@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist "logs" mkdir "logs"
python server_new.py 1>> "logs\autostart.log" 2>&1

