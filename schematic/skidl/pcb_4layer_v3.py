"""
CyberWand 4层PCB布局脚本 v3.0
功能:
  1. 从网表创建/更新PCB
  2. 设置4层层叠
  3. 智能元器件布局 (充足间距, 功能分区)
  4. 设置铜箔区域 (GND+3V3内层平面)
  5. 设置设计规则
  6. 导出DSN文件供Freerouter使用
  7. 导入Freerouter布线结果(SES)
  8. 基础Python布线 (简单连接)

使用方法:
  python pcb_4layer_v3.py --step layout    # 布局+导出DSN
  python pcb_4layer_v3.py --step import    # 导入SES
  python pcb_4layer_v3.py --step drc       # 运行DRC
"""

import pcbnew
import os
import sys
import argparse
import math

# ============================================================
# 配置
# ============================================================

KICAD_DIR = r'D:\thinkpad\Documents\cybewand_insta360'
PCB_FILE = os.path.join(KICAD_DIR, 'cybewand_insta360.kicad_pcb')
NETLIST_FILE = r'D:\win_workspace\CyberWand_Insta360\schematic\skidl\output\cyberwand_netlist.net'
DSN_FILE = os.path.join(KICAD_DIR, 'cyberwand_insta360.dsn')
SES_FILE = os.path.join(KICAD_DIR, 'cyberwand_insta360.ses')
DRC_FILE = r'D:\win_workspace\CyberWand_Insta360\schematic\skidl\docs\DRC_4layer_v3.json'

# 板子参数
BOARD_W = 100     # 宽度 mm
BOARD_H = 80      # 高度 mm (更紧凑的设计)
BOARD_L = 10      # 左边界 mm
BOARD_T = 10      # 上边界 mm

def mm(val):
    """毫米转KiCad内部单位"""
    return pcbnew.FromMM(val)

def to_mm(val):
    """KiCad内部单位转毫米"""
    return pcbnew.ToMM(val)

# ============================================================
# 元器件布局定义 (功能分区, 充足间距)
# ============================================================
# 布局策略:
#   - 顶部: LCD显示屏 (大型排针接口)
#   - 中部左: ESP32主控 (核心, 居中偏左)
#   - 中部右: 传感器+音频
#   - 底部: 电源管理+USB接口
#   - 左侧: 按键
#   - 右侧: LED+保护组件
#
# 坐标系: 原点在板子左上角 (BOARD_L, BOARD_T)

def abs_pos(rx, ry):
    """相对坐标转绝对坐标"""
    return (BOARD_L + rx, BOARD_T + ry)

