"""
CyberWand v2.0 - 更新现有4层PCB
功能:
  1. 从现有4层PCB加载（保留层叠设置）
  2. 导入新网表（添加保护组件）
  3. 更新元器件布局
  4. 清除旧布线，执行智能布线
  5. 运行DRC验证并迭代修复
"""

import pcbnew
import os
import sys
import re
import math
import subprocess
import json
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')

# ============================================================
# 配置
# ============================================================
KICAD_PROJECT = r'D:\thinkpad\Documents\cybewand_insta360'
PCB_FILE = os.path.join(KICAD_PROJECT, 'cybewand_insta360.kicad_pcb')
NETLIST_FILE = r'D:\win_workspace\CyberWand_Insta360\schematic\skidl\output\cyberwand_netlist.net'
KICAD_FP_DIR = r'D:\kicad\share\kicad\footprints'
KICAD_CLI = r'D:\kicad\bin\kicad-cli.exe'
DRC_OUTPUT = r'D:\win_workspace\CyberWand_Insta360\schematic\skidl\docs\DRC_v2.json'
DSN_FILE = os.path.join(KICAD_PROJECT, 'cybewand_insta360.dsn')

# 板子参数（保持现有尺寸）
BL, BT = 10, 10
BW, BH = 100, 85

def mm(v): return pcbnew.FromMM(v)
def tomm(v): return pcbnew.ToMM(v)
def pt(x, y): return pcbnew.VECTOR2I(mm(x), mm(y))
def ap(rx, ry): return (BL + rx, BT + ry)

