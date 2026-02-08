"""
CyberWand - 从网表构建完整4层PCB
功能:
  1. 解析SKiDL网表(.net)
  2. 从KiCad库加载所有封装
  3. 分配网络和引脚
  4. 放置元器件(功能分区)
  5. 设置4层+铜箔区域
  6. 添加电源via
  7. 导出DSN供Freerouter布线
"""

import pcbnew
import os
import sys
import re

sys.stdout.reconfigure(encoding='utf-8')

# ============================================================
# 配置
# ============================================================

KICAD_DIR = r'D:\thinkpad\Documents\cybewand_insta360'
PCB_FILE = os.path.join(KICAD_DIR, 'cyberwand_insta360.kicad_pcb')
NETLIST_FILE = r'D:\win_workspace\CyberWand_Insta360\schematic\skidl\output\cyberwand_netlist.net'
DSN_FILE = os.path.join(KICAD_DIR, 'cyberwand_insta360.dsn')
KICAD_FP_DIR = r'D:\kicad\share\kicad\footprints'

BOARD_W = 100
BOARD_H = 80
BOARD_L = 10
BOARD_T = 10

def mm(val):
    return pcbnew.FromMM(val)

def to_mm(val):
    return pcbnew.ToMM(val)

def abs_pos(rx, ry):
    return (BOARD_L + rx, BOARD_T + ry)


# ============================================================
# 网表解析器
# ============================================================

