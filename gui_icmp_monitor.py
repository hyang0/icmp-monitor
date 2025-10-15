#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ICMP Ping 监控程序 - 图形界面版本
使用PyQt5创建图形界面，实时显示ping本机的IP地址和状态
"""

import sys
import time
from collections import defaultdict
from datetime import datetime
from threading import Thread

try:
    # 动态导入PyQt5模块
    import importlib
    QtWidgets = importlib.import_module('PyQt5.QtWidgets')
    QtCore = importlib.import_module('PyQt5.QtCore')
    QtGui = importlib.import_module('PyQt5.QtGui')
    
    # 获取PyQt5类
    QApplication = getattr(QtWidgets, 'QApplication')
    QMainWindow = getattr(QtWidgets, 'QMainWindow')
    QWidget = getattr(QtWidgets, 'QWidget')
    QVBoxLayout = getattr(QtWidgets, 'QVBoxLayout')
    QHBoxLayout = getattr(QtWidgets, 'QHBoxLayout')
    QLabel = getattr(QtWidgets, 'QLabel')
    QPushButton = getattr(QtWidgets, 'QPushButton')
    QTableWidget = getattr(QtWidgets, 'QTableWidget')
    QTableWidgetItem = getattr(QtWidgets, 'QTableWidgetItem')
    QHeaderView = getattr(QtWidgets, 'QHeaderView')
    QStatusBar = getattr(QtWidgets, 'QStatusBar')
    QTextEdit = getattr(QtWidgets, 'QTextEdit')
    
    Qt = getattr(QtCore, 'Qt')
    QTimer = getattr(QtCore, 'QTimer')
    pyqtSignal = getattr(QtCore, 'pyqtSignal')
    QObject = getattr(QtCore, 'QObject')
    
    QColor = getattr(QtGui, 'QColor')
    QFont = getattr(QtGui, 'QFont')
    
    # 尝试导入Scapy
    scapy_all = importlib.import_module('scapy.all')
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
            L3RawSocket = None
    
    SCAPY_AVAILABLE = all([sniff, ICMP, IP, conf])
    
except ImportError as e:
    print(f"导入模块失败: {e}")
    sys.exit(1)


class ICMPWorker(QObject):
    """处理ICMP包嗅探的后台工作线程"""
    # 定义信号
    new_ping_signal = pyqtSignal(str, float)  # IP, timestamp
    update_ping_signal = pyqtSignal(str, float)  # IP, timestamp
    stop_ping_signal = pyqtSignal(str, float)  # IP, timestamp
    error_signal = pyqtSignal(str)  # 错误信息
    
    def __init__(self):
        super().__init__()
        self.ping_records = defaultdict(dict)
        self.last_update = defaultdict(float)
        self.active_ips = set()
        self.is_running = False
        
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
                    self.new_ping_signal.emit(src_ip, timestamp)
                else:
                    # 更新最后活动时间
                    self.ping_records[src_ip]['last_time'] = timestamp
                    self.update_ping_signal.emit(src_ip, timestamp)
                    
                # 更新活跃状态
                self.last_update[src_ip] = timestamp
                self.active_ips.add(src_ip)
    
    def check_inactive_ips(self):
        """检查不活跃的IP并更新状态"""
        if not self.is_running:
            return
            
        current_time = time.time()
        inactive_ips = []
        
        # 检查超过3秒没有活动的IP
        for ip in self.active_ips:
            if current_time - self.last_update[ip] > 3:
                inactive_ips.append(ip)
                
        # 移除不活跃的IP并发送停止信号
        for ip in inactive_ips:
            self.active_ips.discard(ip)
            last_time = self.last_update[ip]
            self.stop_ping_signal.emit(ip, last_time)
    
    def start_sniffing(self):
        """开始嗅探ICMP包"""
        if not SCAPY_AVAILABLE:
            self.error_signal.emit("Scapy库不可用，请安装Scapy库")
            return
            
        self.is_running = True
        try:
            # 配置使用L3socket避免需要winpcap
            if L3RawSocket and conf:
                conf.L3socket = L3RawSocket
            
            # 在后台线程中定期检查不活跃的IP
            checker_thread = Thread(target=self._check_loop, daemon=True)
            checker_thread.start()
            
            # 开始嗅探ICMP包
            if sniff:
                sniff(filter="icmp", prn=self.packet_handler, store=0)
        except PermissionError:
            self.error_signal.emit("权限错误：需要管理员权限来捕获数据包，请以管理员身份运行此程序")
        except Exception as e:
            error_msg = str(e)
            if "winpcap is not installed" in error_msg:
                self.error_signal.emit("需要安装npcap或winpcap来捕获数据包，请访问https://nmap.org/npcap/下载安装")
            else:
                self.error_signal.emit(f"发生错误: {error_msg}")
            
    def _check_loop(self):
        """定期检查不活跃IP的循环"""
        while self.is_running:
            time.sleep(1)
            self.check_inactive_ips()
    
    def stop_sniffing(self):
        """停止嗅探"""
        self.is_running = False


class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ICMP Ping 监控程序")
        self.setGeometry(100, 100, 800, 600)
        
        # 初始化UI
        self.init_ui()
        
        # 初始化ICMP工作线程
        self.icmp_worker = ICMPWorker()
        self.icmp_thread = None
        
        # 连接信号
        self.icmp_worker.new_ping_signal.connect(self.on_new_ping)
        self.icmp_worker.update_ping_signal.connect(self.on_update_ping)
        self.icmp_worker.stop_ping_signal.connect(self.on_stop_ping)
        self.icmp_worker.error_signal.connect(self.on_error)
        
        # 设置定时器定期清理过期记录
        self.cleanup_timer = QTimer()
        self.cleanup_timer.timeout.connect(self.cleanup_old_records)
        self.cleanup_timer.start(10000)  # 每10秒检查一次
        
        # 存储IP记录信息
        self.ip_records = {}  # {ip: {start_time, last_time, status}}
        
    def init_ui(self):
        """初始化用户界面"""
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建布局
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # 创建标题
        title_label = QLabel("ICMP Ping 监控")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 创建控制按钮布局
        button_layout = QHBoxLayout()
        
        self.start_button = QPushButton("开始监控")
        self.start_button.clicked.connect(self.start_monitoring)
        button_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("停止监控")
        self.stop_button.clicked.connect(self.stop_monitoring)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)
        
        self.clear_button = QPushButton("清空记录")
        self.clear_button.clicked.connect(self.clear_records)
        button_layout.addWidget(self.clear_button)
        
        button_layout.addStretch()
        main_layout.addLayout(button_layout)
        
        # 创建表格显示IP记录
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["IP地址", "开始时间", "最后活动时间", "状态"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        main_layout.addWidget(self.table)
        
        # 创建状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("准备就绪")
        
        # 创建日志输出区域
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(100)
        self.log_text.setReadOnly(True)
        main_layout.addWidget(self.log_text)
        
    def start_monitoring(self):
        """开始监控"""
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.status_bar.showMessage("正在启动监控...")
        
        # 在后台线程中启动嗅探
        self.icmp_thread = Thread(target=self.icmp_worker.start_sniffing, daemon=True)
        self.icmp_thread.start()
        
        self.log_message("开始监控ICMP ping请求...")
        
    def stop_monitoring(self):
        """停止监控"""
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.status_bar.showMessage("正在停止监控...")
        
        self.icmp_worker.stop_sniffing()
        self.log_message("监控已停止")
        self.status_bar.showMessage("监控已停止")
        
    def clear_records(self):
        """清空记录"""
        self.table.setRowCount(0)
        self.ip_records.clear()
        self.log_message("记录已清空")
        
    def on_new_ping(self, ip, timestamp):
        """处理新ping事件"""
        # 更新记录
        self.ip_records[ip] = {
            'start_time': timestamp,
            'last_time': timestamp,
            'status': 'pinging'
        }
        
        # 更新UI
        self.update_table()
        self.log_message(f"[{datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')}] {ip} 开始ping本机")
        self.status_bar.showMessage(f"检测到新的ping请求: {ip}")
        
    def on_update_ping(self, ip, timestamp):
        """处理ping更新事件"""
        if ip in self.ip_records:
            self.ip_records[ip]['last_time'] = timestamp
            self.ip_records[ip]['status'] = 'pinging'
            
            # 更新UI
            self.update_table()
            
    def on_stop_ping(self, ip, timestamp):
        """处理停止ping事件"""
        if ip in self.ip_records:
            self.ip_records[ip]['last_time'] = timestamp
            self.ip_records[ip]['status'] = 'stopped'
            
            # 更新UI
            self.update_table()
            self.log_message(f"[{datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')}] {ip} 停止ping本机")
            self.status_bar.showMessage(f"检测到停止ping: {ip}")
            
    def on_error(self, error_msg):
        """处理错误信息"""
        self.log_message(f"错误: {error_msg}")
        self.status_bar.showMessage(f"错误: {error_msg}")
        
    def update_table(self):
        """更新表格显示"""
        # 清空表格
        self.table.setRowCount(0)
        self.table.setRowCount(len(self.ip_records))
        
        # 填充数据
        row = 0
        for ip, record in self.ip_records.items():
            # IP地址
            ip_item = QTableWidgetItem(ip)
            self.table.setItem(row, 0, ip_item)
            
            # 开始时间
            start_time = datetime.fromtimestamp(record['start_time']).strftime('%Y-%m-%d %H:%M:%S')
            start_item = QTableWidgetItem(start_time)
            self.table.setItem(row, 1, start_item)
            
            # 最后活动时间
            last_time = datetime.fromtimestamp(record['last_time']).strftime('%Y-%m-%d %H:%M:%S')
            last_item = QTableWidgetItem(last_time)
            self.table.setItem(row, 2, last_item)
            
            # 状态
            status = record['status']
            status_item = QTableWidgetItem(status)
            if status == 'pinging':
                status_item.setBackground(QColor(144, 238, 144))  # 浅绿色
                status_item.setText("正在Ping")
            else:
                status_item.setBackground(QColor(255, 182, 193))  # 浅红色
                status_item.setText("已停止")
            self.table.setItem(row, 3, status_item)
            
            row += 1
            
        # 根据IP地址排序（按数字排序而非字符串排序）
        if len(self.ip_records) > 1:
            self._sort_table_by_ip()
        
    def _sort_table_by_ip(self):
        """根据IP地址进行数字排序"""
        try:
            # 获取所有行数据
            rows = []
            for row in range(self.table.rowCount()):
                ip_item = self.table.item(row, 0)
                if ip_item:
                    rows.append((ip_item.text(), row))
            
            # 按IP地址数字排序
            def ip_to_tuple(ip):
                try:
                    return tuple(int(i) for i in ip.split('.'))
                except:
                    return (0, 0, 0, 0)
            
            rows.sort(key=lambda x: ip_to_tuple(x[0]))
            
            # 保存当前表格的所有数据
            table_data = []
            for original_row in range(self.table.rowCount()):
                row_data = []
                for col in range(self.table.columnCount()):
                    item = self.table.item(original_row, col)
                    if item:
                        # 保存项目的文本、背景色和显示文本
                        row_data.append({
                            'text': item.text(),
                            'background': item.background(),
                            'display_text': item.text()
                        })
                    else:
                        row_data.append({
                            'text': '',
                            'background': None,
                            'display_text': ''
                        })
                table_data.append(row_data)
            
            # 按排序后的顺序重新排列数据
            sorted_data = []
            for ip, original_row in rows:
                sorted_data.append(table_data[original_row])
            
            # 重新填充表格
            for i, row_data in enumerate(sorted_data):
                for col, item_data in enumerate(row_data):
                    item = QTableWidgetItem(item_data['text'])
                    if item_data['background']:
                        item.setBackground(item_data['background'])
                    if item_data['display_text'] and item_data['display_text'] != item_data['text']:
                        item.setText(item_data['display_text'])
                    self.table.setItem(i, col, item)
        except Exception as e:
            # 如果排序出错，至少保持原有数据显示
            pass
    
    def log_message(self, message):
        """添加日志消息"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.log_text.append(f"[{timestamp}] {message}")
        # 滚动到底部
        self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())
        
    def cleanup_old_records(self):
        """清理过期记录（超过1小时没有活动的记录）"""
        current_time = time.time()
        expired_ips = []
        
        for ip, record in self.ip_records.items():
            if current_time - record['last_time'] > 3600:  # 1小时
                expired_ips.append(ip)
                
        for ip in expired_ips:
            del self.ip_records[ip]
            
        if expired_ips:
            self.update_table()
            self.log_message(f"已清理 {len(expired_ips)} 条过期记录")
            
    def closeEvent(self, event):
        """窗口关闭事件"""
        self.icmp_worker.stop_sniffing()
        event.accept()


def main():
    app = QApplication(sys.argv)
    
    # 设置应用程序样式
    app.setStyle('Fusion')
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()