"""分析DRC错误报告"""
import json
import sys
from collections import defaultdict

def analyze_drc(json_file):
    sys.stdout.reconfigure(encoding='utf-8')
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print("=" * 70)
    print("DRC错误分析报告")
    print("=" * 70)
    
    # 统计未连接项
    unconnected = data.get('unconnected_items', [])
    print(f"\n[1] 未连接项: {len(unconnected)} 个")
    
    # 按网络分组
    net_issues = defaultdict(int)
    for item in unconnected:
        for sub_item in item.get('items', []):
            desc = sub_item.get('description', '')
            # 提取网络名
            if '[' in desc and ']' in desc:
                net_name = desc.split('[')[1].split(']')[0]
                net_issues[net_name] += 1
    
    print("\n未连接的网络（前20个）:")
    for net, count in sorted(net_issues.items(), key=lambda x: x[1], reverse=True)[:20]:
        print(f"  {net:30s}: {count:3d} 处未连接")
    
    # 统计violations
    violations = data.get('violations', [])
    print(f"\n[2] 设计规则违规: {len(violations)} 个")
    
    # 按类型分组
    violation_types = defaultdict(int)
    for v in violations:
        vtype = v.get('type', 'unknown')
        violation_types[vtype] += 1
    
    print("\n违规类型统计:")
    for vtype, count in sorted(violation_types.items(), key=lambda x: x[1], reverse=True):
        print(f"  {vtype:40s}: {count:4d} 个")
    
    # 详细分析各类型违规
    print("\n" + "=" * 70)
    print("详细违规分析")
    print("=" * 70)
    
    # 间距违规
    clearance_errors = [v for v in violations if 'clearance' in v.get('type', '').lower()]
    if clearance_errors:
        print(f"\n[!] 间距违规 ({len(clearance_errors)} 个)")
        print("原因: 走线、焊盘或铜箔之间距离太近")
        # 显示前5个
        for i, err in enumerate(clearance_errors[:5], 1):
            items = err.get('items', [])
            if len(items) >= 2:
                desc1 = items[0].get('description', '')[:60]
                desc2 = items[1].get('description', '')[:60]
                print(f"  {i}. {desc1}")
                print(f"     与 {desc2}")
    
    # 走线宽度违规
    track_width_errors = [v for v in violations if 'track_width' in v.get('type', '').lower()]
    if track_width_errors:
        print(f"\n[!] 走线宽度违规 ({len(track_width_errors)} 个)")
        print("原因: 走线宽度不符合设计规则")
    
    # 过孔违规
    via_errors = [v for v in violations if 'via' in v.get('type', '').lower()]
    if via_errors:
        print(f"\n[!] 过孔违规 ({len(via_errors)} 个)")
        print("原因: 过孔大小或位置不合规")
    
    # 铜箔连接问题
    copper_errors = [v for v in violations if 'copper' in v.get('type', '').lower() or 'zone' in v.get('type', '').lower()]
    if copper_errors:
        print(f"\n[!] 铜箔问题 ({len(copper_errors)} 个)")
    
    print("\n" + "=" * 70)
    print("总结")
    print("=" * 70)
    print(f"\n总错误数: {len(unconnected) + len(violations)}")
    print(f"  - 未连接: {len(unconnected)}")
    print(f"  - 违规: {len(violations)}")
    
    # 给出建议
    print("\n建议修复顺序:")
    print("1. [高优先级] 修复未连接的网络（特别是GND和信号网络）")
    print("2. [高优先级] 修复间距违规（调整走线路径或宽度）")
    print("3. [中优先级] 修复走线宽度违规")
    print("4. [低优先级] 优化铜箔填充")
    
    return {
        'unconnected_count': len(unconnected),
        'violation_count': len(violations),
        'net_issues': net_issues,
        'violation_types': violation_types
    }

if __name__ == '__main__':
    if len(sys.argv) > 1:
        result = analyze_drc(sys.argv[1])
    else:
        result = analyze_drc('schematic/skidl/docs/DRC.json')
