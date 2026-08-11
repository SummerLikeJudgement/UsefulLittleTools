import sys
import socket
import datetime
import json
import threading
import time
import os
from dotenv import load_dotenv
from scapy.all import ARP, Ether, srp, conf
from PyQt5 import QtWidgets, QtCore, QtGui

DARK_QSS = """
*{background:#121212;color:#dcdcdc;font-family:"Segoe UI",Roboto,sans-serif;font-size:10.5pt}
QMenuBar{background:#202020}
QMenuBar::item{padding:4px 12px}
QMenuBar::item:selected{background:#2a2a2a}
QLabel[columnTitle=true]{font-size:12pt;font-weight:600;color:#f0f0f0;padding:4px}
QFrame[class=deviceCard]{background:#1e1e1e;border:1px solid #353535;border-radius:8px;padding:6px}
QFrame[class=deviceCard]:hover{background:#282828;border-color:#4a90e2}
QLabel.title{color:#eaeaea;font-weight:600}
QLabel.subtitle{color:#a0a0a0;font-size:9pt}
QLabel.indexLbl{color:#fff;background:#4a90e2;padding:1px 4px;border-radius:4px;min-width:22px;max-width:22px;qproperty-alignment:AlignCenter;font-size:8pt}
QScrollBar:vertical{background:#1a1a1a;width:10px;margin:0}
QScrollBar::handle:vertical{background:#3c3c3c;min-height:20px;border-radius:4px}
QScrollBar::handle:vertical:hover{background:#4a90e2}
QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0}
QScrollBar::add-page:vertical,QScrollBar::sub-page:vertical{background:0 0}
QPushButton{background:#2a2a2a;border:1px solid #3c3c3c;border-radius:4px;padding:6px 12px}
QPushButton:hover{background:#3c3c3c;border-color:#4a90e2}
QPushButton:pressed{background:#1e1e1e}
"""

conf.verb = 0


class ScanThread(QtCore.QThread):
    """设备扫描线程"""
    device_found = QtCore.pyqtSignal(dict)
    scan_finished = QtCore.pyqtSignal()

    def __init__(self, iface, network, interval=10):
        super().__init__()
        self.iface = iface
        self.network = network
        self.interval = interval  # 扫描间隔（秒）
        self._running = True
        self.first_seen = {}
        self.devices = {}  # 存储所有发现的设备

    def run(self):
        while self._running:
            try:
                # 执行ARP扫描
                ans, _ = srp(
                    Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=self.network),
                    iface=self.iface, timeout=3, verbose=False
                )

                ts = datetime.datetime.now()
                current_ips = set()

                # 处理扫描结果
                for _, r in ans:
                    ip, mac = r.psrc, r.src
                    current_ips.add(ip)

                    try:
                        name = socket.gethostbyaddr(ip)[0]
                    except (socket.herror, socket.gaierror):
                        name = ip

                    # 记录首次发现时间
                    if ip not in self.first_seen:
                        self.first_seen[ip] = ts

                    device_info = {
                        "ip": ip,
                        "mac": mac,
                        "name": name,
                        "first_seen": self.first_seen[ip].isoformat(sep=" ", timespec="seconds"),
                        "last_seen": ts.isoformat(sep=" ", timespec="seconds"),
                        "interface": self.iface,
                    }

                    # 更新设备信息
                    self.devices[ip] = device_info
                    self.device_found.emit(device_info)

                # 标记离线设备（可选功能）
                # 这里只更新在线设备，不下线已离线设备

                self.scan_finished.emit()

            except Exception as e:
                print(f"[扫描错误] {e}")

            # 等待下一次扫描
            for _ in range(self.interval * 10):
                if not self._running:
                    break
                self.msleep(100)

    def stop(self):
        """停止扫描线程"""
        self._running = False
        self.requestInterruption()
        self.quit()
        self.wait()