def parse_netlist(filepath):
    """解析SKiDL生成的KiCad网表(.net)"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    components = {}  # ref -> {footprint, value, ...}
    nets = {}        # net_name -> [(ref, pin), ...]

    # 解析组件 - 匹配 (comp (ref "xxx") ... (footprint "xxx") ...)
    # 先找到所有comp块
    # 使用递进方式: 找(comp开头, 然后逐步解析内部字段
    pos = 0
    while True:
        idx = content.find('(comp\n', pos)
        if idx == -1:
            idx = content.find('(comp ', pos)
        if idx == -1:
            break

        # 找到这个comp块的结束位置
        depth = 0
        end = idx
        for i in range(idx, len(content)):
            if content[i] == '(':
                depth += 1
            elif content[i] == ')':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break

        block = content[idx:end]

        ref_match = re.search(r'\(ref\s+"([^"]+)"\)', block)
        val_match = re.search(r'\(value\s+"([^"]*)"\)', block)
        fp_match = re.search(r'\(footprint\s+"([^"]+)"\)', block)

        if ref_match and fp_match:
            ref = ref_match.group(1)
            fp = fp_match.group(1)
            val = val_match.group(1) if val_match else ''
            components[ref] = {'footprint': fp, 'value': val}

        pos = end

    # 解析网络 - 多行格式
    net_section = content.find('(nets')
    if net_section > 0:
        net_content = content[net_section:]
        pos = 0

        while True:
            idx = net_content.find('(net\n', pos)
            if idx == -1:
                idx = net_content.find('(net ', pos)
            if idx == -1:
                break

            # 找到net块的结束
            depth = 0
            end = idx
            for i in range(idx, min(idx + 5000, len(net_content))):
                if net_content[i] == '(':
                    depth += 1
                elif net_content[i] == ')':
                    depth -= 1
                    if depth == 0:
                        end = i + 1
                        break

            block = net_content[idx:end]
            name_match = re.search(r'\(name\s+"([^"]*)"\)', block)
            if name_match:
                net_name = name_match.group(1)
                # 多行node匹配
                pins = re.findall(
                    r'\(node\s*\n?\s*\(ref\s+"([^"]+)"\)\s*\n?\s*\(pin\s+"([^"]+)"\)',
                    block
                )
                if net_name not in nets:
                    nets[net_name] = []
                nets[net_name].extend(pins)

            pos = end

    return components, nets


# ============================================================
# 元器件布局定义
# ============================================================

LAYOUT = {
    # === ESP32主控 (中心偏左上) ===
    'U1':   {'pos': abs_pos(33, 32), 'rot': 0,    'layer': 'F'},
    'C1':   {'pos': abs_pos(22, 24), 'rot': 0,    'layer': 'F'},
    'C2':   {'pos': abs_pos(22, 27), 'rot': 0,    'layer': 'F'},
    'C3':   {'pos': abs_pos(22, 30), 'rot': 0,    'layer': 'F'},
    'R1':   {'pos': abs_pos(22, 33), 'rot': 0,    'layer': 'F'},
    'R7':   {'pos': abs_pos(22, 36), 'rot': 0,    'layer': 'F'},

    # === LCD (顶部中央) ===
    'LCD1': {'pos': abs_pos(55, 8),  'rot': 90,   'layer': 'F'},
    'C5':   {'pos': abs_pos(65, 5),  'rot': 0,    'layer': 'F'},
    'C6':   {'pos': abs_pos(68, 5),  'rot': 0,    'layer': 'F'},

    # === SPI阻尼 ===
    'R13':  {'pos': abs_pos(44, 16), 'rot': 0,    'layer': 'F'},
    'R14':  {'pos': abs_pos(44, 19), 'rot': 0,    'layer': 'F'},

    # === IMU ===
    'U2':   {'pos': abs_pos(58, 32), 'rot': 0,    'layer': 'F'},
    'C4':   {'pos': abs_pos(66, 32), 'rot': 0,    'layer': 'F'},
    'R2':   {'pos': abs_pos(56, 27), 'rot': 0,    'layer': 'F'},
    'R3':   {'pos': abs_pos(62, 27), 'rot': 0,    'layer': 'F'},

    # === SD卡 ===
    'J1':   {'pos': abs_pos(82, 12), 'rot': 0,    'layer': 'F'},

    # === DFPlayer + Speaker ===
    'U3':   {'pos': abs_pos(82, 32), 'rot': 0,    'layer': 'F'},
    'C7':   {'pos': abs_pos(92, 27), 'rot': 0,    'layer': 'F'},
    'C8':   {'pos': abs_pos(95, 27), 'rot': 0,    'layer': 'F'},
    'LS1':  {'pos': abs_pos(82, 18), 'rot': 0,    'layer': 'B'},

    # === 麦克风 ===
    'MIC1': {'pos': abs_pos(82, 48), 'rot': 0,    'layer': 'F'},
    'C10':  {'pos': abs_pos(90, 48), 'rot': 0,    'layer': 'F'},
    'R15':  {'pos': abs_pos(70, 42), 'rot': 0,    'layer': 'F'},
    'R16':  {'pos': abs_pos(70, 45), 'rot': 0,    'layer': 'F'},

    # === 按键 (左侧) ===
    'SW1':  {'pos': abs_pos(5, 28),  'rot': 0,    'layer': 'F'},
    'SW2':  {'pos': abs_pos(5, 42),  'rot': 0,    'layer': 'F'},
    'SW3':  {'pos': abs_pos(5, 56),  'rot': 0,    'layer': 'F'},
    'R4':   {'pos': abs_pos(13, 26), 'rot': 0,    'layer': 'F'},
    'R5':   {'pos': abs_pos(13, 40), 'rot': 0,    'layer': 'F'},
    'R6':   {'pos': abs_pos(13, 54), 'rot': 0,    'layer': 'F'},
    'C18':  {'pos': abs_pos(13, 30), 'rot': 0,    'layer': 'F'},
    'C19':  {'pos': abs_pos(13, 44), 'rot': 0,    'layer': 'F'},
    'C20':  {'pos': abs_pos(13, 58), 'rot': 0,    'layer': 'F'},

    # === WS2812B LED ===
    'D1':   {'pos': abs_pos(92, 42), 'rot': 0,    'layer': 'F'},
    'D2':   {'pos': abs_pos(92, 50), 'rot': 0,    'layer': 'F'},
    'D3':   {'pos': abs_pos(92, 58), 'rot': 0,    'layer': 'F'},
    'C11':  {'pos': abs_pos(97, 42), 'rot': 0,    'layer': 'F'},
    'C12':  {'pos': abs_pos(97, 50), 'rot': 0,    'layer': 'F'},
    'C13':  {'pos': abs_pos(97, 58), 'rot': 0,    'layer': 'F'},

    # === 电平转换 ===
    'U7':   {'pos': abs_pos(85, 62), 'rot': 0,    'layer': 'F'},
    'C16':  {'pos': abs_pos(85, 56), 'rot': 0,    'layer': 'F'},
    'R17':  {'pos': abs_pos(78, 58), 'rot': 0,    'layer': 'F'},

    # === USB (底部中央) ===
    'J2':   {'pos': abs_pos(50, 74), 'rot': 0,    'layer': 'F'},
    'R8':   {'pos': abs_pos(38, 70), 'rot': 0,    'layer': 'F'},
    'R9':   {'pos': abs_pos(38, 74), 'rot': 0,    'layer': 'F'},
    'R18':  {'pos': abs_pos(60, 68), 'rot': 0,    'layer': 'F'},
    'R19':  {'pos': abs_pos(60, 72), 'rot': 0,    'layer': 'F'},
    'C15':  {'pos': abs_pos(64, 70), 'rot': 0,    'layer': 'F'},
    'C17':  {'pos': abs_pos(68, 70), 'rot': 0,    'layer': 'F'},

    # === USB ESD + PTC ===
    'U6':   {'pos': abs_pos(50, 66), 'rot': 0,    'layer': 'F'},
    'F1':   {'pos': abs_pos(42, 66), 'rot': 0,    'layer': 'F'},

    # === 电源管理 (底部左) ===
    'U4':   {'pos': abs_pos(26, 64), 'rot': 0,    'layer': 'F'},
    'R10':  {'pos': abs_pos(18, 60), 'rot': 0,    'layer': 'F'},
    'D4':   {'pos': abs_pos(34, 58), 'rot': 0,    'layer': 'F'},
    'D5':   {'pos': abs_pos(38, 58), 'rot': 0,    'layer': 'F'},
    'R11':  {'pos': abs_pos(34, 55), 'rot': 0,    'layer': 'F'},
    'R12':  {'pos': abs_pos(38, 55), 'rot': 0,    'layer': 'F'},

    # === LDO ===
    'U5':   {'pos': abs_pos(26, 52), 'rot': 0,    'layer': 'F'},
    'C14':  {'pos': abs_pos(20, 49), 'rot': 0,    'layer': 'F'},
    'C9':   {'pos': abs_pos(32, 49), 'rot': 0,    'layer': 'F'},

    # === 电源开关 ===
    'SW4':  {'pos': abs_pos(14, 68), 'rot': 90,   'layer': 'F'},

    # === 电池(背面) ===
    'BT1':  {'pos': abs_pos(50, 50), 'rot': 0,    'layer': 'B'},
}


def build_pcb():
    """从网表构建完整PCB"""
    print("=" * 60)
    print("CyberWand 4层PCB - 从网表构建")
    print("=" * 60)

    # 1. 解析网表
    print("\n[1/9] 解析网表...")
    components, nets = parse_netlist(NETLIST_FILE)
    print(f"  组件: {len(components)}")
    print(f"  网络: {len(nets)}")

    for ref, info in sorted(components.items()):
        print(f"    {ref}: {info.get('footprint', '?')}")

    # 2. 加载现有PCB或创建新PCB
    print("\n[2/9] 加载/创建PCB...")
    board = None
    try:
        board = pcbnew.LoadBoard(PCB_FILE)
    except Exception as e:
        print(f"  加载失败: {e}")

    if board is None:
        print("  创建新的空白PCB...")
        board = pcbnew.BOARD()

    existing_refs = set()
    try:
        existing_refs = {fp.GetReference() for fp in board.GetFootprints()}
    except:
        pass
    print(f"  现有元件: {len(existing_refs)}")

    # 3. 添加缺失的封装
    print("\n[3/9] 添加缺失封装...")
    added = 0
    for ref, info in components.items():
        if ref in existing_refs:
            continue

        fp_full = info.get('footprint', '')
        if not fp_full:
            print(f"  [!] {ref}: 无封装信息")
            continue

        # 解析库名和封装名
        parts = fp_full.split(':')
        if len(parts) == 2:
            lib_name, fp_name = parts
        else:
            print(f"  [!] {ref}: 封装格式无效: {fp_full}")
            continue

        # 查找封装库路径
        lib_path = os.path.join(KICAD_FP_DIR, f'{lib_name}.pretty')
        if not os.path.exists(lib_path):
            print(f"  [!] {ref}: 封装库不存在: {lib_path}")
            continue

        # 加载封装
        try:
            fp = pcbnew.FootprintLoad(lib_path, fp_name)
            if fp is None:
                print(f"  [!] {ref}: 加载失败: {fp_name}")
                continue

            fp.SetReference(ref)
            val = info.get('value', '')
            if val:
                fp.SetValue(val)

            # 默认位置
            fp.SetPosition(pcbnew.VECTOR2I(mm(50), mm(50)))
            board.Add(fp)
            added += 1
            print(f"  [+] {ref}: {fp_name}")
        except Exception as e:
            print(f"  [!] {ref}: 加载异常: {e}")

    print(f"  新增 {added} 个封装")

    # 移除不需要的旧封装 (H1-H4 安装孔等)
    remove_refs = set()
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        if ref not in components and ref.startswith('H'):
            remove_refs.add(ref)
    # 不移除安装孔, 保留它们

    # 4. 分配网络
    print("\n[4/9] 分配网络...")
    netinfo = board.GetNetInfo()

    # 确保所有网络存在
    existing_nets = set()
    for net in netinfo.NetsByName():
        existing_nets.add(net)

    for net_name in nets:
        if net_name and net_name not in existing_nets:
            new_net = pcbnew.NETINFO_ITEM(board, net_name)
            board.Add(new_net)
            print(f"  新网络: {net_name}")

    # 将引脚分配到网络
    net_assigned = 0
    for net_name, pin_list in nets.items():
        if not net_name:
            continue

        net_item = board.GetNetInfo().GetNetItem(net_name)
        if not net_item:
            continue

        for ref, pin in pin_list:
            for fp in board.GetFootprints():
                if fp.GetReference() != ref:
                    continue
                for pad in fp.Pads():
                    pad_name = pad.GetName()
                    if pad_name == pin or pad_name == str(pin):
                        pad.SetNet(net_item)
                        net_assigned += 1
                        break

    print(f"  分配 {net_assigned} 个引脚网络")

    # 5. 设置板子外框
    print("\n[5/9] 设置板子参数...")

    # 清除旧外框
    to_remove = [s for s in board.GetDrawings() if s.GetLayer() == pcbnew.Edge_Cuts]
    for s in to_remove:
        board.Remove(s)

    # 新外框
    edge = pcbnew.PCB_SHAPE(board)
    edge.SetShape(pcbnew.SHAPE_T_RECT)
    edge.SetStart(pcbnew.VECTOR2I(mm(BOARD_L), mm(BOARD_T)))
    edge.SetEnd(pcbnew.VECTOR2I(mm(BOARD_L + BOARD_W), mm(BOARD_T + BOARD_H)))
    edge.SetLayer(pcbnew.Edge_Cuts)
    edge.SetWidth(mm(0.15))
    board.Add(edge)
    print(f"  板尺寸: {BOARD_W}x{BOARD_H}mm")

    # 6. 设置4层
    print("\n[6/9] 设置4层层叠...")
    settings = board.GetDesignSettings()
    settings.SetCopperLayerCount(4)

    # 设计规则
    settings.m_TrackMinWidth = mm(0.15)
    settings.m_ViasMinSize = mm(0.5)
    settings.m_MinThroughDrill = mm(0.25)
    settings.m_MinClearance = mm(0.15)
    settings.m_HoleToHoleMin = mm(0.25)
    settings.m_CopperEdgeClearance = mm(0.3)

    # KiCad 9: 设计设置通过引用修改, 不需要SetDesignSettings

    enabled = board.GetEnabledLayers()
    enabled.AddLayer(pcbnew.In1_Cu)
    enabled.AddLayer(pcbnew.In2_Cu)
    board.SetEnabledLayers(enabled)

    board.SetLayerName(pcbnew.In1_Cu, "GND_Plane")
    board.SetLayerName(pcbnew.In2_Cu, "PWR_3V3")
    print("  4层: F.Cu / GND_Plane / PWR_3V3 / B.Cu")

    # 7. 放置元器件
    print("\n[7/9] 放置元器件...")
    placed = 0
    not_found = []
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        if ref in LAYOUT:
            info = LAYOUT[ref]
            x, y = info['pos']
            rot = info['rot']
            layer = info['layer']

            fp.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
            fp.SetOrientationDegrees(rot)

            if layer == 'B' and fp.GetLayer() != pcbnew.B_Cu:
                fp.Flip(fp.GetPosition(), False)
            elif layer == 'F' and fp.GetLayer() != pcbnew.F_Cu:
                fp.Flip(fp.GetPosition(), False)

            placed += 1
        else:
            not_found.append(ref)

    print(f"  已放置 {placed} 个元件")
    if not_found:
        print(f"  未定义位置: {not_found}")

    # 8. 清除旧走线和铜箔区域, 设置新的
    print("\n[8/9] 设置铜箔区域...")

    # 清除旧走线
    tracks = list(board.GetTracks())
    for t in tracks:
        board.Remove(t)
    print(f"  清除 {len(tracks)} 条旧走线")

    # 清除旧zone
    zones_to_remove = []
    for i in range(board.GetAreaCount()):
        zones_to_remove.append(board.GetArea(i))
    for z in zones_to_remove:
        board.Remove(z)
    print(f"  清除 {len(zones_to_remove)} 个旧铜箔区域")

    # 查找GND和3V3网络
    gnd_net = board.GetNetInfo().GetNetItem('GND')
    pwr_net = board.GetNetInfo().GetNetItem('3V3')

    margin = 0.5
    x1, y1 = BOARD_L + margin, BOARD_T + margin
    x2, y2 = BOARD_L + BOARD_W - margin, BOARD_T + BOARD_H - margin

    def make_zone(net, layer, name):
        zone = pcbnew.ZONE(board)
        zone.SetNet(net)
        zone.SetLayer(layer)
        zone.SetZoneName(name)

        poly = pcbnew.SHAPE_POLY_SET()
        poly.NewOutline()
        poly.Append(mm(x1), mm(y1))
        poly.Append(mm(x2), mm(y1))
        poly.Append(mm(x2), mm(y2))
        poly.Append(mm(x1), mm(y2))
        zone.SetOutline(poly)

        zone.SetMinThickness(mm(0.2))
        zone.SetThermalReliefGap(mm(0.3))
        zone.SetThermalReliefSpokeWidth(mm(0.3))
        zone.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)

        board.Add(zone)
        return zone

    if gnd_net:
        make_zone(gnd_net, pcbnew.In1_Cu, "GND_Plane")
        make_zone(gnd_net, pcbnew.F_Cu, "GND_F")
        make_zone(gnd_net, pcbnew.B_Cu, "GND_B")
        print("  GND平面: In1.Cu + F.Cu + B.Cu")

    if pwr_net:
        make_zone(pwr_net, pcbnew.In2_Cu, "3V3_Plane")
        print("  3V3平面: In2.Cu")

    # 添加GND缝合via
    if gnd_net:
        via_count = 0
        for x in range(int(BOARD_L + 3), int(BOARD_L + BOARD_W - 2), 8):
            for y in [BOARD_T + 3, BOARD_T + BOARD_H - 3]:
                via = pcbnew.PCB_VIA(board)
                via.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
                via.SetViaType(pcbnew.VIATYPE_THROUGH)
                via.SetWidth(mm(0.5))
                via.SetDrill(mm(0.25))
                via.SetNet(gnd_net)
                board.Add(via)
                via_count += 1
        for y in range(int(BOARD_T + 3), int(BOARD_T + BOARD_H - 2), 8):
            for x in [BOARD_L + 3, BOARD_L + BOARD_W - 3]:
                via = pcbnew.PCB_VIA(board)
                via.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
                via.SetViaType(pcbnew.VIATYPE_THROUGH)
                via.SetWidth(mm(0.5))
                via.SetDrill(mm(0.25))
                via.SetNet(gnd_net)
                board.Add(via)
                via_count += 1
        print(f"  添加 {via_count} 个GND缝合via")

    # 9. 保存并导出DSN
    print("\n[9/9] 保存并导出...")
    board.Save(PCB_FILE)
    print(f"  PCB保存: {PCB_FILE}")

    # 导出DSN
    try:
        pcbnew.ExportSpecctraDSN(board, DSN_FILE)
        print(f"  DSN导出: {DSN_FILE}")
    except Exception as e:
        print(f"  DSN导出失败: {e}")
        print("  请在KiCad中手动导出: 文件 -> 导出 -> Specctra DSN")

    # 统计
    print("\n" + "=" * 60)
    print("构建完成! 统计:")
    fp_count = len(list(board.GetFootprints()))
    net_count = board.GetNetCount()
    print(f"  元件: {fp_count}")
    print(f"  网络: {net_count}")
    print(f"  PCB: {PCB_FILE}")
    print(f"  DSN: {DSN_FILE}")

    print(f"\n下一步: 使用Freerouter进行自动布线")
    print(f"  D:\\freerouter\\freerouter.bat -gui.enabled=false -de \"{DSN_FILE}\" -do \"{SES_FILE}\"")
    print(f"\n布线完成后: 导入SES文件")
    print(f"  在KiCad中: 文件 -> 导入 -> Specctra Session")
    print("=" * 60)


if __name__ == '__main__':
    build_pcb()