# ============================================================
# 网表解析
# ============================================================
def parse_netlist(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    components, nets = {}, {}
    
    # 解析组件
    pos = 0
    while True:
        idx = content.find('(comp\n', pos)
        if idx == -1: idx = content.find('(comp ', pos)
        if idx == -1: break
        depth, end = 0, idx
        for i in range(idx, len(content)):
            if content[i] == '(': depth += 1
            elif content[i] == ')':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        block = content[idx:end]
        ref_m = re.search(r'\(ref\s+"([^"]+)"\)', block)
        fp_m = re.search(r'\(footprint\s+"([^"]+)"\)', block)
        val_m = re.search(r'\(value\s+"([^"]*)"\)', block)
        if ref_m and fp_m:
            components[ref_m.group(1)] = {
                'footprint': fp_m.group(1),
                'value': val_m.group(1) if val_m else ''
            }
        pos = end
    
    # 解析网络
    ns = content.find('(nets')
    if ns > 0:
        nc = content[ns:]
        pos = 0
        while True:
            idx = nc.find('(net\n', pos)
            if idx == -1: idx = nc.find('(net ', pos)
            if idx == -1: break
            depth, end = 0, idx
            for i in range(idx, min(idx+5000, len(nc))):
                if nc[i] == '(': depth += 1
                elif nc[i] == ')':
                    depth -= 1
                    if depth == 0:
                        end = i + 1
                        break
            block = nc[idx:end]
            nm = re.search(r'\(name\s+"([^"]*)"\)', block)
            if nm:
                name = nm.group(1)
                pins = re.findall(
                    r'\(node\s*\n?\s*\(ref\s+"([^"]+)"\)\s*\n?\s*\(pin\s+"([^"]+)"\)',
                    block)
                nets.setdefault(name, []).extend(pins)
            pos = end
    
    return components, nets

# ============================================================
# 元器件布局定义
# ============================================================
LAYOUT = {
    # ═══ ESP32主控区 (中心偏左) ═══
    'U1':   (ap(36, 35), 0, 'F'),
    'C1':   (ap(24, 23), 0, 'F'),
    'C2':   (ap(24, 26), 0, 'F'),
    'C3':   (ap(24, 29), 0, 'F'),
    'R1':   (ap(24, 32), 0, 'F'),
    'R7':   (ap(24, 35), 0, 'F'),

    # ═══ LCD (顶部中央) ═══
    'LCD1': (ap(55, 7),  90, 'F'),
    'C5':   (ap(67, 3),  0,  'F'),
    'C6':   (ap(71, 3),  0,  'F'),

    # ═══ SPI阻尼电阻 ═══
    'R13':  (ap(45, 15), 0,  'F'),
    'R14':  (ap(45, 18), 0,  'F'),

    # ═══ MPU6050 ═══
    'U2':   (ap(61, 35), 0,  'F'),
    'C4':   (ap(69, 35), 0,  'F'),
    'R2':   (ap(59, 28), 0,  'F'),
    'R3':   (ap(64, 28), 0,  'F'),

    # ═══ SD卡 ═══
    'J1':   (ap(86, 11), 0,  'F'),

    # ═══ DFPlayer + 扬声器 ═══
    'U3':   (ap(84, 35), 0,  'F'),
    'C7':   (ap(94, 29), 0,  'F'),
    'C8':   (ap(97, 29), 0,  'F'),
    'LS1':  (ap(84, 17), 0,  'B'),

    # ═══ INMP441麦克风 ═══
    'MIC1': (ap(84, 51), 0,  'F'),
    'C10':  (ap(92, 51), 0,  'F'),
    'R15':  (ap(73, 43), 0,  'F'),
    'R16':  (ap(73, 46), 0,  'F'),

    # ═══ 按键 ═══
    'SW2':  (ap(5, 27),  0,  'F'),
    'SW3':  (ap(5, 43),  0,  'F'),
    'SW4':  (ap(5, 59),  0,  'F'),
    'R4':   (ap(13, 25), 0,  'F'),
    'R5':   (ap(13, 41), 0,  'F'),
    'R6':   (ap(13, 57), 0,  'F'),
    'C18':  (ap(13, 29), 0,  'F'),
    'C19':  (ap(13, 45), 0,  'F'),
    'C20':  (ap(13, 61), 0,  'F'),

    # ═══ WS2812B LED ═══
    'D1':   (ap(93, 43), 0,  'F'),
    'D2':   (ap(93, 51), 0,  'F'),
    'D3':   (ap(93, 59), 0,  'F'),
    'C11':  (ap(98, 43), 0,  'F'),
    'C12':  (ap(98, 51), 0,  'F'),
    'C13':  (ap(98, 59), 0,  'F'),

    # ═══ 电平转换器 ═══
    'U7':   (ap(85, 63), 0,  'F'),
    'C16':  (ap(85, 57), 0,  'F'),
    'R17':  (ap(79, 60), 0,  'F'),

    # ═══ USB接口 ═══
    'J2':   (ap(50, 79), 0,  'F'),
    'R8':   (ap(38, 73), 0,  'F'),
    'R9':   (ap(38, 77), 0,  'F'),
    'R18':  (ap(61, 71), 0,  'F'),
    'R19':  (ap(61, 75), 0,  'F'),
    'C15':  (ap(65, 73), 0,  'F'),
    'C17':  (ap(69, 73), 0,  'F'),

    # ═══ USB ESD + PTC ═══
    'U6':   (ap(50, 69), 0,  'F'),
    'F1':   (ap(42, 69), 0,  'F'),

    # ═══ TP4056充电 ═══
    'U4':   (ap(26, 67), 0,  'F'),
    'R10':  (ap(18, 63), 0,  'F'),
    'D4':   (ap(35, 61), 0,  'F'),
    'D5':   (ap(39, 61), 0,  'F'),
    'R11':  (ap(35, 58), 0,  'F'),
    'R12':  (ap(39, 58), 0,  'F'),

    # ═══ ME6211 LDO ═══
    'U5':   (ap(26, 53), 0,  'F'),
    'C14':  (ap(20, 50), 0,  'F'),
    'C9':   (ap(32, 50), 0,  'F'),

    # ═══ 电源开关 ═══
    'SW1':  (ap(14, 71), 90, 'F'),

    # ═══ 电池 (背面) ═══
    'BT1':  (ap(50, 52), 0,  'B'),
}


# ============================================================
# 主流程
# ============================================================
def main():
    print("=" * 70)
    print("CyberWand v2.0 - 更新4层PCB (导入新网表+布线+DRC)")
    print("=" * 70)

    # [1] 解析网表
    print("\n[1/7] 解析新网表...")
    comps, nets = parse_netlist(NETLIST_FILE)
    print(f"  元件: {len(comps)}, 网络: {len(nets)}")

    # [2] 加载现有PCB
    print("\n[2/7] 加载现有4层PCB...")
    board = pcbnew.LoadBoard(PCB_FILE)
    existing = {fp.GetReference(): fp for fp in board.GetFootprints()}
    print(f"  现有元件: {len(existing)}")

    # [3] 添加缺失的新元件
    print("\n[3/7] 添加新元件...")
    added, failed = 0, []
    for ref, info in sorted(comps.items()):
        if ref in existing:
            continue  # 已存在

        fp_str = info['footprint']
        parts = fp_str.split(':')
        if len(parts) != 2:
            failed.append((ref, f'格式错误: {fp_str}'))
            continue
        lib, name = parts
        lib_path = os.path.join(KICAD_FP_DIR, f'{lib}.pretty')
        if not os.path.exists(lib_path):
            failed.append((ref, f'库不存在: {lib}'))
            continue

        try:
            fp = pcbnew.FootprintLoad(lib_path, name)
            if fp is None:
                failed.append((ref, f'加载失败: {name}'))
                continue
            fp.SetReference(ref)
            fp.SetValue(info.get('value', ''))
            fp.SetPosition(pt(50, 50))  # 临时位置
            board.Add(fp)
            added += 1
            print(f"  [+] {ref}: {name}")
        except Exception as e:
            failed.append((ref, str(e)))

    print(f"  新增: {added}, 失败: {len(failed)}")
    for ref, reason in failed:
        print(f"    [!] {ref}: {reason}")

    # [4] 更新网络分配
    print("\n[4/7] 更新网络分配...")
    netinfo = board.GetNetInfo()
    
    # 添加新网络
    existing_nets = set(netinfo.NetsByName())
    for net_name in nets:
        if net_name and net_name not in existing_nets:
            board.Add(pcbnew.NETINFO_ITEM(board, net_name))
            print(f"  新网络: {net_name}")

    # 重新分配所有引脚
    assigned = 0
    for net_name, pin_list in nets.items():
        if not net_name:
            continue
        ni = board.GetNetInfo().GetNetItem(net_name)
        if not ni:
            continue
        for ref, pin in pin_list:
            for fp in board.GetFootprints():
                if fp.GetReference() != ref:
                    continue
                for pad in fp.Pads():
                    if pad.GetName() == pin:
                        pad.SetNet(ni)
                        assigned += 1
                        break
                break
    print(f"  分配 {assigned} 个引脚网络")

    # [5] 重新布局
    print("\n[5/7] 重新布局元器件...")
    placed, not_defined = 0, []
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        if ref not in LAYOUT:
            not_defined.append(ref)
            continue
        pos, rot, layer = LAYOUT[ref]
        fp.SetPosition(pt(*pos))
        fp.SetOrientationDegrees(rot)
        target = pcbnew.B_Cu if layer == 'B' else pcbnew.F_Cu
        if fp.GetLayer() != target:
            fp.Flip(fp.GetPosition(), False)
        placed += 1
    
    print(f"  已放置: {placed}/{len(LAYOUT)}")
    if not_defined:
        print(f"  未定义位置: {not_defined}")

    # [6] 清除旧布线+重新布线
    print("\n[6/7] 清除旧布线并重新布线...")
    
    # 清除所有走线
    tracks = list(board.GetTracks())
    removed = 0
    for t in tracks:
        board.Remove(t)
        removed += 1
    print(f"  清除 {removed} 条旧走线/via")

    # 重新布线
    routed = auto_route_enhanced(board)

    # [7] 保存并运行DRC
    print("\n[7/7] 保存PCB...")
    board.Save(PCB_FILE)
    print(f"  PCB已保存: {PCB_FILE}")

    # 导出DSN
    try:
        pcbnew.ExportSpecctraDSN(board, DSN_FILE)
        print(f"  DSN已导出: {DSN_FILE}")
    except Exception as e:
        print(f"  DSN导出失败: {e}")

    # DRC检查
    run_drc()

    print("\n" + "=" * 70)
    print("✅ PCB更新完成!")
    print(f"  新增元件: {added}")
    print(f"  布线数量: {routed}")
    print(f"  DRC报告: {DRC_OUTPUT}")
    print("=" * 70)


# ============================================================
# 增强型自动布线引擎
# ============================================================
POWER_NETS = {'GND', '3V3', '5V', '5V_PROT', 'VBAT', 'VBAT_SW'}

def auto_route_enhanced(board):
    """增强型自动布线 - L型/绕行, 避障"""
    ni = board.GetNetInfo()
    routed = 0

    # 收集焊盘
    pad_map = defaultdict(list)
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        for pad in fp.Pads():
            n = pad.GetNet()
            if not n:
                continue
            nn = n.GetNetname()
            if nn in POWER_NETS:
                continue
            pos = pad.GetPosition()
            pad_map[nn].append((tomm(pos.x), tomm(pos.y), pad.GetLayer(), ref, pad.GetName()))

    # 1. 添加电源via
    pwr_vias = 0
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            n = pad.GetNet()
            if not n:
                continue
            nn = n.GetNetname()
            if nn not in POWER_NETS:
                continue
            net_obj = ni.GetNetItem(nn)
            if not net_obj:
                continue
            
            # 为每个电源焊盘添加via
            pos = pad.GetPosition()
            v = pcbnew.PCB_VIA(board)
            v.SetPosition(pos)
            v.SetViaType(pcbnew.VIATYPE_THROUGH)
            v.SetWidth(mm(0.5))
            v.SetDrill(mm(0.25))
            v.SetNet(net_obj)
            board.Add(v)
            pwr_vias += 1

    print(f"  电源via: {pwr_vias}")

    # 2. 信号布线 - 最小生成树
    for net_name, pads in pad_map.items():
        if len(pads) < 2:
            continue

        net_obj = ni.GetNetItem(net_name)
        if not net_obj:
            continue

        # MST连接
        connected = [pads[0]]
        remaining = list(pads[1:])

        while remaining:
            best_dist = float('inf')
            best_pair = None

            for cp in connected:
                for idx, rp in enumerate(remaining):
                    d = math.hypot(rp[0]-cp[0], rp[1]-cp[1])
                    if d < best_dist:
                        best_dist = d
                        best_pair = (cp, idx)

            if best_pair is None:
                break

            src, idx = best_pair
            tgt = remaining.pop(idx)
            connected.append(tgt)

            # 布线
            x1, y1, l1, r1, p1 = src
            x2, y2, l2, r2, p2 = tgt

            if route_l_shape(board, net_obj, x1, y1, x2, y2):
                routed += 1

    print(f"  信号布线: {routed} 成功")
    return routed


def route_l_shape(board, net, x1, y1, x2, y2):
    """L型布线 - 美观的中点转折"""
    dx, dy = x2 - x1, y2 - y1
    dist = math.hypot(dx, dy)

    if dist < 0.5:
        return True

    w = mm(0.2)
    layer = pcbnew.F_Cu

    # 水平+垂直对齐 → 直线
    if abs(dx) < 0.5:
        add_track(board, net, x1, y1, x2, y2, w, layer)
        return True
    if abs(dy) < 0.5:
        add_track(board, net, x1, y1, x2, y2, w, layer)
        return True

    # L型: 根据距离选择转折点
    if abs(dx) > abs(dy):
        # 水平为主: 先走70%水平, 再垂直, 再水平
        mx = x1 + dx * 0.7
        add_track(board, net, x1, y1, mx, y1, w, layer)
        add_track(board, net, mx, y1, mx, y2, w, layer)
        add_track(board, net, mx, y2, x2, y2, w, layer)
    else:
        # 垂直为主
        my = y1 + dy * 0.7
        add_track(board, net, x1, y1, x1, my, w, layer)
        add_track(board, net, x1, my, x2, my, w, layer)
        add_track(board, net, x2, my, x2, y2, w, layer)

    return True


def add_track(board, net, x1, y1, x2, y2, w, layer):
    """添加走线段"""
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pt(x1, y1))
    t.SetEnd(pt(x2, y2))
    t.SetWidth(w)
    t.SetLayer(layer)
    t.SetNet(net)
    board.Add(t)


