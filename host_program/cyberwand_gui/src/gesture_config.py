"""
CyberWand Control Center - 手势配置组件
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, 
                                QComboBox, QSlider, QPushButton, QLabel, 
                                QMessageBox, QGroupBox, QSpinBox)
from PySide6.QtCore import Signal, Slot


class GestureConfigWidget(QWidget):
    """手势配置组件"""
    
    config_saved = Signal(dict)  # 配置保存信号
    config_loaded = Signal(dict)  # 配置加载信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ble_connector = parent.ble_connector if parent else None
        self.init_ui()
        self.setup_connections()
    
    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # 标题
        title_label = QLabel("🎮 手势配置")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # 手势映射组
        gesture_group = QGroupBox("手势映射")
        gesture_layout = QFormLayout(gesture_group)
        gesture_layout.setSpacing(10)
        
        # 挥舞向左
        self.wave_left_combo = QComboBox()
        self.wave_left_combo.addItems([
            "上一页", "下一页", "音量+", "音量-", "播放/暂停", "截图", "无"
        ])
        self.wave_left_combo.setCurrentText("上一页")
        gesture_layout.addRow("挥舞向左:", self.wave_left_combo)
        
        # 挥舞向右
        self.wave_right_combo = QComboBox()
        self.wave_right_combo.addItems([
            "上一页", "下一页", "音量+", "音量-", "播放/暂停", "截图", "无"
        ])
        self.wave_right_combo.setCurrentText("下一页")
        gesture_layout.addRow("挥舞向右:", self.wave_right_combo)
        
        # 顺时针旋转
        self.rotate_cw_combo = QComboBox()
        self.rotate_cw_combo.addItems([
            "上一页", "下一页", "音量+", "音量-", "播放/暂停", "截图", "无"
        ])
        self.rotate_cw_combo.setCurrentText("音量+")
        gesture_layout.addRow("顺时针旋转:", self.rotate_cw_combo)
        
        # 逆时针旋转
        self.rotate_ccw_combo = QComboBox()
        self.rotate_ccw_combo.addItems([
            "上一页", "下一页", "音量+", "音量-", "播放/暂停", "截图", "无"
        ])
        self.rotate_ccw_combo.setCurrentText("音量-")
        gesture_layout.addRow("逆时针旋转:", self.rotate_ccw_combo)
        
        # 画圈手势
        self.circle_combo = QComboBox()
        self.circle_combo.addItems([
            "上一页", "下一页", "音量+", "音量-", "播放/暂停", "截图", "无"
        ])
        self.circle_combo.setCurrentText("播放/暂停")
        gesture_layout.addRow("画圈:", self.circle_combo)
        
        # 双击手势
        self.double_tap_combo = QComboBox()
        self.double_tap_combo.addItems([
            "上一页", "下一页", "音量+", "音量-", "播放/暂停", "截图", "无"
        ])
        self.double_tap_combo.setCurrentText("截图")
        gesture_layout.addRow("双击:", self.double_tap_combo)
        
        layout.addWidget(gesture_group)
        
        # 灵敏度设置组
        sensitivity_group = QGroupBox("识别灵敏度")
        sensitivity_layout = QVBoxLayout(sensitivity_group)
        
        sensitivity_info = QLabel("灵敏度越高，手势识别越快，但可能增加误触发")
        sensitivity_info.setStyleSheet("color: gray; font-size: 12px;")
        sensitivity_layout.addWidget(sensitivity_info)
        
        sensitivity_slider_layout = QHBoxLayout()
        sensitivity_slider_layout.addWidget(QLabel("低"))
        
        self.sensitivity_slider = QSlider()
        self.sensitivity_slider.setOrientation(Qt.Horizontal)
        self.sensitivity_slider.setRange(1, 100)
        self.sensitivity_slider.setValue(80)
        self.sensitivity_slider.setTickPosition(QSlider.TicksBelow)
        self.sensitivity_slider.setTickInterval(10)
        self.sensitivity_slider.valueChanged.connect(self.on_sensitivity_changed)
        sensitivity_slider_layout.addWidget(self.sensitivity_slider)
        
        sensitivity_slider_layout.addWidget(QLabel("高"))
        sensitivity_layout.addLayout(sensitivity_slider_layout)
        
        # 灵敏度数值显示
        self.sensitivity_value_label = QLabel("当前值：80")
        self.sensitivity_value_label.setStyleSheet("font-size: 13px;")
        sensitivity_layout.addWidget(self.sensitivity_value_label)
        
        layout.addWidget(sensitivity_group)
        
        # 高级设置组
        advanced_group = QGroupBox("高级设置")
        advanced_layout = QFormLayout(advanced_group)
        
        # 识别超时（毫秒）
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(100, 5000)
        self.timeout_spin.setValue(500)
        self.timeout_spin.setSuffix(" ms")
        advanced_layout.addRow("识别超时:", self.timeout_spin)
        
        # 连续触发间隔（毫秒）
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(100, 5000)
        self.interval_spin.setValue(1000)
        self.interval_spin.setSuffix(" ms")
        advanced_layout.addRow("触发间隔:", self.interval_spin)
        
        layout.addWidget(advanced_group)
        
        # 按钮区域
        button_layout = QVBoxLayout()
        button_layout.setSpacing(10)
        
        self.save_btn = QPushButton("💾 保存配置到设备")
        self.save_btn.clicked.connect(self.save_config)
        self.save_btn.setStyleSheet("min-height: 40px; font-size: 14px; background-color: #4CAF50; color: white;")
        button_layout.addWidget(self.save_btn)
        
        self.load_btn = QPushButton("📂 从设备加载配置")
        self.load_btn.clicked.connect(self.load_config)
        self.load_btn.setStyleSheet("min-height: 40px; font-size: 14px;")
        button_layout.addWidget(self.load_btn)
        
        self.reset_btn = QPushButton("🔄 恢复默认配置")
        self.reset_btn.clicked.connect(self.reset_config)
        self.reset_btn.setStyleSheet("min-height: 40px; font-size: 14px;")
        button_layout.addWidget(self.reset_btn)
        
        layout.addLayout(button_layout)
        
        # 添加弹性空间
        layout.addStretch()
    
    def setup_connections(self):
        """设置信号连接"""
        if self.ble_connector:
            self.ble_connector.connected.connect(self.on_connected)
            self.ble_connector.disconnected.connect(self.on_disconnected)
    
    @Slot()
    def on_sensitivity_changed(self, value):
        """灵敏度变化处理"""
        self.sensitivity_value_label.setText(f"当前值：{value}")
    
    @Slot()
    async def save_config(self):
        """保存配置"""
        # 检查连接
        if not self.ble_connector or not self.ble_connector.is_connected:
            reply = QMessageBox.question(
                self, "未连接",
                "设备未连接，是否仅保存本地配置？",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        
        # 收集配置
        config = self.get_config()
        
        # 发送到设备
        if self.ble_connector and self.ble_connector.is_connected:
            try:
                await self.ble_connector.send_gesture_mapping(config)
                await self.ble_connector.send_sensitivity(config['sensitivity'])
                QMessageBox.information(self, "成功", "配置已保存到设备")
            except Exception as e:
                QMessageBox.critical(self, "失败", f"保存失败：{str(e)}")
        else:
            QMessageBox.information(self, "成功", "本地配置已保存（未发送到设备）")
        
        self.config_saved.emit(config)
    
    @Slot()
    async def load_config(self):
        """加载配置"""
        # 检查连接
        if not self.ble_connector or not self.ble_connector.is_connected:
            QMessageBox.warning(self, "警告", "请先连接设备")
            return
        
        # TODO: 从设备读取配置
        QMessageBox.information(self, "提示", "加载配置功能开发中...")
    
    @Slot()
    def reset_config(self):
        """恢复默认配置"""
        reply = QMessageBox.question(
            self, "确认",
            "确定要恢复默认配置吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.No:
            return
        
        # 恢复默认值
        self.wave_left_combo.setCurrentText("上一页")
        self.wave_right_combo.setCurrentText("下一页")
        self.rotate_cw_combo.setCurrentText("音量+")
        self.rotate_ccw_combo.setCurrentText("音量-")
        self.circle_combo.setCurrentText("播放/暂停")
        self.double_tap_combo.setCurrentText("截图")
        self.sensitivity_slider.setValue(80)
        self.timeout_spin.setValue(500)
        self.interval_spin.setValue(1000)
    
    @Slot()
    def on_connected(self, device_info):
        """连接成功回调"""
        # 自动加载设备配置
        # self.load_config()
        pass
    
    @Slot()
    def on_disconnected(self):
        """断开连接回调"""
        self.save_btn.setEnabled(False)
        self.load_btn.setEnabled(False)
    
    def get_config(self):
        """获取当前配置"""
        return {
            'wave_left': self.wave_left_combo.currentText(),
            'wave_right': self.wave_right_combo.currentText(),
            'rotate_cw': self.rotate_cw_combo.currentText(),
            'rotate_ccw': self.rotate_ccw_combo.currentText(),
            'circle': self.circle_combo.currentText(),
            'double_tap': self.double_tap_combo.currentText(),
            'sensitivity': self.sensitivity_slider.value(),
            'timeout': self.timeout_spin.value(),
            'interval': self.interval_spin.value()
        }
    
    def set_config(self, config):
        """设置配置"""
        if 'wave_left' in config:
            self.wave_left_combo.setCurrentText(config['wave_left'])
        if 'wave_right' in config:
            self.wave_right_combo.setCurrentText(config['wave_right'])
        if 'rotate_cw' in config:
            self.rotate_cw_combo.setCurrentText(config['rotate_cw'])
        if 'rotate_ccw' in config:
            self.rotate_ccw_combo.setCurrentText(config['rotate_ccw'])
        if 'circle' in config:
            self.circle_combo.setCurrentText(config['circle'])
        if 'double_tap' in config:
            self.double_tap_combo.setCurrentText(config['double_tap'])
        if 'sensitivity' in config:
            self.sensitivity_slider.setValue(config['sensitivity'])
        if 'timeout' in config:
            self.timeout_spin.setValue(config['timeout'])
        if 'interval' in config:
            self.interval_spin.setValue(config['interval'])