LAYOUT = {
    # === 主控区域 (中心, 充分空间给天线) ===
    'U1':   {'pos': abs_pos(35, 35), 'rot': 0,    'layer': 'F'},   # ESP32-S3 (核心)
    'C1':   {'pos': abs_pos(25, 25), 'rot': 0,    'layer': 'F'},   # ESP32去耦1 (靠近3V3引脚)
    'C2':   {'pos': abs_pos(25, 28), 'rot': 0,    'layer': 'F'},   # ESP32去耦2
    'C3':   {'pos': abs_pos(25, 31), 'rot': 0,    'layer': 'F'},   # ESP32去耦3
    'R1':   {'pos': abs_pos(25, 34), 'rot': 0,    'layer': 'F'},   # EN上拉
    'R7':   {'pos': abs_pos(25, 37), 'rot': 0,    'layer': 'F'},   # IO46下拉

    # === LCD显示屏 (顶部中央) ===
    'LCD1': {'pos': abs_pos(50, 8),  'rot': 90,   'layer': 'F'},   # LCD排针
    'C5':   {'pos': abs_pos(60, 5),  'rot': 0,    'layer': 'F'},   # LCD去耦1
    'C6':   {'pos': abs_pos(63, 5),  'rot': 0,    'layer': 'F'},   # LCD去耦2

    # === SPI阻尼电阻 (ESP32和LCD之间) ===
    'R13':  {'pos': abs_pos(42, 18), 'rot': 0,    'layer': 'F'},   # SPI_SCK阻尼
    'R14':  {'pos': abs_pos(42, 21), 'rot': 0,    'layer': 'F'},   # SPI_MOSI阻尼

    # === IMU传感器 (ESP32右侧) ===
    'U2':   {'pos': abs_pos(58, 35), 'rot': 0,    'layer': 'F'},   # MPU6050
    'C4':   {'pos': abs_pos(64, 35), 'rot': 0,    'layer': 'F'},   # MPU6050去耦
    'R2':   {'pos': abs_pos(58, 30), 'rot': 0,    'layer': 'F'},   # I2C SDA上拉
    'R3':   {'pos': abs_pos(62, 30), 'rot': 0,    'layer': 'F'},   # I2C SCL上拉

    # === SD卡 (LCD旁边) ===
    'J1':   {'pos': abs_pos(80, 15), 'rot': 0,    'layer': 'F'},   # SD卡座

    # === DFPlayer + 扬声器 (右上) ===
    'U3':   {'pos': abs_pos(80, 35), 'rot': 0,    'layer': 'F'},   # DFPlayer Mini
    'C7':   {'pos': abs_pos(90, 30), 'rot': 0,    'layer': 'F'},   # DFPlayer去耦1(10uF)
    'C8':   {'pos': abs_pos(93, 30), 'rot': 0,    'layer': 'F'},   # DFPlayer去耦2(100nF)
    'LS1':  {'pos': abs_pos(80, 20), 'rot': 0,    'layer': 'B'},   # 扬声器(背面)

    # === 麦克风 (右中) ===
    'MIC1': {'pos': abs_pos(80, 50), 'rot': 0,    'layer': 'F'},   # INMP441
    'C10':  {'pos': abs_pos(86, 50), 'rot': 0,    'layer': 'F'},   # 麦克风去耦
    'R15':  {'pos': abs_pos(68, 45), 'rot': 0,    'layer': 'F'},   # I2S_SCK阻尼
    'R16':  {'pos': abs_pos(68, 48), 'rot': 0,    'layer': 'F'},   # I2S_WS阻尼

    # === 按键 (左侧, 垂直排列) ===
    'SW1':  {'pos': abs_pos(5, 30),  'rot': 0,    'layer': 'F'},   # 模式按键
    'SW2':  {'pos': abs_pos(5, 45),  'rot': 0,    'layer': 'F'},   # 选择按键
    'SW3':  {'pos': abs_pos(5, 60),  'rot': 0,    'layer': 'F'},   # 播放按键
    'R4':   {'pos': abs_pos(12, 28), 'rot': 0,    'layer': 'F'},   # 按键1上拉
    'R5':   {'pos': abs_pos(12, 43), 'rot': 0,    'layer': 'F'},   # 按键2上拉
    'R6':   {'pos': abs_pos(12, 58), 'rot': 0,    'layer': 'F'},   # 按键3上拉
    'C18':  {'pos': abs_pos(12, 31), 'rot': 0,    'layer': 'F'},   # 按键1去抖
    'C19':  {'pos': abs_pos(12, 46), 'rot': 0,    'layer': 'F'},   # 按键2去抖
    'C20':  {'pos': abs_pos(12, 61), 'rot': 0,    'layer': 'F'},   # 按键3去抖

    # === WS2812B LED (右侧, 垂直排列) ===
    'D1':   {'pos': abs_pos(92, 45), 'rot': 0,    'layer': 'F'},   # LED1
    'D2':   {'pos': abs_pos(92, 52), 'rot': 0,    'layer': 'F'},   # LED2
    'D3':   {'pos': abs_pos(92, 59), 'rot': 0,    'layer': 'F'},   # LED3
    'C11':  {'pos': abs_pos(96, 45), 'rot': 0,    'layer': 'F'},   # LED1去耦
    'C12':  {'pos': abs_pos(96, 52), 'rot': 0,    'layer': 'F'},   # LED2去耦
    'C13':  {'pos': abs_pos(96, 59), 'rot': 0,    'layer': 'F'},   # LED3去耦

    # === 电平转换器 (LED附近) ===
    'U7':   {'pos': abs_pos(85, 60), 'rot': 0,    'layer': 'F'},   # 74AHCT125
    'C16':  {'pos': abs_pos(85, 55), 'rot': 0,    'layer': 'F'},   # 电平转换去耦
    'R17':  {'pos': abs_pos(78, 58), 'rot': 0,    'layer': 'F'},   # LED数据串联100Ω

    # === USB接口 (底部中央) ===
    'J2':   {'pos': abs_pos(50, 75), 'rot': 0,    'layer': 'F'},   # USB Type-C
    'R8':   {'pos': abs_pos(40, 72), 'rot': 0,    'layer': 'F'},   # CC1电阻
    'R9':   {'pos': abs_pos(40, 75), 'rot': 0,    'layer': 'F'},   # CC2电阻
    'R18':  {'pos': abs_pos(58, 70), 'rot': 0,    'layer': 'F'},   # USB D+ 22Ω
    'R19':  {'pos': abs_pos(58, 73), 'rot': 0,    'layer': 'F'},   # USB D- 22Ω
    'C15':  {'pos': abs_pos(62, 72), 'rot': 0,    'layer': 'F'},   # USB滤波10uF
    'C17':  {'pos': abs_pos(65, 72), 'rot': 0,    'layer': 'F'},   # VBUS储能22uF

    # === USB ESD保护 (USB接口旁) ===
    'U6':   {'pos': abs_pos(50, 68), 'rot': 0,    'layer': 'F'},   # USBLC6-2SC6
    'F1':   {'pos': abs_pos(44, 68), 'rot': 0,    'layer': 'F'},   # PTC保险丝

    # === 电源管理 (底部) ===
    'U4':   {'pos': abs_pos(25, 65), 'rot': 0,    'layer': 'F'},   # TP4056
    'R10':  {'pos': abs_pos(20, 60), 'rot': 0,    'layer': 'F'},   # PROG电阻
    'D4':   {'pos': abs_pos(33, 60), 'rot': 0,    'layer': 'F'},   # 充电LED(红)
    'D5':   {'pos': abs_pos(36, 60), 'rot': 0,    'layer': 'F'},   # 充满LED(绿)
    'R11':  {'pos': abs_pos(33, 57), 'rot': 0,    'layer': 'F'},   # LED红限流
    'R12':  {'pos': abs_pos(36, 57), 'rot': 0,    'layer': 'F'},   # LED绿限流

    # === LDO稳压 ===
    'U5':   {'pos': abs_pos(25, 55), 'rot': 0,    'layer': 'F'},   # ME6211
    'C14':  {'pos': abs_pos(20, 52), 'rot': 0,    'layer': 'F'},   # LDO输入电容
    'C9':   {'pos': abs_pos(30, 52), 'rot': 0,    'layer': 'F'},   # LDO输出电容

    # === 电源开关 (电池旁) ===
    'SW4':  {'pos': abs_pos(15, 70), 'rot': 90,   'layer': 'F'},   # 电源开关

    # === 电池 (背面中央) ===
    'BT1':  {'pos': abs_pos(50, 55), 'rot': 0,    'layer': 'B'},   # 锂电池 (背面)
}