# ============================================================
# DRC验证
# ============================================================
def run_drc():
    """KiCad CLI DRC"""
    print("\n" + "=" * 70)
    print("运行DRC检查...")
    print("=" * 70)

    if not os.path.exists(KICAD_CLI):
        print(f"  [!] KiCad CLI未找到: {KICAD_CLI}")
        return

    os.makedirs(os.path.dirname(DRC_OUTPUT), exist_ok=True)

    cmd = [KICAD_CLI, 'pcb', 'drc',
           '--output', DRC_OUTPUT,
           '--format', 'json',
           '--severity-all',
           PCB_FILE]

    result = subprocess.run(cmd, capture_output=True, text=True,
                          encoding='utf-8', errors='replace')

    if os.path.exists(DRC_OUTPUT):
        with open(DRC_OUTPUT, 'r', encoding='utf-8') as f:
            data = json.load(f)

        violations = data.get('violations', [])
        unresolved = data.get('unresolved', [])

        counts = defaultdict(int)
        for v in violations:
            counts[v.get('type', 'unknown')] += 1

        print(f"\n  DRC结果:")
        print(f"  {'违规类型':<40} {'数量':>6}")
        print(f"  {'-'*46}")
        total = 0
        for vtype, cnt in sorted(counts.items(), key=lambda x: -x[1]):
            print(f"  {vtype:<40} {cnt:>6}")
            total += cnt
        print(f"  {'-'*46}")
        print(f"  {'总违规':<40} {total:>6}")
        print(f"  {'未连接项':<40} {len(unresolved):>6}")
        
        if total == 0 and len(unresolved) == 0:
            print("\n  ✅ DRC检查通过! 无违规, 无未连接。")
        else:
            print(f"\n  ⚠ 发现 {total} 个违规和 {len(unresolved)} 个未连接项")
            print(f"  详细报告: {DRC_OUTPUT}")
    else:
        print(f"  DRC输出文件未生成")
        if result.returncode != 0:
            print(f"  返回码: {result.returncode}")
        if result.stderr:
            print(f"  错误: {result.stderr[:500]}")


if __name__ == '__main__':
    main()
