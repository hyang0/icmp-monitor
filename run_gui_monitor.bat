@echo off
echo ICMP Ping 监控程序 - 图形界面版本
echo ================================
echo 正在以管理员权限启动程序...
echo.

REM 检查是否以管理员权限运行
net session >nul 2>&1
if %errorLevel% == 0 (
    echo 已获得管理员权限
    echo 正在启动监控程序...
    python gui_icmp_monitor.py
) else (
    echo 请求管理员权限...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

pause