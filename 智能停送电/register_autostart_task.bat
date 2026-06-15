@echo off
chcp 65001 >nul
cd /d "%~dp0"
set TN=PowerOutageWeb5050
set TR=%~dp0run_server_autostart.bat
echo Task: %TN%
echo Script: %TR%
schtasks /Query /TN "%TN%" >nul 2>&1
if %errorlevel%==0 schtasks /Delete /TN "%TN%" /F
schtasks /Create /TN "%TN%" /TR "\"%TR%\"" /SC ONLOGON /RL HIGHEST /F
if errorlevel 1 (
  echo FAILED. Run this bat as Administrator.
  pause
  exit /b 1
)
echo OK. Log: %~dp0logs\autostart.log
echo Uninstall: schtasks /Delete /TN "%TN%" /F
pause
