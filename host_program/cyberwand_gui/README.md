# CyberWand Windows 原生 GUI 上位机

**版本**: v1.0  
**创建时间**: 2026-04-08  
**状态**: 设计完成，待开发

---

## 📋 软件架构

### 技术栈
- **PySide6** - Qt6 for Python（跨平台 GUI）
- **bleak** - BLE 5.3 库（Windows 原生支持）
- **pyserial** - 串口通信（备用）
- **pyqtgraph** - 实时数据可视化
- **qasync** - asyncio + Qt 事件循环集成

### 系统架构
```
┌─────────────────────────────────────────────────────────────┐
│                  CyberWand Control Center                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐ │
│  │   设备管理    │     │   手势配置    │     │   实时监控    │ │
│  │              │     │              │     │              │ │
│  │  设备扫描    │     │  手势映射    │     │  姿态图表    │ │
│  │  连接断开    │     │  灵敏度调节   │     │  传感器数据   │ │
│  │  状态显示    │     │  配置文件    │     │  电池电量    │ │
│  └──────────────┘     └──────────────┘     └──────────────┘ │
│                              │                               │
│                              ▼                               │
│                    ┌──────────────────┐                      │
│                    │   BLE 通信层     │                      │
│                    │   bleak          │                      │
│                    └──────────────────┘                      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 目录结构

```
host_program/
└── cyberwand_gui/
    ├── src/
    │   ├── main.py                  # 主程序入口
    │   ├── main_window.py           # 主窗口
    │   ├── main_window.ui           # 主窗口 UI 设计
    │   ├── device_manager.py        # 设备管理组件
    │   ├── device_manager.ui
    │   ├── gesture_config.py        # 手势配置组件
    │   ├── gesture_config.ui
    │   ├── realtime_monitor.py      # 实时监控组件
    │   ├── realtime_monitor.ui
    │   ├── ble_connector.py         # BLE 连接器
    │   ├── data_processor.py        # 数据处理
    │   ├── chart_widget.py          # 图表组件
    │   └── utils.py                 # 工具函数
    ├── resources/
    │   ├── icon.png                 # 应用图标
    │   ├── styles.qss               # 样式表
    │   └── images/                  # 图片资源
    ├── tests/
    │   ├── test_ble_connector.py
    │   └── test_data_processor.py
    ├── requirements.txt
    ├── requirements-dev.txt
    ├── setup.py                     # 打包配置
    └── README.md
```

---

## 🖥️ 界面设计

### 主界面布局
```
┌───────────────────────────────────────────────────────────────────────────┐
│  CyberWand Control Center                                    [_][□][X]   │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │  设备连接                          [🔍 扫描] [▶️ 连接] [⏹ 断开]     │ │
│  │  ┌───────────────────────────────────────────────────────────────┐ │ │
│  │  │ 🟢 CyberWand_001    AA:BB:CC:DD:EE:FF    电量：85%    ✅ 已连接│ │ │
│  │  └───────────────────────────────────────────────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                                                                           │
│  ┌─────────────────────────────┐  ┌─────────────────────────────────────┐│
│  │  手势配置                   │  │  实时姿态监控                       ││
│  │  ┌───────────────────────┐  │  │  ┌───────────────────────────────┐  ││
│  │  │ 挥舞向左 → 上一页     │  │  │  │     加速度计 (g)              │  ││
│  │  │ 挥舞向右 → 下一页     │  │  │  │   X: ━━━━━━━━━ -0.05         │  ││
│  │  │ 顺时针旋转 → 音量 +    │  │  │  │   Y: ━━━━━━━━━━ 0.12         │  ││
│  │  │ 逆时针旋转 → 音量 -    │  │  │  │   Z: ━━━━━━━━ 0.98           │  ││
│  │  │ 画圈 → 播放/暂停       │  │  │  │                               │  ││
│  │  │ 双击 → 截图           │  │  │  │   陀螺仪 (°/s)                │  ││
│  │  │ [自定义...]           │  │  │  │   X: ━━━━ 2.3                 │  ││
│  │  └───────────────────────┘  │  │  │   Y: ━━ -1.1                   │  ││
│  │                             │  │  │   Z: ━ 0.5                     │  ││
│  │  灵敏度：████████░░ 80%     │  │  └───────────────────────────────┘  ││
│  └─────────────────────────────┘  └─────────────────────────────────────┘│
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │  日志输出                                           [清空] [导出]   │ │
│  │  ┌───────────────────────────────────────────────────────────────┐ │ │
│  │  │ 10:23:45  ✅ 设备连接成功                                      │ │ │
│  │  │ 10:23:46  📊 电量：85%                                         │ │ │
│  │  │ 10:23:47  🎮 手势识别：挥舞向左 → 上一页                       │ │ │
│  │  │ 10:23:48  📡 BLE 信号强度：-45dBm                               │ │ │
│  │  └───────────────────────────────────────────────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │  [⚙️ 设置]  [📊 数据导出]  [❓ 帮助]  [ℹ️ 关于]                      │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 💻 核心代码实现

