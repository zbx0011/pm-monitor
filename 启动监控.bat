@echo off
echo ========================================
echo  铂钯跨市场套利监控 - 启动中...
echo ========================================
cd /d "e:\项目\币圈等监控系统"

echo 启动自动数据刷新服务 (每10分钟更新)...
start /min python auto_refresh_service.py

echo 启动API服务器...
start python price_api_server.py

timeout /t 3 /nobreak > nul
echo 打开监控页面...
start http://localhost:8080/precious_metals_monitor.html

echo.
echo ========================================
echo  服务已启动！
echo  - 自动刷新服务: 每10分钟更新分钟级数据
echo  - 前端页面: 每60秒刷新显示
echo  - 关闭此窗口将停止所有服务
echo ========================================
pause