class DeviceCard(QtWidgets.QFrame):
    """设备卡片组件"""

    def __init__(self, info: dict, index: int):
        super().__init__()
        self.info = info
        self.setProperty("class", "deviceCard")

        h = QtWidgets.QHBoxLayout(self)
        h.setContentsMargins(6, 4, 6, 4)
        h.setSpacing(8)

        # 序号标签
        self.idx_lbl = QtWidgets.QLabel(str(index))
        self.idx_lbl.setProperty("class", "indexLbl")
        h.addWidget(self.idx_lbl)

        # 设备信息
        v = QtWidgets.QVBoxLayout()
        v.setSpacing(2)

        self.name_lbl = QtWidgets.QLabel(info["name"])
        self.name_lbl.setProperty("class", "title")

        self.ip_lbl = QtWidgets.QLabel(info["ip"])
        self.ip_lbl.setProperty("class", "subtitle")

        self.mac_lbl = QtWidgets.QLabel(f"MAC: {info['mac']}")
        self.mac_lbl.setProperty("class", "subtitle")
        self.mac_lbl.setStyleSheet("font-size:8pt; color:#808080")

        v.addWidget(self.name_lbl)
        v.addWidget(self.ip_lbl)
        v.addWidget(self.mac_lbl)
        h.addLayout(v)

        h.addStretch()

        # 首次发现时间标签（可选）
        self.first_seen_lbl = QtWidgets.QLabel("首次发现")
        self.first_seen_lbl.setProperty("class", "subtitle")
        self.first_seen_lbl.setStyleSheet("font-size:8pt; color:#606060")
        h.addWidget(self.first_seen_lbl)

        self.setToolTip(self._tt())
        self.update_time_display()

    def _tt(self):
        """生成工具提示文本"""
        i = self.info
        return (f"<b>{i['name']}</b><br>"
                f"IP地址: {i['ip']}<br>"
                f"MAC地址: {i['mac']}<br>"
                f"首次发现: {i['first_seen']}<br>"
                f"最后在线: {i['last_seen']}<br>"
                f"网络接口: {i['interface']}")

    def update_info(self, info):
        """更新设备信息"""
        self.info = info
        self.name_lbl.setText(info["name"])
        self.ip_lbl.setText(info["ip"])
        self.mac_lbl.setText(f"MAC: {info['mac']}")
        self.setToolTip(self._tt())
        self.update_time_display()

    def update_time_display(self):
        """更新时间显示"""
        # 计算在线时长（简化显示）
        try:
            first = datetime.datetime.fromisoformat(self.info['first_seen'])
            last = datetime.datetime.fromisoformat(self.info['last_seen'])
            duration = last - first

            if duration.total_seconds() < 60:
                time_str = f"{int(duration.total_seconds())}秒前"
            elif duration.total_seconds() < 3600:
                time_str = f"{int(duration.total_seconds() / 60)}分钟前"
            else:
                time_str = f"{int(duration.total_seconds() / 3600)}小时前"

            self.first_seen_lbl.setText(time_str)
        except:
            self.first_seen_lbl.setText("在线")


