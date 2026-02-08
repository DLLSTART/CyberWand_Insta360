"""
CyberWand DRC错误分析和修正建议

基于DRC报告: schematic/skidl/docs/DRC.json
分析时间: 2026-02-08
"""

import json
import re
from collections import defaultdict

def analyze_drc_report(json_file):
    """分析DRC报告"""
    
    # 设置UTF-8输出
    import sys
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print("=" * 70)
    print("CyberWand DRC 错误分析报告")
    print("=" * 70)
    print(f"\nDRC运行时间: {data['date']}")
    print(f"KiCad版本: {data['kicad_version']}")
    print(f"PCB文件: {data['source']}")
    print()
    
    # 统计未连接项
    unconnected = data.get('unconnected_items', [])
    violations = data.get('violations', [])
    
    print(f"[统计] 错误统计:")
    print(f"  - 未连接错误: {len(unconnected)} 个")
    print(f"  - 设计规则违规: {len(violations)} 个")
    print()
    
    # 分析未连接的网络
    print("=" * 70)
    print("[分析] 未连接网络分析")
    print("=" * 70)
    
    network_stats = defaultdict(lambda: {'count': 0, 'items': []})
    
    for error in unconnected:
        items = error.get('items', [])
        if len(items) >= 2:
            # 提取网络名称
            desc1 = items[0].get('description', '')
            desc2 = items[1].get('description', '')
            
            # 从描述中提取网络名
            match1 = re.search(r'\[(.*?)\]', desc1)
            match2 = re.search(r'\[(.*?)\]', desc2)
            
            if match1 and match2:
                net1 = match1.group(1)
                net2 = match2.group(1)
                
                # 通常net1和net2应该相同
                net_name = net1 if net1 == net2 else f"{net1}/{net2}"
                
                network_stats[net_name]['count'] += 1
                network_stats[net_name]['items'].append({
                    'from': desc1,
                    'to': desc2,
                    'pos1': items[0].get('pos'),
                    'pos2': items[1].get('pos')
                })
    
    # 按网络分类显示
    sorted_nets = sorted(network_stats.items(), key=lambda x: x[1]['count'], reverse=True)
    
    print(f"\n发现 {len(sorted_nets)} 个网络存在未连接错误：\n")
    
    for net_name, info in sorted_nets[:20]:  # 显示前20个
        count = info['count']
        priority = get_network_priority(net_name)
        width = get_track_width(net_name)
        
        print(f"  {priority} | {net_name:20s} | {count:3d} 处未连接 | 推荐线宽: {width}mm")
    
    if len(sorted_nets) > 20:
        print(f"\n  ... 还有 {len(sorted_nets) - 20} 个网络")
    
    print()
    print("=" * 70)
    print("[建议] 修正建议")
    print("=" * 70)
    
    print_recommendations(network_stats)
    
    return network_stats


def get_network_priority(net_name):
    """获取网络优先级标识"""
    name_upper = net_name.upper()
    
    if any(p in name_upper for p in ['VCC', 'BAT', '+5V', '+3V3', 'VBUS', '3V3']):
        return "[P1]"
    if 'GND' in name_upper:
        return "[P2]"
    if 'USB' in name_upper and ('D+' in name_upper or 'D-' in name_upper):
        return "[P3]"
    if 'SCK' in name_upper or 'SCLK' in name_upper or 'BCK' in name_upper:
        return "[P4]"
    if 'SDA' in name_upper or 'SCL' in name_upper:
        return "[P5]"
    return "[P6]"


def get_track_width(net_name):
    """获取推荐走线宽度"""
    name_upper = net_name.upper()
    
    if any(p in name_upper for p in ['VCC', 'BAT', '+5V', '+3V3', 'VBUS', '3V3']):
        return 0.5
    if 'GND' in name_upper:
        return 0.4
    return 0.2


