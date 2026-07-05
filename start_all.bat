@echo off
chcp 65001 >nul
echo ============================================
echo   slowbuild 服务启动
echo ============================================

:: 1. slowbuild 后端 (端口5000)
echo [1/5] slowbuild 后端...
start "slowbuild" /min cmd /c "cd /d C:\slowbuild && python server.py"
echo   OK

:: 2. 餐厅点单系统 (端口5001)
echo [2/5] 餐厅点单系统...
start "restaurant" /min cmd /c "cd /d C:\Users\方世聪\Desktop\restaurant-order\backend && python app.py"
echo   OK

:: 3. 音乐解读站 (端口5003)
echo [3/5] 音乐解读站...
start "music" /min cmd /c "cd /d C:\slowbuild\music-app && python app.py"
echo   OK

:: 等后端启动
echo [等待] 后端启动中 (15秒)...
timeout /t 15 /nobreak >nul

:: 4. cloudflared 隧道
echo [4/5] cloudflared 隧道...
start "cloudflared" /min cmd /c "cd /d C:\slowbuild && cloudflared tunnel run slowbuild"
echo   OK

echo ============================================
echo   全部启动完毕
echo   slowbuild.top         - 端口5000
echo   order.slowbuild.top   - 端口5001
echo   music.slowbuild.top   - 端口5003
echo ============================================
timeout /t 3 >nul
