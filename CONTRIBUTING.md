# 贡献指南

感谢您对ICMP监控项目的关注！我们欢迎各种形式的贡献。

## 如何贡献

### 报告Bug
- 确保您使用的是最新版本的代码
- 详细描述复现步骤
- 提供您的操作系统和Python版本信息
- 如果可能，提供错误日志或截图

### 提交功能请求
- 清晰描述您希望添加的功能
- 解释该功能的使用场景和价值
- 如果可能，提供实现思路

### 提交代码
1. Fork项目仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

## 开发环境设置

### 克隆仓库
```bash
git clone https://github.com/yourusername/icmp-monitor.git
cd icmp-monitor
```

### 安装依赖
```bash
pip install -r requirements.txt
```

### 运行程序
```bash
# 命令行版本
python icmp_monitor.py

# 图形界面版本（需要管理员权限）
python gui_icmp_monitor.py
```

## 代码规范

- 遵循PEP 8代码风格
- 添加适当的注释和文档字符串
- 确保代码兼容Python 3.6+
- 编写单元测试（如果适用）

## 测试

在提交代码前，请确保：

1. 程序能正常启动和运行
2. 没有引入新的错误或警告
3. 现有功能未被破坏

## 提问

如果您有任何问题，可以通过以下方式联系：

- 在GitHub Issues中提问
- 发送邮件至项目维护者邮箱

再次感谢您的贡献！