def setup_board_outline(board):
    """设置板子外框"""
    edge = pcbnew.PCB_SHAPE(board)
    edge.SetShape(pcbnew.SHAPE_T_RECT)
    edge.SetStart(pcbnew.VECTOR2I(mm(BOARD_L), mm(BOARD_T)))
    edge.SetEnd(pcbnew.VECTOR2I(mm(BOARD_L + BOARD_W), mm(BOARD_T + BOARD_H)))
    edge.SetLayer(pcbnew.Edge_Cuts)
    edge.SetWidth(mm(0.15))
    board.Add(edge)
    print(f"  板子尺寸: {BOARD_W}x{BOARD_H}mm")


def setup_4layer_stackup(board):
    """设置4层层叠"""
    settings = board.GetDesignSettings()
    settings.SetCopperLayerCount(4)
    board.SetDesignSettings(settings)

    # 启用内层
    enabled = board.GetEnabledLayers()
    enabled.AddLayer(pcbnew.In1_Cu)
    enabled.AddLayer(pcbnew.In2_Cu)
    board.SetEnabledLayers(enabled)

    # 设置层名
    board.SetLayerName(pcbnew.F_Cu, "F.Cu")
    board.SetLayerName(pcbnew.In1_Cu, "GND_Plane")
    board.SetLayerName(pcbnew.In2_Cu, "PWR_3V3")
    board.SetLayerName(pcbnew.B_Cu, "B.Cu")

    print("  4层层叠: F.Cu / GND_Plane / PWR_3V3 / B.Cu")


