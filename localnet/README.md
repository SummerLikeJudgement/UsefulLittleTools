# 局域网设备扫描工具
一个用于扫描局域网内在线设备的 Python GUI 工具，支持自动扫描、设备列表管理、自定义扫描间隔等功能。

## 功能特性
- 📡 自动扫描局域网中的所有在线设备
- 📋 显示设备IP地址、MAC地址、主机名
- ⏰ 记录设备首次发现和最后在线时间
- ⚙️ 支持自定义扫描间隔（2-60秒）
- 🎨 深色主题界面

## 快速开始

### 1. 安装依赖
```bash
pip install scapy pyqt5 python-dotenv
```

### 2. 配置环境变量
复制 `.env.example` 为 `.env`，修改以下配置：

```env
# 网络接口名称
NETWORK_INTERFACE=Realtek 8852CE WiFi 6E PCI-E NIC

# 扫描网段（CIDR格式）
SCAN_NETWORK=192.168.1.0/24

# 扫描间隔（秒）
SCAN_INTERVAL=10

# 扫描超时（秒）
SCAN_TIMEOUT=3
```

**网络接口名称获取方法：**

- **Windows**: 打开命令提示符，输入 `ipconfig /all`，找到适配器名称
- **Linux**: 输入 `ip link show`，查看接口名称（如 eth0, wlan0）
- **macOS**: 输入 `ifconfig`，查看接口名称（如 en0, en1）

### 3. 运行
```bash
python ipscan.py
```

## 使用说明

### 快捷键
- `F5`: 立即手动扫描
- `Ctrl+Q`: 安全退出

### 菜单功能
- **控制 > 立即扫描**: 手动触发一次扫描
- **控制 > 清空列表**: 清空当前设备列表
- **控制 > 退出**: 安全退出程序
- **设置 > 扫描间隔设置**: 调整自动扫描间隔
- **设置 > 关于**: 查看软件信息

## 注意事项
- 需要管理员权限才能进行ARP扫描
- 首次运行可能需要等待几秒才能看到设备
- 建议将扫描间隔设置为10-30秒，避免网络负载过大
- 设备名称解析可能需要几秒时间

## 技术依赖
- Python 3.x
- Scapy - ARP协议扫描
- PyQt5 - GUI界面
- python-dotenv - 环境变量管理

## 开发说明

### 主要类结构
- `ScanThread`: 扫描线程，负责执行ARP扫描
- `DeviceCard`: 设备卡片组件，展示单个设备信息
- `DeviceListWidget`: 设备列表组件，管理所有设备卡片
- `MainWindow`: 主窗口，整合所有功能

### 扫描原理
使用ARP协议向局域网发送广播包，接收响应的设备即为在线设备。通过 `socket.gethostbyaddr()` 尝试解析设备主机名。

## 许可证
MIT License