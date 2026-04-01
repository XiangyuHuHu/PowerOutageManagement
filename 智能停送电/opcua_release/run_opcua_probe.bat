@echo off
chcp 65001 >nul
set OPCUA_ENDPOINT=opc.tcp://127.0.0.1:49320
opcua_probe.exe
echo.
pause