def setup_design_rules(board):
    """设置设计规则"""
    ds = board.GetDesignSettings()

    ds.m_TrackMinWidth = mm(0.15)        # 最小走线宽度
    ds.m_ViasMinSize = mm(0.5)           # Via外径
    ds.m_MinThroughDrill = mm(0.25)      # Via钻孔
    ds.m_MinClearance = mm(0.15)         # 最小间距
    ds.m_HoleToHoleMin = mm(0.25)        # 孔到孔间距
    ds.m_CopperEdgeClearance = mm(0.3)   # 走线到板边距离

    # 走线宽度类
    ds.m_TrackWidthList.clear()
    ds.m_TrackWidthList.append(mm(0.2))   # 信号线
    ds.m_TrackWidthList.append(mm(0.3))   # 电源线
    ds.m_TrackWidthList.append(mm(0.5))   # 大电流线

    board.SetDesignSettings(ds)
    print("  设计规则已设置")


def place_components(board):
    """放置所有元器件"""
    placed = 0
    missing = []

    for fp in board.GetFootprints():
        ref = fp.GetReference()
        if ref in LAYOUT:
            info = LAYOUT[ref]
            x, y = info['pos']
            rot = info['rot']
            layer = info['layer']

            fp.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
            fp.SetOrientationDegrees(rot)

            if layer == 'B':
                if fp.GetLayer() != pcbnew.B_Cu:
                    fp.Flip(fp.GetPosition(), False)
            else:
                if fp.GetLayer() != pcbnew.F_Cu:
                    fp.Flip(fp.GetPosition(), False)

            placed += 1

    # 检查未在布局中的元件
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        if ref not in LAYOUT:
            missing.append(ref)

    print(f"  已放置 {placed}/{len(LAYOUT)} 个元件")
    if missing:
        print(f"  ⚠ 未定义布局的元件: {missing}")

    return placed


def setup_copper_zones(board):
    """设置GND和3V3铜箔区域"""
    # 先移除旧的zone
    zones_to_remove = []
    for i in range(board.GetAreaCount()):
        zones_to_remove.append(board.GetArea(i))
    for z in zones_to_remove:
        board.Remove(z)

    # 查找GND和3V3网络
    netinfo = board.GetNetInfo()
    gnd_net = None
    pwr_net = None

    for net in netinfo.NetsByName():
        name = net
        if name == 'GND':
            gnd_net = netinfo.GetNetItem(name)
        elif name == '3V3':
            pwr_net = netinfo.GetNetItem(name)

    if not gnd_net:
        print("  ⚠ 未找到GND网络")
        return
    if not pwr_net:
        print("  ⚠ 未找到3V3网络")

    margin = 0.5  # 铜箔离板边距离
    x1, y1 = BOARD_L + margin, BOARD_T + margin
    x2, y2 = BOARD_L + BOARD_W - margin, BOARD_T + BOARD_H - margin

    def make_zone(net, layer, name):
        zone = pcbnew.ZONE(board)
        zone.SetNet(net)
        zone.SetLayer(layer)
        zone.SetZoneName(name)

        # 创建多边形轮廓
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

    # In1.Cu = GND完整平面
    make_zone(gnd_net, pcbnew.In1_Cu, "GND_Plane")
    print("  GND平面已创建 (In1.Cu)")

    # In2.Cu = 3V3电源平面
    if pwr_net:
        make_zone(pwr_net, pcbnew.In2_Cu, "3V3_Plane")
        print("  3V3平面已创建 (In2.Cu)")

    # F.Cu GND填充 (元件面)
    make_zone(gnd_net, pcbnew.F_Cu, "GND_F")
    print("  F.Cu GND填充已创建")

    # B.Cu GND填充 (背面)
    make_zone(gnd_net, pcbnew.B_Cu, "GND_B")
    print("  B.Cu GND填充已创建")