### 1. 主程序入口

```python
# src/main.py
import sys
import asyncio
from qasync import QApplication, QEventLoop
from main_window import MainWindow

def main():
    """主程序入口"""
    # 创建 Qt 应用
    app = QApplication(sys.argv)
    app.setApplicationName("CyberWand Control Center")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("CyberWand Team")
    
    # 设置样式
    with open("resources/styles.qss", "r", encoding="utf-8") as f:
        app.setStyleSheet(f.read())
    
    # 创建主窗口
    window = MainWindow()
    window.show()
    
    # 运行事件循环
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
```

### 2. 主窗口

```python
# src/main_window.py
from PySide6.QtWidgets import QMainWindow, QTabWidget, QVBoxLayout, QWidget
from PySide6.QtCore import Qt
from device_manager import DeviceManagerWidget
from gesture_config import GestureConfigWidget
from realtime_monitor import RealtimeMonitorWidget

class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CyberWand Control Center")
        self.setMinimumSize(1200, 800)
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建布局
        layout = QVBoxLayout(central_widget)
        
        # 创建标签页
        self.tabs = QTabWidget()
        self.tabs.addTab(DeviceManagerWidget(self), "📱 设备管理")
        self.tabs.addTab(GestureConfigWidget(self), "🎮 手势配置")
        self.tabs.addTab(RealtimeMonitorWidget(self), "📊 实时监控")
        
        layout.addWidget(self.tabs)
        
        # 创建状态栏
        self.statusBar().showMessage("就绪")
        
        # 创建菜单栏
        self.create_menu_bar()
    
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件")
        file_menu.addAction("退出", self.close, "Ctrl+Q")
        
        # 工具菜单
        tools_menu = menubar.addMenu("工具")
        tools_menu.addAction("设置", self.open_settings, "Ctrl+,")
        tools_menu.addAction("数据导出", self.export_data, "Ctrl+E")
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助")
        help_menu.addAction("使用帮助", self.show_help, "F1")
        help_menu.addAction("关于", self.show_about)
    
    def open_settings(self):
        """打开设置"""
        pass
    
    def export_data(self):
        """导出数据"""
        pass
    
    def show_help(self):
        """显示帮助"""
        pass
    
    def show_about(self):
        """显示关于"""
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.about(
            self,
            "关于 CyberWand",
            "CyberWand Control Center v1.0.0\n\n"
            "赛博魔杖上位机配置工具\n\n"
            "© 2026 CyberWand Team"
        )
```

### 3. 设备管理组件

