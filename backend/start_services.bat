@echo off
REM === slowbuild 全服务启动 ===
REM 放到 shell:startup 自动启动
REM 需要 Python 3.12 + pip install flask flask-cors

echo ================================
echo   slowbuild All Services
echo ================================

cd /d C:\slowbuild\backend

echo.
echo [1/2] Starting main server (port 5000)...
start "slowbuild-main" cmd /c "python server.py"

echo [2/2] Starting order server (port 5002)...
start "slowbuild-order" cmd /c "python order_server.py"

echo.
echo Both servers started!
echo   Main:   http://localhost:5000
echo   Orders: http://localhost:5002
echo.
pause