def add_stitching_vias(board):
    """添加GND缝合Via"""
    netinfo = board.GetNetInfo()
    gnd_net = None
    for net in netinfo.NetsByName():
        if net == 'GND':
            gnd_net = netinfo.GetNetItem(net)
            break

    if not gnd_net:
        return

    count = 0
    spacing = 8  # 每8mm一个via

    # 沿板边添加
    for x in range(int(BOARD_L + 3), int(BOARD_L + BOARD_W - 2), spacing):
        for y in [BOARD_T + 3, BOARD_T + BOARD_H - 3]:
            via = pcbnew.PCB_VIA(board)
            via.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
            via.SetViaType(pcbnew.VIATYPE_THROUGH)
            via.SetWidth(mm(0.5))
            via.SetDrill(mm(0.25))
            via.SetNet(gnd_net)
            board.Add(via)
            count += 1

    for y in range(int(BOARD_T + 3), int(BOARD_T + BOARD_H - 2), spacing):
        for x in [BOARD_L + 3, BOARD_L + BOARD_W - 3]:
            via = pcbnew.PCB_VIA(board)
            via.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
            via.SetViaType(pcbnew.VIATYPE_THROUGH)
            via.SetWidth(mm(0.5))
            via.SetDrill(mm(0.25))
            via.SetNet(gnd_net)
            board.Add(via)
            count += 1

    print(f"  添加 {count} 个GND缝合Via")


def add_power_vias(board):
    """为电源焊盘添加Via连接到内层平面"""
    netinfo = board.GetNetInfo()

    gnd_net = None
    pwr_net = None
    for net in netinfo.NetsByName():
        if net == 'GND':
            gnd_net = netinfo.GetNetItem(net)
        elif net == '3V3':
            pwr_net = netinfo.GetNetItem(net)

    if not gnd_net or not pwr_net:
        return

    count = 0
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            net = pad.GetNet()
            if not net:
                continue

            net_name = net.GetNetname()
            pos = pad.GetPosition()

            if net_name == 'GND':
                # 为GND焊盘添加via到In1.Cu
                via = pcbnew.PCB_VIA(board)
                via.SetPosition(pos)
                via.SetViaType(pcbnew.VIATYPE_THROUGH)
                via.SetWidth(mm(0.5))
                via.SetDrill(mm(0.25))
                via.SetNet(gnd_net)
                board.Add(via)
                count += 1

            elif net_name == '3V3':
                # 为3V3焊盘添加via到In2.Cu
                via = pcbnew.PCB_VIA(board)
                via.SetPosition(pos)
                via.SetViaType(pcbnew.VIATYPE_THROUGH)
                via.SetWidth(mm(0.5))
                via.SetDrill(mm(0.25))
                via.SetNet(pwr_net)
                board.Add(via)
                count += 1

    print(f"  添加 {count} 个电源连接Via")


def export_dsn(board):
    """导出DSN文件供Freerouter使用"""
    try:
        pcbnew.ExportSpecctraDSN(board, DSN_FILE)
        print(f"  DSN已导出: {DSN_FILE}")
        return True
    except Exception as e:
        print(f"  ⚠ DSN导出失败: {e}")
        # 尝试使用文件路径导出
        try:
            board.Save(PCB_FILE)
            print(f"  PCB已保存, 请在KiCad中手动导出DSN")
            return False
        except:
            return False