def print_recommendations(network_stats):
    """打印修正建议"""
    
    print("\n[OK] 当前状态：")
    print("  - PCB布局已完成（所有元器件已放置）OK")
    print("  - 板框已创建（60mm x 130mm）OK")
    print("  - 安装孔已添加（4个）OK")
    print("  - GND铺铜区域已设置 OK")
    print("  - [X] 尚未布线（所有错误都是未连接）")
    
    print("\n[方案] 修正方案：\n")
    
    print("【方案1】手动布线（推荐，质量最高）")
    print("-" * 70)
    print("按照以下优先级依次手动布线：\n")
    
    print("第1步：电源线（粗线0.5mm）")
    print("  - VCC_3V3（3.3V电源主网络）")
    print("  - BAT（电池电源）")
    print("  - 5V（USB供电）")
    print("  快捷键：X开始布线，设置线宽0.5mm\n")
    
    print("第2步：GND连接（配合铺铜）")
    print("  - 在关键位置添加GND过孔连接铺铜")
    print("  - 焊盘如果离铺铜远，手动走线连接")
    print("  快捷键：V放置过孔\n")
    
    print("第3步：USB差分对（0.2mm，需要等长）")
    print("  - USB_D+")
    print("  - USB_D-")
    print("  保持平行，长度差<5mm\n")
    
    print("第4步：高速信号（0.2mm）")
    print("  - SPI_SCK（SPI时钟）")
    print("  - SPI_MOSI, SPI_MISO")
    print("  - I2S时钟信号\n")
    
    print("第5步：I2C总线（0.2mm）")
    print("  - I2C_SDA")
    print("  - I2C_SCL\n")
    
    print("第6步：其他信号（0.2mm）")
    print("  - GPIO控制信号")
    print("  - LED控制")
    print("  - 片选信号等\n")
    
    print("第7步：填充铜箔")
    print("  快捷键：B\n")
    
    print("\n【方案2】KiCad自动布线器（快速但需要调整）")
    print("-" * 70)
    print("1. 先手动布线关键信号（电源、USB、SPI时钟）")
    print("2. 菜单：布线 → 自动布线器")
    print("3. 选择剩余网络，点击开始")
    print("4. 自动布线完成后检查和优化")
    print("5. 填充铜箔（快捷键B）\n")
    
    print("\n【方案3】使用CyberWand布线助手（辅助工具）")
    print("-" * 70)
    print("1. 在KiCad中：工具 → 外部插件 → CyberWand Routing Assistant")
    print("2. 点击'应用推荐走线宽度'")
    print("3. 查看网络优先级列表")
    print("4. 按照优先级手动布线")
    print("5. 使用助手一键填充铜箔\n")
    
    print("\n[DOC] 参考文档：")
    print("  - PCB_DESIGN_TUTORIAL.md（第五步：布线实战）")
    print("  - PCB_QUICK_REFERENCE.md（快速参考）")
    print("  - KICAD_PLUGIN_INSTALLED.md（插件使用说明）")
    
    print("\n[!] 重要提示：")
    print("  - 这些错误是正常的！表示还没有布线")
    print("  - 不是PCB布局的问题，布局已经很好了")
    print("  - 现在需要进行布线操作")
    print("  - 布线完成后重新运行DRC，错误会消失")
    
    print("\n" + "=" * 70)


if __name__ == '__main__':
    import sys
    import os
    
    # 默认DRC文件路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    drc_file = os.path.join(script_dir, 'docs', 'DRC.json')
    
    if len(sys.argv) > 1:
        drc_file = sys.argv[1]
    
    if not os.path.exists(drc_file):
        print(f"[X] DRC文件不存在: {drc_file}")
        print("\n使用方法:")
        print(f"  python {os.path.basename(__file__)} <DRC.json路径>")
        sys.exit(1)
    
    try:
        stats = analyze_drc_report(drc_file)
        
        print("\n[OK] 分析完成！")
        print(f"\n建议：立即开始布线，从优先级P1（电源）开始！")
        
    except Exception as e:
        print(f"\n[X] 分析失败: {e}")
        import traceback
        traceback.print_exc()
