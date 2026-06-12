@echo off
chcp 65001 >nul
title slowbuild-backend
cd /d "%~dp0"

echo ==================================================
echo   slowbuild backend v1.0
echo ==================================================
echo.
echo [1/2] 安装依赖...
pip install -r requirements.txt --quiet
echo.
echo [2/2] 启动服务...
echo.
python server.py
pause