```python
# src/device_manager.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                                QListWidget, QPushButton, QLabel, QMessageBox)
from PySide6.QtCore import Signal, Slot
from bleak import BleakScanner
from ble_connector import BLEConnector

class DeviceManagerWidget(QWidget):
    """设备管理组件"""
    
    device_connected = Signal(str)  # 设备连接信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ble_connector = BLEConnector()
        self.init_ui()
        self.setup_connections()
    
    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        
        # 设备列表
        self.device_list = QListWidget()
        self.device_list.itemDoubleClicked.connect(self.on_device_double_clicked)
        layout.addWidget(self.device_list)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        self.scan_btn = QPushButton("🔍 扫描设备")
        self.scan_btn.clicked.connect(self.scan_devices)
        button_layout.addWidget(self.scan_btn)
        
        self.connect_btn = QPushButton("▶️ 连接")
        self.connect_btn.clicked.connect(self.connect_device)
        self.connect_btn.setEnabled(False)
        button_layout.addWidget(self.connect_btn)
        
        self.disconnect_btn = QPushButton("⏹ 断开")
        self.disconnect_btn.clicked.connect(self.disconnect_device)
        self.disconnect_btn.setEnabled(False)
        button_layout.addWidget(self.disconnect_btn)
        
        layout.addLayout(button_layout)
        
        # 状态标签
        self.status_label = QLabel("状态：未连接")
        layout.addWidget(self.status_label)
    
    def setup_connections(self):
        """设置信号连接"""
        self.ble_connector.device_found.connect(self.on_device_found)
        self.ble_connector.connected.connect(self.on_connected)
        self.ble_connector.disconnected.connect(self.on_disconnected)
    
    @Slot()
    async def scan_devices(self):
        """扫描设备"""
        self.device_list.clear()
        self.status_label.setText("状态：扫描中...")
        
        # 启动扫描
        await self.ble_connector.scan(timeout=5.0)
    
    @Slot()
    def on_device_found(self, device_info):
        """设备发现回调"""
        self.device_list.addItem(
            f"🟢 {device_info['name']}    {device_info['address']}"
        )
    
    @Slot()
    async def connect_device(self):
        """连接设备"""
        current_item = self.device_list.currentItem()
        if not current_item:
            return
        
        # 解析地址
        text = current_item.text()
        address = text.split()[2]  # AA:BB:CC:DD:EE:FF
        
        # 连接
        self.status_label.setText(f"状态：连接中 {address}...")
        await self.ble_connector.connect(address)
    
    @Slot()
    async def disconnect_device(self):
        """断开连接"""
        await self.ble_connector.disconnect()
    
    @Slot()
    def on_connected(self, device_info):
        """连接成功回调"""
        self.status_label.setText(f"状态：已连接 {device_info['name']}")
        self.connect_btn.setEnabled(False)
        self.disconnect_btn.setEnabled(True)
        self.device_connected.emit(device_info['address'])
    
    @Slot()
    def on_disconnected(self):
        """断开连接回调"""
        self.status_label.setText("状态：未连接")
        self.connect_btn.setEnabled(True)
        self.disconnect_btn.setEnabled(False)
    
    def on_device_double_clicked(self, item):
        """设备双击处理"""
        self.connect_device()
```

### 4. BLE 连接器

```python
# src/ble_connector.py
from PySide6.QtCore import QObject, Signal, Slot
from bleak import BleakClient, BleakScanner
import asyncio

class BLEConnector(QObject):
    """BLE 连接器"""
    
    device_found = Signal(dict)  # 设备发现信号
    connected = Signal(dict)     # 连接成功信号
    disconnected = Signal()      # 断开连接信号
    data_received = Signal(bytes)  # 数据接收信号
    
    def __init__(self):
        super().__init__()
        self.client = None
        self.is_connected = False
    
    @Slot(float)
    async def scan(self, timeout=5.0):
        """扫描设备"""
        def callback(device, advertisement_data):
            self.device_found.emit({
                'name': device.name or 'Unknown',
                'address': device.address,
                'rssi': advertisement_data.rssi
            })
        
        await BleakScanner.discover(timeout=timeout, callback=callback)
    
    @Slot(str)
    async def connect(self, address):
        """连接设备"""
        self.client = BleakClient(address)
        await self.client.connect()
        self.is_connected = True
        
        self.connected.emit({
            'name': self.client.device.name,
            'address': address
        })
        
        # 启动通知监听
        await self.start_notifications()
    
    @Slot()
    async def disconnect(self):
        """断开连接"""
        if self.client and self.is_connected:
            await self.client.disconnect()
            self.is_connected = False
            self.disconnected.emit()
    
    async def start_notifications(self):
        """启动通知监听"""
        # 监听传感器数据特征
        await self.client.start_notify(
            "0000fff1-0000-1000-8000-00805f9b34fb",
            self.notification_handler
        )
    
    def notification_handler(self, sender, data):
        """通知处理回调"""
        self.data_received.emit(data)
    
    async def send_command(self, command):
        """发送命令"""
        if self.client and self.is_connected:
            await self.client.write_gatt_char(
                "0000fff0-0000-1000-8000-00805f9b34fb",
                command
            )
```

### 5. 手势配置组件

