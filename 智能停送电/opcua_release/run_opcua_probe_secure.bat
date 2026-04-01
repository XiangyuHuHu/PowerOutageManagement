@echo off
chcp 65001 >nul
REM ===== OPC UA secure test config =====
set OPCUA_ENDPOINT=opc.tcp://127.0.0.1:49320
set OPCUA_SECURITY_POLICY=Basic256Sha256
set OPCUA_SECURITY_MODE=SignAndEncrypt
set OPCUA_CERT=client_cert.der
set OPCUA_KEY=client_key.pem
REM Optional:
REM set OPCUA_SERVER_CERT=server_cert.der

echo Endpoint: %OPCUA_ENDPOINT%
echo Security: %OPCUA_SECURITY_POLICY%/%OPCUA_SECURITY_MODE%
opcua_probe_secure.exe
echo.
pause
