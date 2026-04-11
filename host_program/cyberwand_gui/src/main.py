"""
CyberWand Control Center - Windows 原生 GUI 上位机
版本：v1.0.0
创建时间：2026-04-08
"""

import sys
import asyncio
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from qasync import QEventLoop

from main_window import MainWindow


def main():
    """主程序入口"""
    # 创建 Qt 应用
    app = QApplication(sys.argv)
    app.setApplicationName("CyberWand Control Center")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("CyberWand Team")
    
    # 设置窗口图标
    app.setWindowIcon(QIcon("resources/icon.png"))
    
    # 加载样式表
    try:
        with open("resources/styles.qss", "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        pass  # 使用默认样式
    
    # 创建主窗口
    window = MainWindow()
    window.show()
    
    # 运行事件循环
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
