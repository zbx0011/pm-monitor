@echo off
chcp 65001 >nul
echo ========================================
echo  铂钯跨市场套利监控 - 启动中...
echo ========================================
cd /d "e:\项目\币圈等监控系统"

echo 启动API服务器与自动更新服务 (每2分钟)...
start python price_api_server.py

timeout /t 3 /nobreak > nul
echo 打开监控页面...
start http://localhost:8080/precious_metals_monitor.html

echo.
echo ========================================
echo  服务已启动！
echo  - 后台服务: http://localhost:8080 (含自动更新)
echo  - 监控页面: http://localhost:8080/precious_metals_monitor.html
echo  - 关闭此窗口将停止所有服务
echo ========================================
pause
