#!/bin/bash

echo "ICMP Ping 监控程序 - 图形界面版本"
echo "================================"
echo "正在检查权限..."
echo

# 检查是否以root权限运行
if [ "$EUID" -eq 0 ]; then
    echo "已获得root权限"
    echo "正在启动监控程序..."
    python3 gui_icmp_monitor.py
else
    echo "请求root权限..."
    sudo python3 gui_icmp_monitor.py
fi

echo
read -p "按回车键退出..."