def import_ses(board):
    """导入Freerouter布线结果"""
    if not os.path.exists(SES_FILE):
        print(f"  ⚠ SES文件不存在: {SES_FILE}")
        return False

    try:
        pcbnew.ImportSpecctraSES(board, SES_FILE)
        print(f"  SES已导入: {SES_FILE}")
        return True
    except Exception as e:
        print(f"  ⚠ SES导入失败: {e}")
        return False


def basic_routing(board):
    """基础Python布线 - 只处理简单的短距离连接"""
    netinfo = board.GetNetInfo()
    routed = 0
    failed = 0

    # 收集所有焊盘信息
    pad_data = {}  # net_name -> [(x, y, layer, ref, pin), ...]
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        for pad in fp.Pads():
            net = pad.GetNet()
            if not net:
                continue
            net_name = net.GetNetname()
            if net_name in ('GND', '3V3', '5V', '5V_PROT', 'VBAT', 'VBAT_SW'):
                continue  # 电源网络由铜箔平面处理

            pos = pad.GetPosition()
            x, y = to_mm(pos.x), to_mm(pos.y)
            layer = pad.GetLayer()

            if net_name not in pad_data:
                pad_data[net_name] = []
            pad_data[net_name].append((x, y, layer, ref, pad.GetName()))

    # 对每个信号网络, 尝试简单的直线/L型布线
    for net_name, pads in pad_data.items():
        if len(pads) < 2:
            continue

        net_item = netinfo.GetNetItem(net_name)
        if not net_item:
            continue

        # 简单的两点连接
        for i in range(len(pads) - 1):
            x1, y1, l1, ref1, pin1 = pads[i]
            x2, y2, l2, ref2, pin2 = pads[i + 1]

            dist = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

            # 只处理短距离(< 20mm)且同层的简单连接
            if dist < 20 and l1 == l2:
                try:
                    # L型布线
                    track1 = pcbnew.PCB_TRACK(board)
                    track1.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1)))
                    track1.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y1)))
                    track1.SetWidth(mm(0.2))
                    track1.SetLayer(pcbnew.F_Cu)
                    track1.SetNet(net_item)
                    board.Add(track1)

                    track2 = pcbnew.PCB_TRACK(board)
                    track2.SetStart(pcbnew.VECTOR2I(mm(x2), mm(y1)))
                    track2.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y2)))
                    track2.SetWidth(mm(0.2))
                    track2.SetLayer(pcbnew.F_Cu)
                    track2.SetNet(net_item)
                    board.Add(track2)

                    routed += 1
                except Exception as e:
                    failed += 1

    print(f"  基础布线: {routed} 成功, {failed} 失败")
    print(f"  ℹ 剩余复杂布线将由Freerouter完成")


def step_layout():
    """步骤1: 布局+导出DSN"""
    print("=" * 60)
    print("CyberWand 4层PCB v3.0 - 布局阶段")
    print("=" * 60)

    # 加载或创建PCB
    if os.path.exists(PCB_FILE):
        print(f"\n加载现有PCB: {PCB_FILE}")
        board = pcbnew.LoadBoard(PCB_FILE)
    else:
        print(f"\n创建新PCB: {PCB_FILE}")
        board = pcbnew.BOARD()

    # 1. 设置板子外框
    print("\n[1/8] 设置板子外框...")
    # 清除旧外框
    shapes = [s for s in board.GetDrawings() if s.GetLayer() == pcbnew.Edge_Cuts]
    for s in shapes:
        board.Remove(s)
    setup_board_outline(board)

    # 2. 设置4层
    print("\n[2/8] 设置4层层叠...")
    setup_4layer_stackup(board)

    # 3. 设置设计规则
    print("\n[3/8] 设置设计规则...")
    setup_design_rules(board)

    # 4. 放置元器件
    print("\n[4/8] 放置元器件...")
    placed = place_components(board)
    if placed == 0:
        print("  ⚠ 没有元件被放置! 请先导入网表。")
        print(f"    1. 在KiCad中打开PCB")
        print(f"    2. 文件 → 导入 → 网表")
        print(f"    3. 选择: {NETLIST_FILE}")
        print(f"    4. 导入后重新运行本脚本")

    # 5. 清除旧走线
    print("\n[5/8] 清除旧走线...")
    tracks = list(board.GetTracks())
    removed = 0
    for t in tracks:
        board.Remove(t)
        removed += 1
    print(f"  移除 {removed} 条旧走线")

    # 6. 设置铜箔区域
    print("\n[6/8] 设置铜箔区域...")
    setup_copper_zones(board)

    # 7. 添加电源Via
    print("\n[7/8] 添加电源Via...")
    add_power_vias(board)
    add_stitching_vias(board)

    # 8. 保存并导出DSN
    print("\n[8/8] 保存PCB并导出DSN...")
    board.Save(PCB_FILE)
    print(f"  PCB已保存: {PCB_FILE}")

    export_dsn(board)

    print("\n" + "=" * 60)
    print("布局完成! 下一步:")
    print(f"  1. 使用Freerouter打开DSN文件进行自动布线:")
    print(f"     freerouter -de {DSN_FILE} -do {SES_FILE}")
    print(f"  2. 布线完成后运行:")
    print(f"     python pcb_4layer_v3.py --step import")
    print("=" * 60)