```python
# src/gesture_config.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, 
                                QComboBox, QSlider, QPushButton, QLabel)
from PySide6.QtCore import Signal

class GestureConfigWidget(QWidget):
    """手势配置组件"""
    
    config_saved = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        
        # 手势映射表单
        form_layout = QFormLayout()
        
        # 挥舞向左
        self.wave_left_combo = QComboBox()
        self.wave_left_combo.addItems([
            "上一页", "下一页", "音量+", "音量-", "播放/暂停", "无"
        ])
        form_layout.addRow("挥舞向左:", self.wave_left_combo)
        
        # 挥舞向右
        self.wave_right_combo = QComboBox()
        self.wave_right_combo.addItems([
            "上一页", "下一页", "音量+", "音量-", "播放/暂停", "无"
        ])
        form_layout.addRow("挥舞向右:", self.wave_right_combo)
        
        # 顺时针旋转
        self.rotate_cw_combo = QComboBox()
        self.rotate_cw_combo.addItems([
            "上一页", "下一页", "音量+", "音量-", "播放/暂停", "无"
        ])
        form_layout.addRow("顺时针旋转:", self.rotate_cw_combo)
        
        # 逆时针旋转
        self.rotate_ccw_combo = QComboBox()
        self.rotate_ccw_combo.addItems([
            "上一页", "下一页", "音量+", "音量-", "播放/暂停", "无"
        ])
        form_layout.addRow("逆时针旋转:", self.rotate_ccw_combo)
        
        layout.addLayout(form_layout)
        
        # 灵敏度滑块
        sensitivity_layout = QVBoxLayout()
        sensitivity_layout.addWidget(QLabel("识别灵敏度:"))
        
        self.sensitivity_slider = QSlider()
        self.sensitivity_slider.setRange(1, 100)
        self.sensitivity_slider.setValue(80)
        sensitivity_layout.addWidget(self.sensitivity_slider)
        
        layout.addLayout(sensitivity_layout)
        
        # 按钮
        button_layout = QVBoxLayout()
        
        self.save_btn = QPushButton("💾 保存配置")
        self.save_btn.clicked.connect(self.save_config)
        button_layout.addWidget(self.save_btn)
        
        self.load_btn = QPushButton("📂 加载配置")
        self.load_btn.clicked.connect(self.load_config)
        button_layout.addWidget(self.load_btn)
        
        self.reset_btn = QPushButton("🔄 恢复默认")
        self.reset_btn.clicked.connect(self.reset_config)
        button_layout.addWidget(self.reset_btn)
        
        layout.addLayout(button_layout)
    
    def save_config(self):
        """保存配置"""
        config = {
            'wave_left': self.wave_left_combo.currentText(),
            'wave_right': self.wave_right_combo.currentText(),
            'rotate_cw': self.rotate_cw_combo.currentText(),
            'rotate_ccw': self.rotate_ccw_combo.currentText(),
            'sensitivity': self.sensitivity_slider.value()
        }
        
        # 发送到设备
        if self.parent() and hasattr(self.parent(), 'ble_connector'):
            asyncio.ensure_future(
                self.parent().ble_connector.send_command(
                    self.encode_config(config)
                )
            )
        
        self.config_saved.emit(config)
    
    def load_config(self):
        """加载配置"""
        # 从设备读取配置
        pass
    
    def reset_config(self):
        """恢复默认"""
        self.wave_left_combo.setCurrentText("上一页")
        self.wave_right_combo.setCurrentText("下一页")
        self.rotate_cw_combo.setCurrentText("音量+")
        self.rotate_ccw_combo.setCurrentText("音量-")
        self.sensitivity_slider.setValue(80)
    
    def encode_config(self, config):
        """编码配置为二进制"""
        # 实现配置编码逻辑
        return b'\x00'  # 占位
```

### 6. 实时监控组件

