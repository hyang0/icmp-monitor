#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简化的ICMP监控程序
在没有完整的Scapy支持或管理员权限的情况下提供基本功能
"""

import sys
import time
import subprocess
import re
from datetime import datetime

def parse_ping_output(output):
    """解析ping命令的输出，提取IP地址"""
    # 匹配IPv4地址的正则表达式
    ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
    ips = re.findall(ip_pattern, output)
    return ips

def monitor_with_ping():
    """使用ping命令监控网络活动"""
    print("简化的ICMP监控程序")
    print("==================")
    print("注意: 此版本功能有限，仅能检测部分ping活动")
    print("建议使用完整版本icmp_monitor.py获得更好的体验")
    print()
    print("开始监控... 按 Ctrl+C 停止")
    
    # 存储已知的ping源IP
    known_ips = set()
    
    try:
        while True:
            # 在Windows上使用netstat查看网络连接
            try:
                result = subprocess.run(['netstat', '-n'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    # 查找ICMP相关的连接
                    lines = result.stdout.split('\n')
                    current_ips = set()
                    
                    for line in lines:
                        if 'icmp' in line.lower() or 'ICMP' in line:
                            # 提取IP地址
                            ips = parse_ping_output(line)
                            for ip in ips:
                                # 排除本地地址
                                if not ip.startswith('127.') and ':' not in ip:
                                    current_ips.add(ip)
                                    if ip not in known_ips:
                                        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {ip} 正在ping本机")
                    
                    # 检查是否有IP停止ping
                    stopped_ips = known_ips - current_ips
                    for ip in stopped_ips:
                        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {ip} 停止ping本机")
                    
                    known_ips = current_ips
                    
            except subprocess.TimeoutExpired:
                pass
            except Exception as e:
                pass
            
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\n监控已停止")

def main():
    print("ICMP监控程序 - 简化版")
    print("====================")
    monitor_with_ping()

if __name__ == "__main__":
    main()