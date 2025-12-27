@echo off
chcp 65001 >nul
title 贵金属价差监控 - 数据自动更新

echo ============================================
echo   贵金属套利监控系统 - 数据自动更新
echo   每5分钟刷新一次数据
echo   按 Ctrl+C 停止
echo ============================================
echo.

:loop
echo [%date% %time%] 正在更新数据...
python generate_spread_v3.py

echo.
echo [%date% %time%] 更新完成，等待5分钟后下次刷新...
echo.

timeout /t 300 /nobreak >nul
goto loop