def step_import():
    """步骤2: 导入Freerouter布线结果"""
    print("=" * 60)
    print("CyberWand 4层PCB v3.0 - 导入Freerouter结果")
    print("=" * 60)

    board = pcbnew.LoadBoard(PCB_FILE)

    if import_ses(board):
        # 填充铜箔
        filler = pcbnew.ZONE_FILLER(board)
        zones = board.Zones()
        filler.Fill(zones)
        print("  铜箔已填充")

        board.Save(PCB_FILE)
        print(f"  PCB已保存: {PCB_FILE}")
        print("\n下一步: 运行DRC检查")
        print(f"  python pcb_4layer_v3.py --step drc")
    else:
        print("\n导入失败, 请检查SES文件是否存在")


def step_drc():
    """步骤3: 运行DRC"""
    print("=" * 60)
    print("CyberWand 4层PCB v3.0 - DRC检查")
    print("=" * 60)

    # 使用KiCad CLI运行DRC
    kicad_cli = r'D:\kicad\bin\kicad-cli.exe'
    if not os.path.exists(kicad_cli):
        print(f"  ⚠ KiCad CLI 未找到: {kicad_cli}")
        return

    os.makedirs(os.path.dirname(DRC_FILE), exist_ok=True)

    import subprocess
    cmd = [
        kicad_cli, 'pcb', 'drc',
        '--output', DRC_FILE,
        '--format', 'json',
        '--severity-all',
        PCB_FILE
    ]

    print(f"  运行: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
    print(f"  返回码: {result.returncode}")
    if result.stdout:
        print(f"  输出: {result.stdout[:500]}")
    if result.stderr:
        print(f"  错误: {result.stderr[:500]}")

    # 分析DRC结果
    if os.path.exists(DRC_FILE):
        import json
        with open(DRC_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)

        violations = data.get('violations', [])
        unresolved = data.get('unresolved', [])

        # 分类统计
        from collections import defaultdict
        counts = defaultdict(int)
        for v in violations:
            counts[v.get('type', 'unknown')] += 1

        print(f"\n  DRC结果:")
        print(f"  {'类型':<30} {'数量':>6}")
        print(f"  {'-'*36}")
        for vtype, cnt in sorted(counts.items(), key=lambda x: -x[1]):
            print(f"  {vtype:<30} {cnt:>6}")
        print(f"  {'-'*36}")
        print(f"  {'总违规':<30} {len(violations):>6}")
        print(f"  {'未解决':<30} {len(unresolved):>6}")


def main():
    parser = argparse.ArgumentParser(description='CyberWand 4层PCB v3.0')
    parser.add_argument('--step', choices=['layout', 'import', 'drc', 'all'],
                       default='layout', help='执行步骤')
    args = parser.parse_args()

    if args.step == 'layout' or args.step == 'all':
        step_layout()

    if args.step == 'import' or args.step == 'all':
        step_import()

    if args.step == 'drc' or args.step == 'all':
        step_drc()


if __name__ == '__main__':
    main()
