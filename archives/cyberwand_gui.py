"""
CyberWand Host GUI v2.0
上位机程序 - 蓝牙连接魔杖并配置按键/功能映射

功能：
- 蓝牙连接CyberWand
- 配置按键映射
- 配置手势功能
- 配置LED灯语
- 保存配置到设备
"""

import sys
import asyncio
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QComboBox, QTableWidget, QTableWidgetItem,
    QMessageBox, QGroupBox, QProgressBar, QTextEdit, QSplitter,
    QTabWidget, QFormLayout, QLineEdit, QCheckBox
)
from PySide6.QtCore import Qt, QTimer, Signal, QObject
from PySide6.QtGui import QFont, QIcon

try:
    from bleak import BleakClient, BleakScanner
    BLEAK_AVAILABLE = True
except ImportError:
    BLEAK_AVAILABLE = False
    print("警告：bleak库未安装，蓝牙功能不可用")
    print("请运行：pip install bleak")


class BluetoothManager(QObject):
    """蓝牙管理模块"""
    
    device_found = Signal(str, str)
    connection_status = Signal(bool, str)
    data_received = Signal(bytes)
    
    def __init__(self):
        super().__init__()
        self.client = None
        self.connected = False
        self.device_address = None
        
    async def scan_devices(self):
        """扫描蓝牙设备"""
        devices = await BleakScanner.discover(timeout=5.0)
        for device in devices:
            self.device_found.emit(device.name or "Unknown", device.address)
        return devices
    
    async def connect(self, address):
        """连接设备"""
        try:
            self.client = BleakClient(address)
            await self.client.connect()
            self.connected = True
            self.device_address = address
            self.connection_status.emit(True, f"已连接：{address}")
            return True
        except Exception as e:
            self.connection_status.emit(False, f"连接失败：{str(e)}")
            return False
    
    async def disconnect(self):
        """断开连接"""
        if self.client:
            await self.client.disconnect()
            self.connected = False
            self.connection_status.emit(False, "已断开")
    
    async def send_command(self, command):
        """发送命令"""
        if self.client and self.connected:
            # 假设服务UUID和特征UUID
            SERVICE_UUID = "0000ffe0-0000-1000-8000-00805f9b34fb"
            CHAR_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"
            await self.client.write_gatt_char(CHAR_UUID, command.encode())
            return True
        return False
    
    async def read_data(self):
        """读取数据"""
        if self.client and self.connected:
            # 实现读取逻辑
            pass


