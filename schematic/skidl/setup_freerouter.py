"""
设置Freerouter自动布线器
========================
Freerouter是KiCad推荐的外部自动布线工具
它使用专业的Lee算法来避免短路和交叉

步骤：
1. 从KiCad导出DSN文件
2. 用Freerouter打开DSN文件自动布线
3. 导入布线结果(.ses文件)回KiCad

本脚本：
1. 生成DSN导出指南
2. 提供Freerouter下载链接和使用说明
"""

import sys
import os


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    
    print("=" * 70)
    print("Freerouter 自动布线器设置指南")
    print("=" * 70)
    
    print("""
[步骤1] 在KiCad中导出DSN文件
  1. 打开KiCad PCB编辑器
  2. 菜单: 文件 -> 导出 -> Specctra DSN...
  3. 保存为: cybewand_insta360.dsn
  4. 保存位置: D:\\thinkpad\\Documents\\cybewand_insta360\\

[步骤2] 下载并运行Freerouter
  方法A: 从GitHub下载（推荐）
    https://github.com/freerouting/freerouting/releases
    下载最新的 freerouting-xxx.jar 文件
    
  方法B: 直接用Java运行
    java -jar freerouting.jar

[步骤3] 在Freerouter中自动布线
  1. 打开Freerouter
  2. File -> Open Design -> 选择 cybewand_insta360.dsn
  3. 等待文件加载
  4. 点击 "Autoroute" 按钮（或菜单 Route -> Autorouter）
  5. 等待自动布线完成（通常几秒到几分钟）
  6. 查看结果

[步骤4] 导出布线结果
  1. 在Freerouter中: File -> Export Specctra Session File
  2. 保存为: cybewand_insta360.ses
  3. 保存到同一目录

[步骤5] 在KiCad中导入布线结果
  1. 回到KiCad PCB编辑器
  2. 菜单: 文件 -> 导入 -> Specctra Session...
  3. 选择 cybewand_insta360.ses
  4. 确认导入

[步骤6] 检查和优化
  1. 运行DRC检查 (Ctrl+Shift+D)
  2. 手动调整不满意的走线
  3. 按 B 重新填充铜箔

注意事项：
  - Freerouter需要Java运行环境
  - 如果没有Java，可以安装JRE: https://adoptium.net/
  - Freerouter会自动避免短路和交叉
  - 布线结果通常比手动布线更整洁
  - 导入后可能需要微调USB差分对
""")


if __name__ == '__main__':
    main()