class DeviceListWidget(QtWidgets.QWidget):
    """设备列表组件"""

    def __init__(self):
        super().__init__()
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 标题栏
        title_bar = QtWidgets.QWidget()
        title_layout = QtWidgets.QHBoxLayout(title_bar)
        title_layout.setContentsMargins(8, 8, 8, 8)

        self.title_label = QtWidgets.QLabel("📡 在线设备列表")
        self.title_label.setProperty("columnTitle", True)
        self.device_count_label = QtWidgets.QLabel("0 个设备")
        self.device_count_label.setStyleSheet("color:#a0a0a0; font-size:10pt;")

        title_layout.addWidget(self.title_label)
        title_layout.addStretch()
        title_layout.addWidget(self.device_count_label)

        layout.addWidget(title_bar)

        # 滚动区域
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.content_widget = QtWidgets.QWidget()
        self.vbox = QtWidgets.QVBoxLayout(self.content_widget)
        self.vbox.setSpacing(8)
        self.vbox.setContentsMargins(4, 4, 4, 4)
        self.vbox.addStretch()

        scroll.setWidget(self.content_widget)
        layout.addWidget(scroll)

        self.cards = {}  # ip -> DeviceCard

    def update_device_count(self):
        """更新设备数量显示"""
        count = len(self.cards)
        self.device_count_label.setText(f"{count} 个设备")

    def add_or_update(self, info):
        """添加或更新设备"""
        ip = info['ip']

        if ip in self.cards:
            # 更新现有设备
            self.cards[ip].update_info(info)
        else:
            # 添加新设备
            card = DeviceCard(info, len(self.cards) + 1)
            self.cards[ip] = card
            # 插入到stretch之前
            self.vbox.insertWidget(self.vbox.count() - 1, card)
            self._renumber()

        self.update_device_count()

    def _renumber(self):
        """重新编号所有设备"""
        for idx, (ip, card) in enumerate(self.cards.items(), 1):
            card.idx_lbl.setText(str(idx))

    def clear(self):
        """清空所有设备"""
        for card in self.cards.values():
            self.vbox.removeWidget(card)
            card.deleteLater()
        self.cards.clear()
        self.update_device_count()


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, iface: str, network: str, scan_interval: int = 10):
        super().__init__()
        self.setWindowTitle("局域网设备扫描工具")
        self.resize(900, 600)

        # 菜单栏
        mbar = self.menuBar()

        # 控制菜单
        control_menu = mbar.addMenu("控制")

        self.scan_action = control_menu.addAction("立即扫描")
        self.scan_action.triggered.connect(self.manual_scan)
        self.scan_action.setShortcut("F5")

        control_menu.addSeparator()

        self.clear_action = control_menu.addAction("清空列表")
        self.clear_action.triggered.connect(self.clear_devices)

        control_menu.addSeparator()

        quit_action = control_menu.addAction("退出")
        quit_action.triggered.connect(self.safe_exit)
        quit_action.setShortcut("Ctrl+Q")

        # 设置菜单
        settings_menu = mbar.addMenu("设置")

        self.interval_action = settings_menu.addAction("扫描间隔设置")
        self.interval_action.triggered.connect(self.show_interval_settings)

        settings_menu.addSeparator()

        about_action = settings_menu.addAction("关于")
        about_action.triggered.connect(self.show_about)

        # 右上角关闭按钮
        quit_btn = QtWidgets.QPushButton("✕")
        quit_btn.setToolTip("安全退出")
        quit_btn.setFixedSize(30, 20)
        quit_btn.setStyleSheet(
            "QPushButton { background:#c73737; color:#fff; border:none; "
            "border-radius:4px; font-weight:bold; padding-bottom:1px; }"
            "QPushButton:hover { background:#e85353; }"
        )
        quit_btn.clicked.connect(self.safe_exit)

        wrapper = QtWidgets.QWidget()
        wrap_lay = QtWidgets.QHBoxLayout(wrapper)
        wrap_lay.setContentsMargins(0, 0, 8, 0)
        wrap_lay.setSpacing(0)
        wrap_lay.addWidget(quit_btn)

        mbar.setCornerWidget(wrapper, QtCore.Qt.TopRightCorner)

        # 主内容区域
        central_widget = QtWidgets.QWidget()
        main_layout = QtWidgets.QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 状态栏（顶部）
        status_bar = QtWidgets.QWidget()
        status_layout = QtWidgets.QHBoxLayout(status_bar)
        status_layout.setContentsMargins(10, 5, 10, 5)

        self.status_icon = QtWidgets.QLabel("🟢")
        self.status_text = QtWidgets.QLabel("扫描中...")
        self.scan_info = QtWidgets.QLabel(f"接口: {iface} | 网段: {network}")
        self.scan_info.setStyleSheet("color:#808080; font-size:9pt;")

        status_layout.addWidget(self.status_icon)
        status_layout.addWidget(self.status_text)
        status_layout.addStretch()
        status_layout.addWidget(self.scan_info)

        main_layout.addWidget(status_bar)

        # 设备列表
        self.device_list = DeviceListWidget()
        main_layout.addWidget(self.device_list)

        self.setCentralWidget(central_widget)

        # 初始化扫描线程
        self.iface = iface
        self.network = network
        self.scan_interval = scan_interval  # 从配置加载的扫描间隔
        self.scan_thread = None

        self.start_scanning()

    def start_scanning(self):
        """开始自动扫描"""
        if self.scan_thread:
            self.scan_thread.stop()

        self.scan_thread = ScanThread(self.iface, self.network, self.scan_interval)
        self.scan_thread.device_found.connect(self._on_device_found)
        self.scan_thread.scan_finished.connect(self._on_scan_finished)
        self.scan_thread.start()

        self.status_text.setText("自动扫描中...")
        self.status_icon.setText("🟢")

    def manual_scan(self):
        """手动触发扫描"""
        if self.scan_thread:
            # 临时提高扫描频率
            old_interval = self.scan_thread.interval
            self.scan_thread.interval = 0.5  # 立即扫描
            QtCore.QTimer.singleShot(1000, lambda: self._reset_scan_interval(old_interval))

            self.status_text.setText("手动扫描中...")
            self.status_icon.setText("🟡")

    def _reset_scan_interval(self, interval):
        """重置扫描间隔"""
        if self.scan_thread:
            self.scan_thread.interval = interval

    def _on_device_found(self, info):
        """处理发现的设备"""
        self.device_list.add_or_update(info)

    def _on_scan_finished(self):
        """扫描完成"""
        self.status_text.setText(f"自动扫描中 (间隔: {self.scan_interval}秒)")
        self.status_icon.setText("🟢")

    def clear_devices(self):
        """清空设备列表"""
        reply = QtWidgets.QMessageBox.question(
            self,
            "确认清空",
            "确定要清空所有设备吗？",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )

        if reply == QtWidgets.QMessageBox.Yes:
            self.device_list.clear()
            self.status_text.setText("列表已清空，继续扫描...")

    def show_interval_settings(self):
        """显示扫描间隔设置对话框"""
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("扫描间隔设置")
        dialog.setFixedSize(350, 200)
        dialog.setStyleSheet(DARK_QSS)

        layout = QtWidgets.QVBoxLayout(dialog)

        label = QtWidgets.QLabel("设置自动扫描间隔时间：")
        layout.addWidget(label)

        spinbox = QtWidgets.QSpinBox()
        spinbox.setRange(2, 60)
        spinbox.setValue(self.scan_interval)
        spinbox.setSuffix(" 秒")
        layout.addWidget(spinbox)

        info_label = QtWidgets.QLabel(
            "💡 提示：\n"
            "• 间隔越短，扫描越频繁，但会增加网络负载\n"
            "• 建议设置为10-30秒\n"
            "• 按F5可立即手动扫描"
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color:#a0a0a0; font-size:9pt; margin-top:10px;")
        layout.addWidget(info_label)

        layout.addStretch()

        btn_layout = QtWidgets.QHBoxLayout()
        save_btn = QtWidgets.QPushButton("保存")
        cancel_btn = QtWidgets.QPushButton("取消")

        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

        save_btn.clicked.connect(lambda: self._update_interval(spinbox.value(), dialog))
        cancel_btn.clicked.connect(dialog.reject)

        dialog.exec_()

    def _update_interval(self, interval, dialog):
        """更新扫描间隔"""
        self.scan_interval = interval
        if self.scan_thread:
            self.scan_thread.interval = interval
        dialog.accept()
        self.status_text.setText(f"自动扫描中 (间隔: {interval}秒)")

    def show_about(self):
        """显示关于对话框"""
        QtWidgets.QMessageBox.about(
            self,
            "关于",
            "局域网设备扫描工具 v1.0\n\n"
            "功能：\n"
            "• 自动扫描局域网中的所有在线设备\n"
            "• 显示每个设备的IP地址、MAC地址、主机名\n"
            "• 记录设备首次发现和最后在线时间\n"
            "• 支持自定义扫描间隔\n\n"
            "技术：\n"
            "• 使用ARP协议进行设备发现\n"
            "• 支持跨平台（Windows/Linux/macOS）\n"
            "• 基于Scapy和PyQt5开发\n\n"
            "© 2024 局域网设备扫描工具"
        )

    def safe_exit(self):
        """安全退出"""
        print("\n[退出] 正在停止扫描线程...")

        if self.scan_thread:
            self.scan_thread.stop()
            self.scan_thread = None

        print("[退出] 程序已退出")
        QtWidgets.QApplication.quit()

    def closeEvent(self, ev: QtGui.QCloseEvent):
        """关闭事件"""
        self.safe_exit()
        ev.accept()


def load_config():
    """从环境变量加载配置"""
    # 加载 .env 文件
    load_dotenv()

    # 网络接口
    interface = os.getenv('NETWORK_INTERFACE', '')
    if not interface:
        # 如果没有配置，自动检测
        if sys.platform == 'win32':
            interface = 'Realtek 8852CE WiFi 6E PCI-E NIC'
        elif sys.platform == 'linux':
            interface = 'eth0'
        elif sys.platform == 'darwin':
            interface = 'en0'
        else:
            interface = 'eth0'

    # 扫描网段
    network_segment = os.getenv('SCAN_NETWORK', '192.168.1.0/24')

    # 扫描间隔
    try:
        scan_interval = int(os.getenv('SCAN_INTERVAL', '10'))
    except ValueError:
        scan_interval = 10

    # 扫描超时
    try:
        scan_timeout = int(os.getenv('SCAN_TIMEOUT', '3'))
    except ValueError:
        scan_timeout = 3

    return interface, network_segment, scan_interval, scan_timeout


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setStyleSheet(DARK_QSS)

    # 从环境变量加载配置
    interface, network_segment, scan_interval, scan_timeout = load_config()

    print(f"启动扫描工具")
    print(f"网络接口: {interface}")
    print(f"扫描网段: {network_segment}")
    print(f"扫描间隔: {scan_interval}秒")
    print(f"扫描超时: {scan_timeout}秒")
    print("-" * 50)

    window = MainWindow(interface, network_segment, scan_interval)
    window.show()

    sys.exit(app.exec_())