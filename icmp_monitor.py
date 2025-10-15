import sys
import time
from collections import defaultdict
from datetime import datetime
import os
import platform
import io

def change_default_encoding():
    """判断是否在 windows git-bash 下运行，是则使用 utf-8 编码"""
    if platform.system() == 'Windows':
        terminal = os.environ.get('TERM')
        if terminal and 'xterm' in terminal:
            sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')



# 初始化Scapy相关变量
sniff = None
ICMP = None
IP = None
conf = None
L3RawSocket = None
SCAPY_AVAILABLE = False

# 尝试导入Scapy模块
try:
    import importlib
    scapy_all = importlib.import_module('scapy.all')
    # 使用getattr安全地获取模块属性
    sniff = getattr(scapy_all, 'sniff', None)
    ICMP = getattr(scapy_all, 'ICMP', None)
    IP = getattr(scapy_all, 'IP', None)
    conf = getattr(scapy_all, 'conf', None)
    
    # 尝试导入L3RawSocket
    try:
        scapy_arch = importlib.import_module('scapy.arch')
        L3RawSocket = getattr(scapy_arch, 'L3RawSocket', None)
    except ImportError:
        try:
            scapy_supersocket = importlib.import_module('scapy.supersocket')
            L3RawSocket = getattr(scapy_supersocket, 'L3RawSocket', None)
        except ImportError:
            pass
    
    SCAPY_AVAILABLE = all([sniff, ICMP, IP, conf])
except ImportError:
    print("警告: Scapy未安装或不可用，将使用基本模式运行")

class ICMPPingMonitor:
    def __init__(self):
        # 存储每个IP的ping信息
        self.ping_records = defaultdict(dict)
        # 记录上次更新时间，用于检测ping是否停止
        self.last_update = defaultdict(float)
        # 存储活跃的IP列表
        self.active_ips = set()
        
    def packet_handler(self, packet):
        """处理捕获到的数据包"""
        if SCAPY_AVAILABLE and ICMP and IP and packet.haslayer(ICMP) and packet.haslayer(IP):
            # 只处理ICMP Echo Request (type=8)
            if packet[ICMP].type == 8:
                src_ip = packet[IP].src
                timestamp = time.time()
                
                # 如果是第一次看到这个IP
                if src_ip not in self.ping_records:
                    self.ping_records[src_ip]['start_time'] = timestamp
                    sys.stdout.flush()
                    print(f"[{datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')}] {src_ip} 开始ping本机")
                else:
                    # 更新最后活动时间
                    self.ping_records[src_ip]['last_time'] = timestamp
                    
                # 更新活跃状态
                self.last_update[src_ip] = timestamp
                self.active_ips.add(src_ip)
                
    def check_inactive_ips(self):
        """检查不活跃的IP并更新状态"""
        current_time = time.time()
        inactive_ips = []
        
        # 检查超过3秒没有活动的IP
        for ip in self.active_ips:
            if current_time - self.last_update[ip] > 3:
                inactive_ips.append(ip)
                
        # 移除不活跃的IP并打印停止信息
        for ip in inactive_ips:
            self.active_ips.discard(ip)
            last_time = self.last_update[ip]
            sys.stdout.flush()
            print(f"[{datetime.fromtimestamp(last_time).strftime('%Y-%m-%d %H:%M:%S')}] {ip} 停止ping本机")
            
    def start_monitoring(self):
        """开始监控ICMP包"""
        if not SCAPY_AVAILABLE:
            print("错误: 需要安装Scapy库来监控ICMP包")
            print("请运行 'pip install scapy' 安装Scapy")
            return
            
        print("开始监控ICMP ping请求...")
        print("按 Ctrl+C 停止监控")
        
        try:
            # 在后台线程中定期检查不活跃的IP
            import threading
            def check_inactive():
                while True:
                    time.sleep(1)
                    self.check_inactive_ips()
                    
            checker_thread = threading.Thread(target=check_inactive, daemon=True)
            checker_thread.start()
            
            # 配置使用L3socket避免需要winpcap
            if L3RawSocket and conf:
                conf.L3socket = L3RawSocket
            
            # 开始嗅探ICMP包
            if sniff:
                sniff(filter="icmp", prn=self.packet_handler, store=0)
            
        except KeyboardInterrupt:
            print("\n监控已停止")
        except PermissionError:
            print("错误: 需要管理员权限来捕获数据包")
            print("请以管理员身份运行此程序")
        except Exception as e:
            print(f"发生错误: {e}")
            print("请确保以管理员身份运行此程序")

def main():
    print("ICMP Ping 监控程序")
    print("=====================")
    print("功能说明:")
    print("1. 监控所有对本机的ICMP Echo请求(ping)")
    print("2. 显示开始ping的IP地址和时间")
    print("3. 当IP停止ping时显示停止时间")
    print("4. 实时显示ping状态")
    print()
    print("使用说明:")
    print("- 需要以管理员权限运行此程序")
    print("- 需要安装Scapy库 (pip install scapy)")
    print("- 按 Ctrl+C 停止监控")
    print()
    
    monitor = ICMPPingMonitor()
    monitor.start_monitoring()

if __name__ == "__main__":
    change_default_encoding()
    main()