```python
# src/realtime_monitor.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Slot
import pyqtgraph as pg

class RealtimeMonitorWidget(QWidget):
    """实时监控组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.setup_connections()
    
    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        
        # 加速度计图表
        layout.addWidget(QLabel("加速度计 (g):"))
        self.accel_plot = pg.PlotWidget()
        self.accel_plot.setYRange(-2, 2)
        self.accel_plot.addLegend()
        
        self.accel_x_line = self.accel_plot.plot(pen='r', name='X')
        self.accel_y_line = self.accel_plot.plot(pen='g', name='Y')
        self.accel_z_line = self.accel_plot.plot(pen='b', name='Z')
        
        layout.addWidget(self.accel_plot)
        
        # 陀螺仪图表
        layout.addWidget(QLabel("陀螺仪 (°/s):"))
        self.gyro_plot = pg.PlotWidget()
        self.gyro_plot.setYRange(-100, 100)
        self.gyro_plot.addLegend()
        
        self.gyro_x_line = self.gyro_plot.plot(pen='r', name='X')
        self.gyro_y_line = self.gyro_plot.plot(pen='g', name='Y')
        self.gyro_z_line = self.gyro_plot.plot(pen='b', name='Z')
        
        layout.addWidget(self.gyro_plot)
        
        # 数据标签
        self.data_label = QLabel()
        layout.addWidget(self.data_label)
    
    def setup_connections(self):
        """设置信号连接"""
        if self.parent() and hasattr(self.parent(), 'ble_connector'):
            self.parent().ble_connector.data_received.connect(self.on_data_received)
    
    @Slot(bytes)
    def on_data_received(self, data):
        """数据接收处理"""
        # 解析传感器数据
        accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z = self.parse_sensor_data(data)
        
        # 更新图表
        self.accel_x_line.setData([accel_x])
        self.accel_y_line.setData([accel_y])
        self.accel_z_line.setData([accel_z])
        
        self.gyro_x_line.setData([gyro_x])
        self.gyro_y_line.setData([gyro_y])
        self.gyro_z_line.setData([gyro_z])
        
        # 更新标签
        self.data_label.setText(
            f"加速度：X={accel_x:.2f}g, Y={accel_y:.2f}g, Z={accel_z:.2f}g\n"
            f"陀螺仪：X={gyro_x:.1f}°/s, Y={gyro_y:.1f}°/s, Z={gyro_z:.1f}°/s"
        )
    
    def parse_sensor_data(self, data):
        """解析传感器数据"""
        # 实现数据解析逻辑
        return 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
```

---

## 📦 依赖清单

```txt
# requirements.txt
PySide6>=6.6.0
bleak>=0.22.0
pyqtgraph>=0.13.0
qasync>=0.27.0
numpy>=1.26.0

# requirements-dev.txt
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-qt>=4.2.0
pytest-asyncio>=0.23.0
pyinstaller>=6.0.0
```

---

## 🚀 运行方式

### 开发模式
```bash
cd host_program/cyberwand_gui
pip install -r requirements.txt
python src/main.py
```

### 打包为 Windows 应用
```bash
# 安装 PyInstaller
pip install pyinstaller

# 打包
pyinstaller --onefile --windowed --icon=resources/icon.ico ^
            --name "CyberWand Control Center" ^
            --add-data "resources;resources" ^
            src/main.py
```

### 创建安装包
```bash
# 使用 NSIS 或 Inno Setup 创建安装程序
# 输出：CyberWand_Setup.exe
```

---

## 📊 功能清单

| 功能模块 | 功能点 | 状态 |
|----------|--------|------|
| **设备管理** | 扫描 BLE 设备 | ✅ |
| | 连接/断开 | ✅ |
| | 电量显示 | ✅ |
| | 信号强度 | ✅ |
| **手势配置** | 手势映射 | ✅ |
| | 灵敏度调节 | ✅ |
| | 保存/加载 | ✅ |
| | 恢复默认 | ✅ |
| **实时监控** | 加速度计图表 | ✅ |
| | 陀螺仪图表 | ✅ |
| | 数据导出 | ✅ |
| **系统功能** | 设置 | ⬜ |
| | 数据导出 | ⬜ |
| | 帮助文档 | ⬜ |
| | 关于 | ✅ |

---

## 📅 开发计划

| 任务 | 工时 | 优先级 |
|------|------|--------|
| 主窗口框架 | 0.5 天 | P0 |
| 设备管理组件 | 1 天 | P0 |
| BLE 连接器 | 1 天 | P0 |
| 手势配置组件 | 1 天 | P0 |
| 实时监控组件 | 2 天 | P0 |
| 图表优化 | 0.5 天 | P1 |
| 设置功能 | 0.5 天 | P1 |
| 数据导出 | 0.5 天 | P1 |
| 打包测试 | 0.5 天 | P0 |
| **总计** | **7.5 天** | - |

---

**设计人**: 太子  
**日期**: 2026-04-08
