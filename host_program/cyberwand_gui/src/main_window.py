"""
CyberWand Control Center - 主窗口
"""

from PySide6.QtWidgets import QMainWindow, QTabWidget, QVBoxLayout, QWidget, QMenuBar, QMenu, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from device_manager import DeviceManagerWidget
from gesture_config import GestureConfigWidget
from realtime_monitor import RealtimeMonitorWidget
from ble_connector import BLEConnector


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        self.ble_connector = BLEConnector()
        self.init_ui()
        self.setup_connections()
    
    def init_ui(self):
        """初始化界面"""
        # 窗口设置
        self.setWindowTitle("CyberWand Control Center - 赛博魔杖控制器")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建布局
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 创建标签页
        self.tabs = QTabWidget()
        self.tabs.addTab(DeviceManagerWidget(self), "📱 设备管理")
        self.tabs.addTab(GestureConfigWidget(self), "🎮 手势配置")
        self.tabs.addTab(RealtimeMonitorWidget(self), "📊 实时监控")
        
        layout.addWidget(self.tabs)
        
        # 创建状态栏
        self.statusBar().showMessage("就绪 - 请扫描并连接设备")
        
        # 创建菜单栏
        self.create_menu_bar()
    
    def setup_connections(self):
        """设置信号连接"""
        # 设备连接信号
        device_widget = self.tabs.widget(0)
        if hasattr(device_widget, 'device_connected'):
            device_widget.device_connected.connect(self.on_device_connected)
    
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件 (&F)")
        
        exit_action = file_menu.addAction("退出 (&X)")
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        
        # 工具菜单
        tools_menu = menubar.addMenu("工具 (&T)")
        
        settings_action = tools_menu.addAction("设置 (&S)")
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self.open_settings)
        
        export_action = tools_menu.addAction("数据导出 (&E)")
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self.export_data)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助 (&H)")
        
        help_action = help_menu.addAction("使用帮助 (&H)")
        help_action.setShortcut("F1")
        help_action.triggered.connect(self.show_help)
        
        about_action = help_menu.addAction("关于 (&A)")
        about_action.triggered.connect(self.show_about)
    
    def open_settings(self):
        """打开设置"""
        QMessageBox.information(self, "设置", "设置功能开发中...")
    
    def export_data(self):
        """导出数据"""
        QMessageBox.information(self, "数据导出", "数据导出功能开发中...")
    
    def show_help(self):
        """显示帮助"""
        help_text = """
        <h2>CyberWand Control Center 使用帮助</h2>
        
        <h3>快速开始</h3>
        <ol>
            <li>点击"🔍 扫描设备"按钮扫描附近的 CyberWand 设备</li>
            <li>双击设备列表中的设备进行连接</li>
            <li>在"🎮 手势配置"页面配置手势映射</li>
            <li>在"📊 实时监控"页面查看传感器数据</li>
        </ol>
        
        <h3>常见问题</h3>
        <p><strong>Q: 扫描不到设备？</strong><br>
        A: 请确保 CyberWand 已开机且处于配对模式。</p>
        
        <p><strong>Q: 连接失败？</strong><br>
        A: 请检查蓝牙是否已开启，设备是否在范围内。</p>
        """
        QMessageBox.about(self, "使用帮助", help_text)
    
    def show_about(self):
        """显示关于"""
        about_text = """
        <h2>CyberWand Control Center</h2>
        <p>版本：1.0.0</p>
        <p>赛博魔杖上位机配置工具</p>
        <p>© 2026 CyberWand Team</p>
        <p>技术支持：太子</p>
        """
        QMessageBox.about(self, "关于 CyberWand", about_text)
    
    @Slot(str)
    def on_device_connected(self, address):
        """设备连接处理"""
        self.statusBar().showMessage(f"已连接设备：{address}")
