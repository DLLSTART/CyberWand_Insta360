"""
CyberWand Control Center - 实时监控组件
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                                QGroupBox, QGridLayout, QProgressBar, QPushButton)
from PySide6.QtCore import Signal, Slot, QTimer
import pyqtgraph as pg
from pyqtgraph import PlotWidget
import numpy as np
from collections import deque


class RealtimeMonitorWidget(QWidget):
    """实时监控组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ble_connector = parent.ble_connector if parent else None
        self.data_buffer_size = 100  # 数据缓冲区大小
        
        # 数据缓冲区
        self.accel_x_data = deque(maxlen=self.data_buffer_size)
        self.accel_y_data = deque(maxlen=self.data_buffer_size)
        self.accel_z_data = deque(maxlen=self.data_buffer_size)
        self.gyro_x_data = deque(maxlen=self.data_buffer_size)
        self.gyro_y_data = deque(maxlen=self.data_buffer_size)
        self.gyro_z_data = deque(maxlen=self.data_buffer_size)
        
        self.init_ui()
        self.setup_connections()
        
        # 启动定时器更新图表
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_charts)
        self.update_timer.start(100)  # 100ms 更新一次
    
    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # 标题
        title_label = QLabel("📊 实时监控")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # 数据数值显示组
        value_group = QGroupBox("传感器数据")
        value_layout = QGridLayout(value_group)
        value_layout.setSpacing(10)
        
        # 加速度计
        value_layout.addWidget(QLabel("加速度计 (g):"), 0, 0)
        
        self.accel_x_label = QLabel("X: 0.00")
        self.accel_x_label.setStyleSheet("color: red; font-family: Consolas;")
        value_layout.addWidget(self.accel_x_label, 0, 1)
        
        self.accel_y_label = QLabel("Y: 0.00")
        self.accel_y_label.setStyleSheet("color: green; font-family: Consolas;")
        value_layout.addWidget(self.accel_y_label, 0, 2)
        
        self.accel_z_label = QLabel("Z: 0.00")
        self.accel_z_label.setStyleSheet("color: blue; font-family: Consolas;")
        value_layout.addWidget(self.accel_z_label, 0, 3)
        
        # 陀螺仪
        value_layout.addWidget(QLabel("陀螺仪 (°/s):"), 1, 0)
        
        self.gyro_x_label = QLabel("X: 0.0")
        self.gyro_x_label.setStyleSheet("color: red; font-family: Consolas;")
        value_layout.addWidget(self.gyro_x_label, 1, 1)
        
        self.gyro_y_label = QLabel("Y: 0.0")
        self.gyro_y_label.setStyleSheet("color: green; font-family: Consolas;")
        value_layout.addWidget(self.gyro_y_label, 1, 2)
        
        self.gyro_z_label = QLabel("Z: 0.0")
        self.gyro_z_label.setStyleSheet("color: blue; font-family: Consolas;")
        value_layout.addWidget(self.gyro_z_label, 1, 3)
        
        layout.addWidget(value_group)
        
        # 加速度计图表组
        accel_group = QGroupBox("加速度计实时波形")
        accel_layout = QVBoxLayout(accel_group)
        
        self.accel_plot = PlotWidget()
        self.accel_plot.setTitle("加速度计 (g)")
        self.accel_plot.setLabel('left', 'g')
        self.accel_plot.setLabel('bottom', '时间', units='s')
        self.accel_plot.setYRange(-2, 2)
        self.accel_plot.setXRange(0, self.data_buffer_size)
        self.accel_plot.showGrid(x=True, y=True, alpha=0.3)
        self.accel_plot.addLegend()
        
        # 创建三条曲线
        pen_config = {'width': 2}
        self.accel_x_curve = self.accel_plot.plot(pen={'color': 'r', **pen_config}, name='X 轴')
        self.accel_y_curve = self.accel_plot.plot(pen={'color': 'g', **pen_config}, name='Y 轴')
        self.accel_z_curve = self.accel_plot.plot(pen={'color': 'b', **pen_config}, name='Z 轴')
        
        accel_layout.addWidget(self.accel_plot)
        layout.addWidget(accel_group)
        
        # 陀螺仪图表组
        gyro_group = QGroupBox("陀螺仪实时波形")
        gyro_layout = QVBoxLayout(gyro_group)
        
        self.gyro_plot = PlotWidget()
        self.gyro_plot.setTitle("陀螺仪 (°/s)")
        self.gyro_plot.setLabel('left', '°/s')
        self.gyro_plot.setLabel('bottom', '时间', units='s')
        self.gyro_plot.setYRange(-100, 100)
        self.gyro_plot.setXRange(0, self.data_buffer_size)
        self.gyro_plot.showGrid(x=True, y=True, alpha=0.3)
        self.gyro_plot.addLegend()
        
        # 创建三条曲线
        self.gyro_x_curve = self.gyro_plot.plot(pen={'color': 'r', **pen_config}, name='X 轴')
        self.gyro_y_curve = self.gyro_plot.plot(pen={'color': 'g', **pen_config}, name='Y 轴')
        self.gyro_z_curve = self.gyro_plot.plot(pen={'color': 'b', **pen_config}, name='Z 轴')
        
        gyro_layout.addWidget(self.gyro_plot)
        layout.addWidget(gyro_group)
        
        # 电量显示
        battery_group = QGroupBox("电池电量")
        battery_layout = QHBoxLayout(battery_group)
        
        self.battery_bar = QProgressBar()
        self.battery_bar.setRange(0, 100)
        self.battery_bar.setValue(0)
        self.battery_bar.setTextVisible(True)
        self.battery_bar.setFormat("%p%")
        self.battery_bar.setMinimumHeight(30)
        battery_layout.addWidget(self.battery_bar)
        
        self.battery_label = QLabel("0%")
        self.battery_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.battery_label.setMinimumWidth(60)
        battery_layout.addWidget(self.battery_label)
        
        layout.addWidget(battery_group)
        
        # 控制按钮
        button_layout = QHBoxLayout()
        
        self.clear_btn = QPushButton("🗑️ 清空数据")
        self.clear_btn.clicked.connect(self.clear_data)
        button_layout.addWidget(self.clear_btn)
        
        self.pause_btn = QPushButton("⏸️ 暂停")
        self.pause_btn.setCheckable(True)
        self.pause_btn.clicked.connect(self.toggle_pause)
        button_layout.addWidget(self.pause_btn)
        
        self.export_btn = QPushButton("📤 导出数据")
        self.export_btn.clicked.connect(self.export_data)
        button_layout.addWidget(self.export_btn)
        
        layout.addLayout(button_layout)
    
    def setup_connections(self):
        """设置信号连接"""
        if self.ble_connector:
            self.ble_connector.data_received.connect(self.on_data_received)
            self.ble_connector.battery_updated.connect(self.on_battery_updated)
            self.ble_connector.disconnected.connect(self.on_disconnected)
    
    @Slot(bytes)
    def on_data_received(self, data):
        """数据接收处理"""
        # 解析传感器数据
        accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z = self.parse_sensor_data(data)
        
        # 添加到缓冲区
        self.accel_x_data.append(accel_x)
        self.accel_y_data.append(accel_y)
        self.accel_z_data.append(accel_z)
        self.gyro_x_data.append(gyro_x)
        self.gyro_y_data.append(gyro_y)
        self.gyro_z_data.append(gyro_z)
        
        # 更新数值标签
        self.accel_x_label.setText(f"X: {accel_x:.2f}")
        self.accel_y_label.setText(f"Y: {accel_y:.2f}")
        self.accel_z_label.setText(f"Z: {accel_z:.2f}")
        self.gyro_x_label.setText(f"X: {gyro_x:.1f}")
        self.gyro_y_label.setText(f"Y: {gyro_y:.1f}")
        self.gyro_z_label.setText(f"Z: {gyro_z:.1f}")
    
    @Slot(int)
    def on_battery_updated(self, battery_level):
        """电量更新处理"""
        self.battery_bar.setValue(battery_level)
        self.battery_label.setText(f"{battery_level}%")
        
        # 根据电量设置颜色
        if battery_level > 50:
            color = "#4CAF50"  # 绿色
        elif battery_level > 20:
            color = "#FF9800"  # 橙色
        else:
            color = "#F44336"  # 红色
        
        self.battery_bar.setStyleSheet(f"""
            QProgressBar::chunk {{
                background-color: {color};
            }}
        """)
    
    @Slot()
    def on_disconnected(self):
        """断开连接处理"""
        self.clear_data()
        self.battery_bar.setValue(0)
        self.battery_label.setText("0%")
    
    def parse_sensor_data(self, data):
        """解析传感器数据"""
        # 数据格式：[类型][Ax_H][Ax_L][Ay_H][Ay_L][Az_H][Az_L][Gx_H][Gx_L][Gy_H][Gy_L][Gz_H][Gz_L]
        if len(data) < 13:
            return 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        
        # 解析加速度计数据（假设为有符号 16 位整数，量程±2g）
        def to_signed_16bit(high, low):
            value = (high << 8) | low
            if value >= 0x8000:
                value -= 0x10000
            return value
        
        accel_x = to_signed_16bit(data[1], data[2]) / 16384.0  # ±2g 量程
        accel_y = to_signed_16bit(data[3], data[4]) / 16384.0
        accel_z = to_signed_16bit(data[5], data[6]) / 16384.0
        
        # 解析陀螺仪数据（假设为有符号 16 位整数，量程±2000°/s）
        gyro_x = to_signed_16bit(data[7], data[8]) / 16.4  # ±2000°/s 量程
        gyro_y = to_signed_16bit(data[9], data[10]) / 16.4
        gyro_z = to_signed_16bit(data[11], data[12]) / 16.4
        
        return accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z
    
    @Slot()
    def update_charts(self):
        """更新图表"""
        if self.pause_btn.isChecked():
            return
        
        if len(self.accel_x_data) > 0:
            self.accel_x_curve.setData(list(self.accel_x_data))
            self.accel_y_curve.setData(list(self.accel_y_data))
            self.accel_z_curve.setData(list(self.accel_z_data))
        
        if len(self.gyro_x_data) > 0:
            self.gyro_x_curve.setData(list(self.gyro_x_data))
            self.gyro_y_curve.setData(list(self.gyro_y_data))
            self.gyro_z_curve.setData(list(self.gyro_z_data))
    
    @Slot()
    def clear_data(self):
        """清空数据"""
        self.accel_x_data.clear()
        self.accel_y_data.clear()
        self.accel_z_data.clear()
        self.gyro_x_data.clear()
        self.gyro_y_data.clear()
        self.gyro_z_data.clear()
        
        # 清空图表
        self.accel_x_curve.setData([])
        self.accel_y_curve.setData([])
        self.accel_z_curve.setData([])
        self.gyro_x_curve.setData([])
        self.gyro_y_curve.setData([])
        self.gyro_z_curve.setData([])
        
        # 重置标签
        self.accel_x_label.setText("X: 0.00")
        self.accel_y_label.setText("Y: 0.00")
        self.accel_z_label.setText("Z: 0.00")
        self.gyro_x_label.setText("X: 0.0")
        self.gyro_y_label.setText("Y: 0.0")
        self.gyro_z_label.setText("Z: 0.0")
    
    @Slot()
    def toggle_pause(self):
        """切换暂停状态"""
        if self.pause_btn.isChecked():
            self.pause_btn.setText("▶️ 继续")
            self.update_timer.stop()
        else:
            self.pause_btn.setText("⏸️ 暂停")
            self.update_timer.start(100)
    
    @Slot()
    def export_data(self):
        """导出数据"""
        from PySide6.QtWidgets import QFileDialog
        import csv
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出传感器数据",
            "",
            "CSV 文件 (*.csv)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Timestamp', 'Accel_X', 'Accel_Y', 'Accel_Z', 
                                     'Gyro_X', 'Gyro_Y', 'Gyro_Z'])
                    
                    for i in range(len(self.accel_x_data)):
                        writer.writerow([
                            i,
                            self.accel_x_data[i],
                            self.accel_y_data[i],
                            self.accel_z_data[i],
                            self.gyro_x_data[i],
                            self.gyro_y_data[i],
                            self.gyro_z_data[i]
                        ])
                
                QMessageBox.information(self, "成功", f"数据已导出到:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "失败", f"导出失败:\n{str(e)}")
