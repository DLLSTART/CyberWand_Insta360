"""
CyberWand v2.0 - 完整PCB构建+布线+验证流水线
使用 KiCad Python API (pcbnew) 从网表直接构建4层PCB

步骤:
  1. 解析SKiDL网表
  2. 创建全新PCB, 加载所有封装
  3. 分配网络到引脚
  4. 功能分区布局
  5. 4层层叠+铜箔区域
  6. 自动布线(美观L型/弧型)
  7. DRC验证
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
# 路径配置
# ============================================================
KICAD_PROJECT = r'D:\thinkpad\Documents\cybewand_insta360'
PCB_FILE = os.path.join(KICAD_PROJECT, 'cybewand_insta360.kicad_pcb')
NETLIST_FILE = r'D:\win_workspace\CyberWand_Insta360\schematic\skidl\output\cyberwand_netlist.net'
KICAD_FP_DIR = r'D:\kicad\share\kicad\footprints'
KICAD_CLI = r'D:\kicad\bin\kicad-cli.exe'
DRC_OUTPUT = r'D:\win_workspace\CyberWand_Insta360\schematic\skidl\docs\DRC_v2.json'
DSN_FILE = os.path.join(KICAD_PROJECT, 'cyberwand_insta360.dsn')

# 板子参数
BL, BT = 10, 10  # 左上角偏移
BW, BH = 100, 85  # 板宽/高 mm

def mm(v): return pcbnew.FromMM(v)
def tomm(v): return pcbnew.ToMM(v)
def pt(x, y): return pcbnew.VECTOR2I(mm(x), mm(y))
def ap(rx, ry): return (BL + rx, BT + ry)  # 相对→绝对坐标

# ============================================================
# 1. 网表解析
# ============================================================
def parse_netlist(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    components = {}
    # 解析comp块
    pos = 0
    while True:
        idx = content.find('(comp\n', pos)
        if idx == -1:
            idx = content.find('(comp ', pos)
        if idx == -1:
            break
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

    nets = {}
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
# 2. 布局定义 - 功能分区
# ============================================================
# 策略: ESP32居中, LCD上方, 电源底部, 按键左侧, LED/音频右侧
# 注意: SW1=电源SPDT, SW2/SW3/SW4=按键

LAYOUT = {
    # ═══ ESP32主控区 (中心) ═══
    'U1':   (ap(35, 33), 0, 'F'),    # ESP32-S3
    'C1':   (ap(23, 22), 0, 'F'),    # ESP32去耦
    'C2':   (ap(23, 25), 0, 'F'),
    'C3':   (ap(23, 28), 0, 'F'),
    'R1':   (ap(23, 31), 0, 'F'),    # EN上拉
    'R7':   (ap(23, 34), 0, 'F'),    # IO46下拉

    # ═══ LCD显示屏 (顶部) ═══
    'LCD1': (ap(55, 8),  90, 'F'),
    'C5':   (ap(66, 4),  0,  'F'),
    'C6':   (ap(70, 4),  0,  'F'),

    # ═══ SPI阻尼电阻 ═══
    'R13':  (ap(44, 16), 0,  'F'),   # SCK阻尼
    'R14':  (ap(44, 19), 0,  'F'),   # MOSI阻尼

    # ═══ MPU6050 (ESP32右侧) ═══
    'U2':   (ap(60, 33), 0,  'F'),
    'C4':   (ap(68, 33), 0,  'F'),
    'R2':   (ap(58, 27), 0,  'F'),   # I2C SDA上拉
    'R3':   (ap(63, 27), 0,  'F'),   # I2C SCL上拉

    # ═══ SD卡 (右上) ═══
    'J1':   (ap(85, 12), 0,  'F'),

    # ═══ DFPlayer + 扬声器 (右中上) ═══
    'U3':   (ap(83, 33), 0,  'F'),
    'C7':   (ap(93, 28), 0,  'F'),
    'C8':   (ap(96, 28), 0,  'F'),
    'LS1':  (ap(83, 18), 0,  'B'),   # 扬声器(背面)

    # ═══ INMP441麦克风 (右中) ═══
    'MIC1': (ap(83, 50), 0,  'F'),
    'C10':  (ap(91, 50), 0,  'F'),
    'R15':  (ap(72, 42), 0,  'F'),   # I2S SCK阻尼
    'R16':  (ap(72, 45), 0,  'F'),   # I2S WS阻尼

    # ═══ 按键 (左侧垂直排列) ═══
    'SW2':  (ap(5, 26),  0,  'F'),   # 模式按键
    'SW3':  (ap(5, 42),  0,  'F'),   # 选择按键
    'SW4':  (ap(5, 58),  0,  'F'),   # 播放按键
    'R4':   (ap(13, 24), 0,  'F'),
    'R5':   (ap(13, 40), 0,  'F'),
    'R6':   (ap(13, 56), 0,  'F'),
    'C18':  (ap(13, 28), 0,  'F'),   # 去抖电容
    'C19':  (ap(13, 44), 0,  'F'),
    'C20':  (ap(13, 60), 0,  'F'),

    # ═══ WS2812B LED (右下) ═══
    'D1':   (ap(92, 42), 0,  'F'),
    'D2':   (ap(92, 50), 0,  'F'),
    'D3':   (ap(92, 58), 0,  'F'),
    'C11':  (ap(97, 42), 0,  'F'),
    'C12':  (ap(97, 50), 0,  'F'),
    'C13':  (ap(97, 58), 0,  'F'),

    # ═══ 电平转换器 (LED附近) ═══
    'U7':   (ap(84, 62), 0,  'F'),
    'C16':  (ap(84, 56), 0,  'F'),
    'R17':  (ap(78, 59), 0,  'F'),   # LED 100Ω串联

    # ═══ USB接口 (底部中央) ═══
    'J2':   (ap(50, 78), 0,  'F'),
    'R8':   (ap(38, 72), 0,  'F'),   # CC1
    'R9':   (ap(38, 76), 0,  'F'),   # CC2
    'R18':  (ap(60, 70), 0,  'F'),   # USB D+ 22Ω
    'R19':  (ap(60, 74), 0,  'F'),   # USB D- 22Ω
    'C15':  (ap(64, 72), 0,  'F'),   # USB 10uF
    'C17':  (ap(68, 72), 0,  'F'),   # VBUS 22uF

    # ═══ USB ESD + PTC (USB旁) ═══
    'U6':   (ap(50, 68), 0,  'F'),   # ESD保护
    'F1':   (ap(42, 68), 0,  'F'),   # PTC保险丝

    # ═══ TP4056充电 (底部左) ═══
    'U4':   (ap(26, 66), 0,  'F'),
    'R10':  (ap(18, 62), 0,  'F'),   # PROG
    'D4':   (ap(35, 60), 0,  'F'),   # 红色LED
    'D5':   (ap(39, 60), 0,  'F'),   # 绿色LED
    'R11':  (ap(35, 57), 0,  'F'),
    'R12':  (ap(39, 57), 0,  'F'),

    # ═══ ME6211 LDO (中下左) ═══
    'U5':   (ap(26, 52), 0,  'F'),
    'C14':  (ap(20, 49), 0,  'F'),   # LDO输入
    'C9':   (ap(32, 49), 0,  'F'),   # LDO输出

    # ═══ 电源开关 (左下) ═══
    'SW1':  (ap(14, 70), 90, 'F'),

    # ═══ 电池 (背面中央) ═══
    'BT1':  (ap(50, 50), 0,  'B'),
}


# ============================================================
# 3. 主构建流程
# ============================================================
def build():
    print("=" * 60)
    print("CyberWand v2.0 - 4层PCB完整构建")
    print("=" * 60)

    # --- 解析网表 ---
    print("\n[1/8] 解析网表...")
    comps, nets = parse_netlist(NETLIST_FILE)
    print(f"  元件: {len(comps)}, 网络: {len(nets)}")

    # --- 创建空白PCB ---
    print("\n[2/8] 创建PCB...")
    board = pcbnew.BOARD()

    # --- 加载封装 ---
    print("\n[3/8] 加载封装...")
    loaded, failed = 0, []
    for ref, info in sorted(comps.items()):
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
            fp.SetPosition(pt(50, 50))
            board.Add(fp)
            loaded += 1
        except Exception as e:
            failed.append((ref, str(e)))

    print(f"  成功: {loaded}, 失败: {len(failed)}")
    for ref, reason in failed:
        print(f"    [!] {ref}: {reason}")

    # --- 添加网络并分配引脚 ---
    print("\n[4/8] 分配网络...")
    for net_name in nets:
        if net_name:
            board.Add(pcbnew.NETINFO_ITEM(board, net_name))

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
    print(f"  分配 {assigned} 个引脚")

    # --- 布局 ---
    print("\n[5/8] 元器件布局...")
    placed = 0
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        if ref not in LAYOUT:
            continue
        pos, rot, layer = LAYOUT[ref]
        fp.SetPosition(pt(*pos))
        fp.SetOrientationDegrees(rot)
        target = pcbnew.B_Cu if layer == 'B' else pcbnew.F_Cu
        if fp.GetLayer() != target:
            fp.Flip(fp.GetPosition(), False)
        placed += 1
    print(f"  已放置 {placed}/{len(LAYOUT)}")

    # --- 板子设置 ---
    print("\n[6/8] 板子设置...")
    # 外框
    edge = pcbnew.PCB_SHAPE(board)
    edge.SetShape(pcbnew.SHAPE_T_RECT)
    edge.SetStart(pt(BL, BT))
    edge.SetEnd(pt(BL + BW, BT + BH))
    edge.SetLayer(pcbnew.Edge_Cuts)
    edge.SetWidth(mm(0.15))
    board.Add(edge)

    # 4层
    ds = board.GetDesignSettings()
    ds.SetCopperLayerCount(4)
    ds.m_TrackMinWidth = mm(0.15)
    ds.m_ViasMinSize = mm(0.5)
    ds.m_MinThroughDrill = mm(0.25)
    ds.m_MinClearance = mm(0.15)
    ds.m_HoleToHoleMin = mm(0.25)
    ds.m_CopperEdgeClearance = mm(0.3)

    enabled = board.GetEnabledLayers()
    enabled.AddLayer(pcbnew.In1_Cu)
    enabled.AddLayer(pcbnew.In2_Cu)
    board.SetEnabledLayers(enabled)
    board.SetLayerName(pcbnew.In1_Cu, "GND_Plane")
    board.SetLayerName(pcbnew.In2_Cu, "PWR_3V3")
    print(f"  板尺寸: {BW}x{BH}mm, 4层")

    # 铜箔区域
    m = 0.5
    x1, y1, x2, y2 = BL+m, BT+m, BL+BW-m, BT+BH-m

    gnd_net = board.GetNetInfo().GetNetItem('GND')
    pwr_net = board.GetNetInfo().GetNetItem('3V3')

    def add_zone(net, layer, name):
        z = pcbnew.ZONE(board)
        z.SetNet(net)
        z.SetLayer(layer)
        z.SetZoneName(name)
        p = pcbnew.SHAPE_POLY_SET()
        p.NewOutline()
        p.Append(mm(x1), mm(y1))
        p.Append(mm(x2), mm(y1))
        p.Append(mm(x2), mm(y2))
        p.Append(mm(x1), mm(y2))
        z.SetOutline(p)
        z.SetMinThickness(mm(0.2))
        z.SetThermalReliefGap(mm(0.3))
        z.SetThermalReliefSpokeWidth(mm(0.3))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        board.Add(z)

    if gnd_net:
        add_zone(gnd_net, pcbnew.In1_Cu, "GND_Plane")
        add_zone(gnd_net, pcbnew.F_Cu, "GND_F")
        add_zone(gnd_net, pcbnew.B_Cu, "GND_B")
    if pwr_net:
        add_zone(pwr_net, pcbnew.In2_Cu, "3V3_Plane")
    print("  铜箔区域: GND(In1+F+B) + 3V3(In2)")

    # GND缝合via
    if gnd_net:
        vc = 0
        for x in range(BL+3, BL+BW-2, 8):
            for y in [BT+3, BT+BH-3]:
                v = pcbnew.PCB_VIA(board)
                v.SetPosition(pt(x, y))
                v.SetViaType(pcbnew.VIATYPE_THROUGH)
                v.SetWidth(mm(0.5))
                v.SetDrill(mm(0.25))
                v.SetNet(gnd_net)
                board.Add(v)
                vc += 1
        for y in range(BT+3, BT+BH-2, 8):
            for x in [BL+3, BL+BW-3]:
                v = pcbnew.PCB_VIA(board)
                v.SetPosition(pt(x, y))
                v.SetViaType(pcbnew.VIATYPE_THROUGH)
                v.SetWidth(mm(0.5))
                v.SetDrill(mm(0.25))
                v.SetNet(gnd_net)
                board.Add(v)
                vc += 1
        print(f"  GND缝合via: {vc}")

    # --- 自动布线 ---
    print("\n[7/8] 自动布线...")
    route_count = auto_route(board, nets)

    # --- 保存+导出 ---
    print("\n[8/8] 保存...")
    board.Save(PCB_FILE)
    print(f"  PCB: {PCB_FILE}")

    # 导出DSN
    try:
        pcbnew.ExportSpecctraDSN(board, DSN_FILE)
        print(f"  DSN: {DSN_FILE}")
    except Exception as e:
        print(f"  DSN导出: {e}")

    # DRC
    run_drc()

    print("\n" + "=" * 60)
    print("构建完成!")
    print(f"  元件: {loaded}")
    print(f"  网络: {len(nets)}")
    print(f"  布线: {route_count}")
    print("=" * 60)


# ============================================================
# 4. 自动布线引擎
# ============================================================
POWER_NETS = {'GND', '3V3', '5V', '5V_PROT', 'VBAT', 'VBAT_SW'}
TRACE_W = 0.2     # 信号线宽 mm
PWR_W = 0.35       # 电源线宽 mm

def auto_route(board, nets):
    """智能自动布线 - L型/U型路径, 美观绕行"""
    ni = board.GetNetInfo()
    routed = 0
    unrouted = []

    # 收集焊盘位置
    pad_map = defaultdict(list)  # net -> [(x,y,layer,ref)]
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        for pad in fp.Pads():
            n = pad.GetNet()
            if not n:
                continue
            nn = n.GetNetname()
            if nn in POWER_NETS:
                continue  # 电源由平面处理
            pos = pad.GetPosition()
            pad_map[nn].append((tomm(pos.x), tomm(pos.y),
                               pad.GetLayer(), ref))

    # 添加电源via
    pwr_vias = 0
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            n = pad.GetNet()
            if not n: continue
            nn = n.GetNetname()
            if nn not in POWER_NETS: continue
            net_obj = ni.GetNetItem(nn)
            if not net_obj: continue
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

    # 对每个信号网络布线
    for net_name, pads in pad_map.items():
        if len(pads) < 2:
            continue

        net_obj = ni.GetNetItem(net_name)
        if not net_obj:
            continue

        # 使用最小生成树连接多个焊盘
        connected = [pads[0]]
        remaining = list(pads[1:])

        while remaining:
            best_dist = float('inf')
            best_from = None
            best_to_idx = None

            for ci, cp in enumerate(connected):
                for ri, rp in enumerate(remaining):
                    d = math.hypot(rp[0]-cp[0], rp[1]-cp[1])
                    if d < best_dist:
                        best_dist = d
                        best_from = cp
                        best_to_idx = ri

            if best_to_idx is None:
                break

            target = remaining.pop(best_to_idx)
            connected.append(target)

            x1, y1, l1, r1 = best_from
            x2, y2, l2, r2 = target
            w = mm(TRACE_W)
            layer = pcbnew.F_Cu  # 默认正面

            success = route_pair(board, net_obj, x1, y1, x2, y2, w, layer)
            if success:
                routed += 1
            else:
                unrouted.append(f"{net_name}: {r1}->{r2}")

    print(f"  信号布线: {routed} 成功")
    if unrouted:
        print(f"  未布线: {len(unrouted)}")
        for u in unrouted[:10]:
            print(f"    {u}")
        if len(unrouted) > 10:
            print(f"    ... 还有 {len(unrouted)-10} 条")

    return routed


def route_pair(board, net, x1, y1, x2, y2, w, layer):
    """在两点间布线 - 使用美观的L型路径"""
    dx = x2 - x1
    dy = y2 - y1
    dist = math.hypot(dx, dy)

    if dist < 0.1:
        return True  # 太近, 不需要布线

    # 策略1: 直线 (如果水平或垂直对齐)
    if abs(dx) < 0.5 or abs(dy) < 0.5:
        add_track(board, net, x1, y1, x2, y2, w, layer)
        return True

    # 策略2: L型路径 (先水平后垂直, 或反过来)
    # 选择中点偏移使路径更美观
    if abs(dx) > abs(dy):
        # 先水平走一半, 再垂直, 再水平
        mx = x1 + dx * 0.5
        add_track(board, net, x1, y1, mx, y1, w, layer)
        add_track(board, net, mx, y1, mx, y2, w, layer)
        add_track(board, net, mx, y2, x2, y2, w, layer)
    else:
        # 先垂直走一半, 再水平, 再垂直
        my = y1 + dy * 0.5
        add_track(board, net, x1, y1, x1, my, w, layer)
        add_track(board, net, x1, my, x2, my, w, layer)
        add_track(board, net, x2, my, x2, y2, w, layer)

    return True


def add_track(board, net, x1, y1, x2, y2, w, layer):
    """添加一段走线"""
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pt(x1, y1))
    t.SetEnd(pt(x2, y2))
    t.SetWidth(w)
    t.SetLayer(layer)
    t.SetNet(net)
    board.Add(t)


# ============================================================
# 5. DRC验证
# ============================================================
def run_drc():
    """使用KiCad CLI运行DRC"""
    print("\n运行DRC检查...")

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
        print(f"  {'类型':<35} {'数量':>5}")
        print(f"  {'-'*40}")
        total = 0
        for t, c in sorted(counts.items(), key=lambda x: -x[1]):
            print(f"  {t:<35} {c:>5}")
            total += c
        print(f"  {'-'*40}")
        print(f"  {'总违规':<35} {total:>5}")
        print(f"  {'未连接':<35} {len(unresolved):>5}")
    else:
        print(f"  DRC输出文件未生成")
        if result.stderr:
            print(f"  错误: {result.stderr[:300]}")


# ============================================================
# Main
# ============================================================
if __name__ == '__main__':
    build()
