"""
CyberWand Control Center - 设备管理组件
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                                QListWidget, QListWidgetItem, QPushButton, 
                                QLabel, QMessageBox, QProgressBar)
from PySide6.QtCore import Signal, Slot
from PySide6.QtGui import QIcon


class DeviceManagerWidget(QWidget):
    """设备管理组件"""
    
    device_connected = Signal(str)  # 设备连接信号
    device_disconnected = Signal()  # 设备断开信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ble_connector = parent.ble_connector if parent else None
        self.init_ui()
        self.setup_connections()
    
    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # 标题
        title_label = QLabel("📱 设备管理")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # 设备列表
        self.device_list = QListWidget()
        self.device_list.setAlternatingRowColors(True)
        self.device_list.itemDoubleClicked.connect(self.on_device_double_clicked)
        self.device_list.itemSelectionChanged.connect(self.on_selection_changed)
        layout.addWidget(self.device_list)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        self.scan_btn = QPushButton("🔍 扫描设备")
        self.scan_btn.clicked.connect(self.scan_devices)
        self.scan_btn.setStyleSheet("min-height: 40px; font-size: 14px;")
        button_layout.addWidget(self.scan_btn)
        
        self.connect_btn = QPushButton("▶️ 连接")
        self.connect_btn.clicked.connect(self.connect_device)
        self.connect_btn.setEnabled(False)
        self.connect_btn.setStyleSheet("min-height: 40px; font-size: 14px;")
        button_layout.addWidget(self.connect_btn)
        
        self.disconnect_btn = QPushButton("⏹ 断开")
        self.disconnect_btn.clicked.connect(self.disconnect_device)
        self.disconnect_btn.setEnabled(False)
        self.disconnect_btn.setStyleSheet("min-height: 40px; font-size: 14px;")
        button_layout.addWidget(self.disconnect_btn)
        
        layout.addLayout(button_layout)
        
        # 状态信息区域
        status_layout = QVBoxLayout()
        
        # 连接状态
        self.status_label = QLabel("状态：未连接")
        self.status_label.setStyleSheet("font-size: 13px;")
        status_layout.addWidget(self.status_label)
        
        # 电量显示
        battery_layout = QHBoxLayout()
        battery_layout.addWidget(QLabel("电量:"))
        self.battery_bar = QProgressBar()
        self.battery_bar.setRange(0, 100)
        self.battery_bar.setValue(0)
        self.battery_bar.setTextVisible(True)
        self.battery_bar.setFormat("%p%")
        self.battery_bar.setEnabled(False)
        battery_layout.addWidget(self.battery_bar)
        status_layout.addLayout(battery_layout)
        
        # 信号强度
        rssi_layout = QHBoxLayout()
        rssi_layout.addWidget(QLabel("信号强度:"))
        self.rssi_label = QLabel("-")
        self.rssi_label.setStyleSheet("font-size: 13px;")
        rssi_layout.addWidget(self.rssi_label)
        status_layout.addLayout(rssi_layout)
        
        layout.addLayout(status_layout)
        
        # 说明文字
        help_label = QLabel("💡 提示：双击设备列表中的设备进行快速连接")
        help_label.setStyleSheet("color: gray; font-size: 12px;")
        layout.addWidget(help_label)
    
    def setup_connections(self):
        """设置信号连接"""
        if self.ble_connector:
            self.ble_connector.device_found.connect(self.on_device_found)
            self.ble_connector.connected.connect(self.on_connected)
            self.ble_connector.disconnected.connect(self.on_disconnected)
            self.ble_connector.battery_updated.connect(self.on_battery_updated)
            self.ble_connector.error_occurred.connect(self.on_error)
    
    @Slot()
    async def scan_devices(self):
        """扫描设备"""
        self.device_list.clear()
        self.status_label.setText("状态：扫描中...")
        self.scan_btn.setEnabled(False)
        
        if self.ble_connector:
            await self.ble_connector.scan(timeout=5.0)
        
        self.scan_btn.setEnabled(True)
        self.status_label.setText("状态：扫描完成")
    
    @Slot(dict)
    def on_device_found(self, device_info):
        """设备发现回调"""
        name = device_info.get('name', 'Unknown')
        address = device_info.get('address', '')
        rssi = device_info.get('rssi', 0)
        
        # 添加设备到列表
        item_text = f"{name}    {address}"
        item = QListWidgetItem(item_text)
        item.setData(Qt.UserRole, device_info)  # 存储设备信息
        
        # 根据信号强度设置颜色
        if rssi > -50:
            item.setForeground(Qt.green)  # 强信号
        elif rssi > -70:
            item.setForeground(Qt.black)  # 中等信号
        else:
            item.setForeground(Qt.gray)  # 弱信号
        
        self.device_list.addItem(item)
    
    @Slot()
    async def connect_device(self):
        """连接设备"""
        current_item = self.device_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "警告", "请先选择要连接的设备")
            return
        
        # 解析设备信息
        device_info = current_item.data(Qt.UserRole)
        address = device_info.get('address', '')
        
        if not address:
            QMessageBox.warning(self, "警告", "设备地址无效")
            return
        
        # 连接
        self.status_label.setText(f"状态：连接中 {address}...")
        self.connect_btn.setEnabled(False)
        
        if self.ble_connector:
            await self.ble_connector.connect(address)
    
    @Slot()
    async def disconnect_device(self):
        """断开连接"""
        self.status_label.setText("状态：断开中...")
        
        if self.ble_connector:
            await self.ble_connector.disconnect()
    
    @Slot()
    def on_connected(self, device_info):
        """连接成功回调"""
        name = device_info.get('name', 'CyberWand')
        address = device_info.get('address', '')
        
        self.status_label.setText(f"状态：已连接 {name}")
        self.connect_btn.setEnabled(False)
        self.disconnect_btn.setEnabled(True)
        self.battery_bar.setEnabled(True)
        
        self.device_connected.emit(address)
    
    @Slot()
    def on_disconnected(self):
        """断开连接回调"""
        self.status_label.setText("状态：未连接")
        self.connect_btn.setEnabled(True)
        self.disconnect_btn.setEnabled(False)
        self.battery_bar.setEnabled(False)
        self.battery_bar.setValue(0)
        self.rssi_label.setText("-")
        
        self.device_disconnected.emit()
    
    @Slot(int)
    def on_battery_updated(self, battery_level):
        """电量更新回调"""
        self.battery_bar.setValue(battery_level)
        
        # 根据电量设置颜色
        if battery_level > 50:
            self.battery_bar.setStyleSheet("QProgressBar::chunk { background-color: #4CAF50; }")
        elif battery_level > 20:
            self.battery_bar.setStyleSheet("QProgressBar::chunk { background-color: #FF9800; }")
        else:
            self.battery_bar.setStyleSheet("QProgressBar::chunk { background-color: #F44336; }")
    
    @Slot(str)
    def on_error(self, error_message):
        """错误处理"""
        QMessageBox.critical(self, "错误", error_message)
        self.status_label.setText("状态：错误")
        self.connect_btn.setEnabled(True)
        self.disconnect_btn.setEnabled(False)
    
    @Slot(QListWidgetItem)
    def on_device_double_clicked(self, item):
        """设备双击处理"""
        self.connect_device()
    
    @Slot()
    def on_selection_changed(self):
        """选择变化处理"""
        has_selection = self.device_list.currentItem() is not None
        self.connect_btn.setEnabled(has_selection and not self.disconnect_btn.isEnabled())
    
    def get_selected_device(self):
        """获取选中的设备"""
        current_item = self.device_list.currentItem()
        if current_item:
            return current_item.data(Qt.UserRole)
        return None