class CyberWandGUI(QMainWindow):
    """CyberWand上位机主窗口"""
    
    def __init__(self):
        super().__init__()
        self.bt_manager = BluetoothManager()
        self.config_data = {
            "button_mappings": [
                {"id": 1, "type": "MODE_TOGGLE", "action": "模式切换"}
            ],
            "gesture_functions": [
                {"id": 1, "gesture": "挥手", "function": "拍照"},
                {"id": 2, "gesture": "握拳", "function": "开始录像"},
                {"id": 3, "gesture": "旋转", "function": "参数调整"}
            ],
            "led_patterns": [
                {"mode": "IDLE", "pattern": "闪烁"},
                {"mode": "CONTROL", "pattern": "常亮"},
                {"mode": "RECORD", "pattern": "快闪"},
                {"mode": "TRANS", "pattern": "慢闪"}
            ]
        }
        self.init_ui()
        self.setup_connections()
        
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("CyberWand Host v2.0 - 魔杖配置工具")
        self.setMinimumSize(800, 600)
        
        # 主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # 顶部状态栏
        status_group = QGroupBox("连接状态")
        status_layout = QHBoxLayout(status_group)
        
        self.status_label = QLabel("未连接")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        self.device_combo = QComboBox()
        self.device_combo.setMinimumWidth(200)
        
        self.scan_btn = QPushButton("扫描设备")
        self.connect_btn = QPushButton("连接")
        self.disconnect_btn = QPushButton("断开")
        self.disconnect_btn.setEnabled(False)
        
        status_layout.addWidget(QLabel("设备:"))
        status_layout.addWidget(self.device_combo)
        status_layout.addWidget(self.scan_btn)
        status_layout.addWidget(self.connect_btn)
        status_layout.addWidget(self.disconnect_btn)
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        
        # 标签页
        self.tabs = QTabWidget()
        
        # 标签页1：按键映射
        self.button_mapping_widget = self.create_button_mapping_tab()
        self.tabs.addTab(self.button_mapping_widget, "按键映射")
        
        # 标签页2：手势功能
        self.gesture_widget = self.create_gesture_function_tab()
        self.tabs.addTab(self.gesture_widget, "手势功能")
        
        # 标签页3：LED灯语
        self.led_widget = self.create_led_pattern_tab()
        self.tabs.addTab(self.led_widget, "LED灯语")
        
        # 标签页4：日志
        self.log_widget = self.create_log_tab()
        self.tabs.addTab(self.log_widget, "日志")
        
        # 底部按钮
        button_layout = QHBoxLayout()
        self.save_btn = QPushButton("💾 保存配置到魔杖")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.save_btn.setEnabled(False)
        
        button_layout.addStretch()
        button_layout.addWidget(self.save_btn)
        button_layout.addStretch()
        
        # 添加到主布局
        main_layout.addWidget(status_group)
        main_layout.addWidget(self.tabs)
        main_layout.addLayout(button_layout)
        
    def create_button_mapping_tab(self):
        """创建按键映射标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 表格
        self.button_table = QTableWidget()
        self.button_table.setColumnCount(3)
        self.button_table.setHorizontalHeaderLabels(["按键ID", "类型", "动作描述"])
        self.button_table.horizontalHeader().setStretchLastSection(True)
        
        # 填充数据
        for i, mapping in enumerate(self.config_data["button_mappings"]):
            self.button_table.insertRow(i)
            self.button_table.setItem(i, 0, QTableWidgetItem(str(mapping["id"])))
            self.button_table.setItem(i, 1, QTableWidgetItem(mapping["type"]))
            self.button_table.setItem(i, 2, QTableWidgetItem(mapping["action"]))
        
        layout.addWidget(QLabel("按键映射配置："))
        layout.addWidget(self.button_table)
        
        # 编辑按钮
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("➕ 添加")
        edit_btn = QPushButton("✏️ 编辑")
        delete_btn = QPushButton("🗑️ 删除")
        
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(delete_btn)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        
        return widget
    
    def create_gesture_function_tab(self):
        """创建手势功能标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 表格
        self.gesture_table = QTableWidget()
        self.gesture_table.setColumnCount(3)
        self.gesture_table.setHorizontalHeaderLabels(["手势ID", "手势名称", "功能"])
        self.gesture_table.horizontalHeader().setStretchLastSection(True)
        
        # 填充数据
        for i, gesture in enumerate(self.config_data["gesture_functions"]):
            self.gesture_table.insertRow(i)
            self.gesture_table.setItem(i, 0, QTableWidgetItem(str(gesture["id"])))
            self.gesture_table.setItem(i, 1, QTableWidgetItem(gesture["gesture"]))
            self.gesture_table.setItem(i, 2, QTableWidgetItem(gesture["function"]))
        
        layout.addWidget(QLabel("手势功能映射："))
        layout.addWidget(self.gesture_table)
        
        # 编辑按钮
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("➕ 添加")
        edit_btn = QPushButton("✏️ 编辑")
        delete_btn = QPushButton("🗑️ 删除")
        
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(delete_btn)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        
        return widget
    
    def create_led_pattern_tab(self):
        """创建LED灯语标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 表格
        self.led_table = QTableWidget()
        self.led_table.setColumnCount(2)
        self.led_table.setHorizontalHeaderLabels(["模式", "灯光图案"])
        self.led_table.horizontalHeader().setStretchLastSection(True)
        
        # 填充数据
        for i, pattern in enumerate(self.config_data["led_patterns"]):
            self.led_table.insertRow(i)
            self.led_table.setItem(i, 0, QTableWidgetItem(pattern["mode"]))
            self.led_table.setItem(i, 1, QTableWidgetItem(pattern["pattern"]))
        
        layout.addWidget(QLabel("LED灯语配置："))
        layout.addWidget(self.led_table)
        
        # 编辑按钮
        btn_layout = QHBoxLayout()
        edit_btn = QPushButton("✏️ 编辑")
        
        btn_layout.addWidget(edit_btn)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        
        return widget
    
    def create_log_tab(self):
        """创建日志标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        
        layout.addWidget(QLabel("操作日志："))
        layout.addWidget(self.log_text)
        
        clear_btn = QPushButton("🗑️ 清空日志")
        layout.addWidget(clear_btn)
        
        return widget
    
    def setup_connections(self):
        """设置信号槽连接"""
        self.scan_btn.clicked.connect(self.scan_devices)
        self.connect_btn.clicked.connect(self.connect_device)
        self.disconnect_btn.clicked.connect(self.disconnect_device)
        self.save_btn.clicked.connect(self.save_config)
        
        # 蓝牙管理器信号
        if BLEAK_AVAILABLE:
            self.bt_manager.device_found.connect(self.on_device_found)
            self.bt_manager.connection_status.connect(self.on_connection_status)
        
    def log_message(self, message):
        """记录日志"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        
    def on_device_found(self, name, address):
        """设备发现回调"""
        self.device_combo.addItem(f"{name} ({address})")
        self.log_message(f"发现设备：{name} - {address}")
        
    def on_connection_status(self, connected, message):
        """连接状态回调"""
        if connected:
            self.status_label.setText("已连接 ✓")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            self.connect_btn.setEnabled(False)
            self.disconnect_btn.setEnabled(True)
            self.save_btn.setEnabled(True)
        else:
            self.status_label.setText("未连接")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            self.connect_btn.setEnabled(True)
            self.disconnect_btn.setEnabled(False)
            self.save_btn.setEnabled(False)
        
        self.log_message(message)
        
    async def scan_devices(self):
        """扫描设备"""
        self.log_message("开始扫描蓝牙设备...")
        self.device_combo.clear()
        
        if not BLEAK_AVAILABLE:
            QMessageBox.warning(self, "警告", "bleak库未安装，无法扫描蓝牙设备")
            return
        
        devices = await self.bt_manager.scan_devices()
        self.log_message(f"扫描完成，发现 {len(devices)} 个设备")
        
    async def connect_device(self):
        """连接设备"""
        current_text = self.device_combo.currentText()
        if not current_text:
            QMessageBox.warning(self, "警告", "请先选择设备")
            return
        
        # 提取地址
        address = current_text.split("(")[-1].strip(")")
        self.log_message(f"正在连接：{address}")
        
        await self.bt_manager.connect(address)
        
    async def disconnect_device(self):
        """断开连接"""
        await self.bt_manager.disconnect()
        
    async def save_config(self):
        """保存配置"""
        self.log_message("正在保存配置到魔杖...")
        
        # 构建配置数据
        config_str = "CONFIG:"
        for mapping in self.config_data["button_mappings"]:
            config_str += f"B{mapping['id']}={mapping['type']}:{mapping['action']};"
        for gesture in self.config_data["gesture_functions"]:
            config_str += f"G{gesture['id']}={gesture['gesture']}:{gesture['function']};"
        config_str += "END"
        
        success = await self.bt_manager.send_command(config_str)
        
        if success:
            self.log_message("配置保存成功！")
            QMessageBox.information(self, "成功", "配置已保存到魔杖！")
        else:
            self.log_message("配置保存失败！")
            QMessageBox.critical(self, "失败", "配置保存失败，请检查连接")
    
    def run_scan(self):
        """运行扫描（包装为普通方法）"""
        if BLEAK_AVAILABLE:
            asyncio.run(self.scan_devices())
    
    def run_connect(self):
        """运行连接"""
        if BLEAK_AVAILABLE:
            asyncio.run(self.connect_device())
    
    def run_disconnect(self):
        """运行断开"""
        if BLEAK_AVAILABLE:
            asyncio.run(self.disconnect_device())
    
    def run_save(self):
        """运行保存"""
        if BLEAK_AVAILABLE:
            asyncio.run(self.save_config())


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用样式
    app.setStyle("Fusion")
    
    window = CyberWandGUI()
    window.show()
    
    # 重新连接信号槽到同步方法
    window.scan_btn.clicked.disconnect()
    window.connect_btn.clicked.disconnect()
    window.disconnect_btn.clicked.disconnect()
    window.save_btn.clicked.disconnect()
    
    window.scan_btn.clicked.connect(window.run_scan)
    window.connect_btn.clicked.connect(window.run_connect)
    window.disconnect_btn.clicked.connect(window.run_disconnect)
    window.save_btn.clicked.connect(window.run_save)
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
