"""
CyberWand PCB 布局+布线+DRC 自动迭代器
=======================================
1. 扩大板子 → 重新摆放元件(间距充足)
2. 清除旧走线 → 重新智能布线
3. 铜箔填充 → 保存
4. 运行DRC → 分析错误
5. 根据错误自动调整 → 重复

板子尺寸: 80 x 150 mm (扩大以容纳所有元件)
"""

import pcbnew
import math
import sys
import os
import json
import subprocess
from collections import defaultdict

def mm(v): return int(v * 1000000)
def to_mm(v): return v / 1000000

# =============================================
# 第一部分：新布局设计
# =============================================
# 设计原则：
# 1. ESP32-S3居中，其他元件围绕
# 2. 功能分区：电源区、传感器区、显示区、音频区、IO区
# 3. 元件最小间距 5mm
# 4. 电源走线短粗

# 板框参数
BOARD_LEFT = 90.0
BOARD_TOP = 25.0
BOARD_W = 90.0
BOARD_H = 165.0
BOARD_RIGHT = BOARD_LEFT + BOARD_W
BOARD_BOTTOM = BOARD_TOP + BOARD_H

# 元件布局 (中心坐标, 旋转角度)
# 按功能分区设计
LAYOUT = {
    # ===== 中心区: ESP32主控 =====
    'U1':  (135.0, 105.0, 0),    # ESP32-S3 (48x43mm) 居中偏上

    # ===== 顶部: 显示屏 + LED =====
    'LCD1': (135.0,  48.0, 90),  # LCD连接器
    'C5':   (155.0,  48.0, 0),   # LCD退耦
    'C6':   (159.0,  48.0, 0),   # LCD退耦
    'D1':   (108.0,  38.0, 0),   # WS2812B LED1
    'D2':   (120.0,  38.0, 0),   # WS2812B LED2
    'D3':   (165.0,  38.0, 0),   # WS2812B LED3
    'C12':  (114.0,  38.0, 0),   # LED退耦

    # ===== 左侧: 按键 (间距15mm) =====
    'SW3':  (97.0, 82.0, 0),     # KEY_PLAY
    'SW2':  (97.0, 100.0, 0),    # KEY_SELECT
    'SW1':  (97.0, 118.0, 0),    # KEY_MODE
    'R6':   (97.0, 90.0, 0),     # KEY_PLAY上拉
    'R5':   (97.0, 108.0, 0),    # KEY_SELECT上拉
    'R4':   (97.0, 126.0, 0),    # KEY_MODE上拉

    # ===== 左上: MPU6050 (远离ESP32) =====
    'U2':   (100.0, 58.0, 0),    # MPU-6050
    'C4':   (110.0, 58.0, 0),    # MPU退耦
    'R2':   (110.0, 53.0, 0),    # I2C SDA上拉
    'R3':   (110.0, 63.0, 0),    # I2C SCL上拉

    # ===== 左下: 麦克风 =====
    'MIC1': (97.0, 142.0, 0),    # INMP441

    # ===== 右侧: DFPlayer + SD卡 (更多空间) =====
    'U3':   (168.0, 80.0, 0),    # DFPlayer Mini
    'J1':   (168.0, 112.0, 90),  # MicroSD卡座
    'C10':  (168.0, 65.0, 0),    # DFPlayer退耦
    'C11':  (172.0, 65.0, 0),    # DFPlayer退耦

    # ===== 底部: 电源区 (更宽松) =====
    'U4':   (115.0, 162.0, 0),   # TP4056
    'U5':   (150.0, 162.0, 0),   # ME6211A33 LDO
    'J2':   (135.0, 180.0, 90),  # USB-C
    'C9':   (125.0, 177.0, 0),   # USB退耦
    'R7':   (125.0, 172.0, 0),   # USB CC1
    'R8':   (128.0, 172.0, 0),   # USB CC2
    'R9':   (108.0, 162.0, 0),   # TP4056 PROG
    'C7':   (150.0, 155.0, 0),   # LDO输出
    'C8':   (154.0, 155.0, 0),   # LDO退耦

    # 充电指示LED (远离电源IC)
    'D4':   (108.0, 155.0, 0),   # Red
    'D5':   (108.0, 158.0, 0),   # Green
    'R10':  (104.0, 155.0, 0),   # LED R
    'R11':  (104.0, 158.0, 0),   # LED R
    'R12':  (115.0, 168.0, 0),   # TP4056 CE

    'R1':   (125.0, 82.0, 0),    # ESP32附近

    # 主控退耦电容 (间距3mm)
    'C1':   (118.0, 78.0, 0),
    'C2':   (122.0, 78.0, 0),
    'C3':   (126.0, 78.0, 0),

    # ===== 背面: 电池+喇叭 =====
    'BT1':  (135.0, 145.0, 180),
    'LS1':  (135.0, 60.0, 180),

    # ===== 安装孔 (板框内缩5mm) =====
    'H1':   (95.0, 30.0, 0),
    'H2':   (175.0, 30.0, 0),
    'H3':   (95.0, 185.0, 0),
    'H4':   (175.0, 185.0, 0),
}


def apply_layout(board):
    """应用新布局"""
    print("\n[布局] 应用新元件位置...")
    FCU = board.GetLayerID('F.Cu')
    BCU = board.GetLayerID('B.Cu')
    
    fps = board.GetFootprints()
    placed = 0
    
    for i in range(len(fps)):
        fp = fps[i]
        ref = fp.GetReference()
        
        if ref in LAYOUT:
            x, y, rot = LAYOUT[ref]
            fp.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
            fp.SetOrientationDegrees(rot)
            
            # BT1和LS1在背面
            if ref in ['BT1', 'LS1']:
                if fp.GetLayer() != BCU:
                    fp.Flip(fp.GetPosition(), False)
            
            placed += 1
    
    print(f"  放置了 {placed} 个元件")
    return placed


def update_board_outline(board):
    """更新板框"""
    print("\n[板框] 更新板框...")
    edge_layer = board.GetLayerID('Edge.Cuts')
    
    # 删除旧板框
    drawings_to_remove = []
    for d in board.GetDrawings():
        if d.GetLayer() == edge_layer:
            drawings_to_remove.append(d)
    for d in drawings_to_remove:
        board.Remove(d)
    
    # 新板框 (圆角矩形用4条线段)
    corners = [
        (BOARD_LEFT, BOARD_TOP),
        (BOARD_RIGHT, BOARD_TOP),
        (BOARD_RIGHT, BOARD_BOTTOM),
        (BOARD_LEFT, BOARD_BOTTOM)
    ]
    
    for i in range(4):
        x1, y1 = corners[i]
        x2, y2 = corners[(i+1) % 4]
        
        line = pcbnew.PCB_SHAPE(board)
        line.SetShape(pcbnew.SHAPE_T_SEGMENT)
        line.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1)))
        line.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y2)))
        line.SetLayer(edge_layer)
        line.SetWidth(mm(0.1))
        board.Add(line)
    
    print(f"  板框: {BOARD_W}x{BOARD_H}mm")


def update_zones(board):
    """更新铜箔区域"""
    print("\n[铜箔] 更新GND铜箔...")
    
    # 删除旧铜箔
    zones_to_remove = list(board.Zones())
    for z in zones_to_remove:
        board.Remove(z)
    
    gnd = board.FindNet("GND")
    if not gnd:
        print("  [!] 未找到GND网络")
        return
    
    FCU = board.GetLayerID('F.Cu')
    BCU = board.GetLayerID('B.Cu')
    
    margin = 1.0  # 铜箔内缩1mm
    
    for layer in [FCU, BCU]:
        zone = pcbnew.ZONE(board)
        zone.SetNet(gnd)
        zone.SetLayer(layer)
        zone.SetIsRuleArea(False)
        zone.SetDoNotAllowTracks(False)
        zone.SetDoNotAllowVias(False)
        zone.SetDoNotAllowPads(False)
        zone.SetDoNotAllowCopperPour(False)
        zone.SetDoNotAllowFootprints(False)
        
        # 铜箔覆盖整个板子(内缩margin)
        outline = zone.Outline()
        outline.NewOutline()
        outline.Append(mm(BOARD_LEFT + margin), mm(BOARD_TOP + margin))
        outline.Append(mm(BOARD_RIGHT - margin), mm(BOARD_TOP + margin))
        outline.Append(mm(BOARD_RIGHT - margin), mm(BOARD_BOTTOM - margin))
        outline.Append(mm(BOARD_LEFT + margin), mm(BOARD_BOTTOM - margin))
        
        zone.SetMinThickness(mm(0.2))
        zone.SetThermalReliefGap(mm(0.3))
        zone.SetThermalReliefSpokeWidth(mm(0.4))
        
        board.Add(zone)
    
    print("  已创建顶层和底层GND铜箔")


# =============================================
# 第二部分：布线
# =============================================
# 全局走线记录（避免交叉）
placed_segments = {'F.Cu':[], 'B.Cu':[]}

def segments_cross(ax1,ay1,ax2,ay2, bx1,by1,bx2,by2):
    """检测两线段是否交叉"""
    def ccw(px,py,qx,qy,rx,ry):
        return (rx-px)*(qy-py) - (qx-px)*(ry-py)
    d1=ccw(ax1,ay1,ax2,ay2,bx1,by1)
    d2=ccw(ax1,ay1,ax2,ay2,bx2,by2)
    d3=ccw(bx1,by1,bx2,by2,ax1,ay1)
    d4=ccw(bx1,by1,bx2,by2,ax2,ay2)
    if((d1>0 and d2<0)or(d1<0 and d2>0))and((d3>0 and d4<0)or(d3<0 and d4>0)): return True
    return False

def check_crossing(x1,y1,x2,y2,layer_name):
    """检查新线段是否与已有线段交叉"""
    for sx1,sy1,sx2,sy2 in placed_segments.get(layer_name,[]):
        if segments_cross(x1,y1,x2,y2,sx1,sy1,sx2,sy2): return True
    return False

def record_segment(x1,y1,x2,y2,layer_name):
    placed_segments.setdefault(layer_name,[]).append((x1,y1,x2,y2))


def route_all(board):
    """布线所有网络"""
    global placed_segments
    placed_segments = {'F.Cu':[], 'B.Cu':[]}
    
    print("\n[布线] 开始...")
    FCU = board.GetLayerID('F.Cu')
    BCU = board.GetLayerID('B.Cu')
    
    # 收集焊盘
    net_pads = defaultdict(list)
    all_pads = []
    fps = board.GetFootprints()
    
    for i in range(len(fps)):
        fp = fps[i]
        ref = fp.GetReference()
        pads = fp.Pads()
        for j in range(len(pads)):
            pad = pads[j]
            net = pad.GetNetname()
            pos = pad.GetPosition()
            on_f = pad.IsOnLayer(FCU)
            on_b = pad.IsOnLayer(BCU)
            is_th = on_f and on_b
            p = {'ref':ref, 'x':pos.x, 'y':pos.y,
                 'on_f':on_f, 'on_b':on_b, 'is_th':is_th, 'net':net or ''}
            all_pads.append(p)
            if net:
                net_pads[net].append(p)
    
    signal_nets = {k:v for k,v in net_pads.items() if len(v)>=2 and k!='GND'}
    
    # 清除旧走线
    tracks = list(board.GetTracks())
    for t in tracks:
        board.Remove(t)
    print(f"  清除 {len(tracks)} 旧走线")
    
    # 排序优先级
    def prio(n):
        nl = n.lower()
        if n in ['3V3','VCC_3V3','BAT','5V']: return 1
        if 'usb' in nl: return 2
        if any(x in nl for x in ['sck','clk','mosi','miso','spi','cs']): return 3
        if any(x in nl for x in ['i2c','sda','scl','i2s']): return 4
        return 5
    
    def wid(n):
        return 0.5 if n in ['3V3','VCC_3V3','BAT','5V'] else 0.25
    
    sorted_nets = sorted(signal_nets.items(), key=lambda x: prio(x[0]))
    routed = 0
    
    for net_name, pads in sorted_nets:
        net_obj = board.FindNet(net_name)
        if not net_obj: continue
        w = mm(wid(net_name))
        
        # MST连接
        connected = [pads[0]]
        remaining = list(pads[1:])
        
        while remaining:
            best_d = float('inf')
            best_c = best_r = None
            for cp in connected:
                for rp in remaining:
                    d = abs(cp['x']-rp['x'])+abs(cp['y']-rp['y'])
                    if d < best_d:
                        best_d = d; best_c = cp; best_r = rp
            if not best_c: break
            
            route_pair(board, all_pads, best_c, best_r, net_name, net_obj, w, FCU, BCU)
            connected.append(best_r)
            remaining.remove(best_r)
        
        routed += 1
    
    print(f"  布线 {routed}/{len(sorted_nets)} 网络")
    return routed


def route_pair(board, all_pads, p1, p2, net_name, net_obj, width, FCU, BCU):
    """连接两个焊盘 (带交叉检测)"""
    sx, sy = p1['x'], p1['y']
    ex, ey = p2['x'], p2['y']
    dist = math.sqrt((ex-sx)**2 + (ey-sy)**2)
    
    p1f = p1['on_f'] or p1['is_th']
    p2f = p2['on_f'] or p2['is_th']
    p1b = p1['on_b'] or p1['is_th']
    p2b = p2['on_b'] or p2['is_th']
    
    safe_pad = mm(0.8)
    
    # 近距离 <10mm → 尝试直连(选择安全层)
    if dist < mm(10):
        # F.Cu直连
        if p1f and p2f:
            if not path_hits_pad(sx,sy,ex,ey,net_name,all_pads,safe_pad) and \
               not check_crossing(sx,sy,ex,ey,'F.Cu'):
                add_trk(board, sx, sy, ex, ey, width, FCU, net_obj)
                return
        # B.Cu直连
        if p1b and p2b:
            if not path_hits_pad(sx,sy,ex,ey,net_name,all_pads,safe_pad) and \
               not check_crossing(sx,sy,ex,ey,'B.Cu'):
                add_trk(board, sx, sy, ex, ey, width, BCU, net_obj)
                return
    
    # 两端通孔 → 优先B.Cu(不占用F.Cu空间)
    if p1['is_th'] and p2['is_th']:
        # 先尝试B.Cu直连
        if dist < mm(15) and not check_crossing(sx,sy,ex,ey,'B.Cu'):
            add_trk(board, sx, sy, ex, ey, width, BCU, net_obj)
            return
        # L型B.Cu
        route_bcu_smart(board, sx, sy, ex, ey, width, BCU, net_obj)
        return
    
    # 两端F.Cu SMD → via桥接(via离焊盘远一些)
    if p1f and p2f:
        dx = ex - sx; dy = ey - sy
        d = max(math.sqrt(dx*dx+dy*dy), 1)
        ux, uy = dx/d, dy/d
        off = min(mm(4.0), int(d * 0.25))
        
        v1x = int(sx + ux*off); v1y = int(sy + uy*off)
        v2x = int(ex - ux*off); v2y = int(ey - uy*off)
        v1x, v1y = safe_via(v1x, v1y, net_name, all_pads)
        v2x, v2y = safe_via(v2x, v2y, net_name, all_pads)
        
        add_trk(board, sx, sy, v1x, v1y, width, FCU, net_obj)
        add_via(board, v1x, v1y, net_obj, FCU, BCU)
        route_bcu_smart(board, v1x, v1y, v2x, v2y, width, BCU, net_obj)
        add_via(board, v2x, v2y, net_obj, FCU, BCU)
        add_trk(board, v2x, v2y, ex, ey, width, FCU, net_obj)
        return
    
    # 不同层 → 单via
    if p1f and not p2f:
        vx, vy = safe_via((sx+ex)//2, (sy+ey)//2, net_name, all_pads)
        add_trk(board, sx, sy, vx, vy, width, FCU, net_obj)
        add_via(board, vx, vy, net_obj, FCU, BCU)
        add_trk(board, vx, vy, ex, ey, width, BCU, net_obj)
        return
    if not p1f and p2f:
        vx, vy = safe_via((sx+ex)//2, (sy+ey)//2, net_name, all_pads)
        add_trk(board, sx, sy, vx, vy, width, BCU, net_obj)
        add_via(board, vx, vy, net_obj, FCU, BCU)
        add_trk(board, vx, vy, ex, ey, width, FCU, net_obj)
        return
    
    # 默认B.Cu
    route_bcu_smart(board, sx, sy, ex, ey, width, BCU, net_obj)


def route_bcu_smart(board, x1, y1, x2, y2, width, BCU, net):
    """B.Cu智能走线: 选择不交叉的路径"""
    dist = math.sqrt((x2-x1)**2 + (y2-y1)**2)
    
    # 短距离直连
    if dist < mm(10):
        if not check_crossing(x1,y1,x2,y2,'B.Cu'):
            add_trk(board, x1, y1, x2, y2, width, BCU, net)
            return
    
    # L型方案1：先水平后垂直
    cross1 = check_crossing(x1,y1,x2,y1,'B.Cu') or check_crossing(x2,y1,x2,y2,'B.Cu')
    # L型方案2：先垂直后水平
    cross2 = check_crossing(x1,y1,x1,y2,'B.Cu') or check_crossing(x1,y2,x2,y2,'B.Cu')
    
    if not cross1:
        add_trk(board, x1, y1, x2, y1, width, BCU, net)
        add_trk(board, x2, y1, x2, y2, width, BCU, net)
    elif not cross2:
        add_trk(board, x1, y1, x1, y2, width, BCU, net)
        add_trk(board, x1, y2, x2, y2, width, BCU, net)
    else:
        # 都交叉 → Z型(中间偏移)
        mx = (x1+x2)//2 + mm(2)
        add_trk(board, x1, y1, mx, y1, width, BCU, net)
        add_trk(board, mx, y1, mx, y2, width, BCU, net)
        add_trk(board, mx, y2, x2, y2, width, BCU, net)


def safe_via(x, y, net_name, all_pads):
    """安全过孔位置 - 3mm安全距离"""
    safe_dist = mm(3)
    # 确保在板框内
    brd_margin = mm(3)
    min_x = mm(BOARD_LEFT) + brd_margin
    max_x = mm(BOARD_RIGHT) - brd_margin
    min_y = mm(BOARD_TOP) + brd_margin
    max_y = mm(BOARD_BOTTOM) - brd_margin
    x = max(min_x, min(max_x, x))
    y = max(min_y, min(max_y, y))
    
    if is_safe(x, y, net_name, all_pads, safe_dist):
        return (x, y)
    # 尝试更多偏移方向
    for r in [mm(3), mm(4), mm(5)]:
        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            nx = int(x + r * math.cos(rad))
            ny = int(y + r * math.sin(rad))
            nx = max(min_x, min(max_x, nx))
            ny = max(min_y, min(max_y, ny))
            if is_safe(nx, ny, net_name, all_pads, safe_dist):
                return (nx, ny)
    return (x, y)


def is_safe(x, y, net_name, all_pads, min_dist):
    for p in all_pads:
        pnet = p['net']
        if pnet == net_name or pnet == '': continue
        if abs(x-p['x'])+abs(y-p['y']) < min_dist: return False
    return True


def path_hits_pad(x1, y1, x2, y2, net_name, all_pads, clearance):
    dx = x2-x1; dy = y2-y1
    dist = math.sqrt(dx*dx+dy*dy)
    if dist < 1: return False
    steps = max(int(dist / mm(0.5)), 3)
    for i in range(1, steps):
        t = i / steps
        px = int(x1 + dx*t); py = int(y1 + dy*t)
        for p in all_pads:
            if p['net'] == net_name or p['net'] == '': continue
            if abs(px-p['x'])+abs(py-p['y']) < clearance: return True
    return False


def add_trk(board, x1, y1, x2, y2, width, layer, net):
    if x1==x2 and y1==y2: return
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(int(x1),int(y1)))
    t.SetEnd(pcbnew.VECTOR2I(int(x2),int(y2)))
    t.SetWidth(width); t.SetLayer(layer); t.SetNet(net)
    board.Add(t)
    ln = 'F.Cu' if layer == board.GetLayerID('F.Cu') else 'B.Cu'
    record_segment(int(x1),int(y1),int(x2),int(y2),ln)


def add_via(board, x, y, net, fcu, bcu):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(int(x),int(y)))
    v.SetWidth(mm(0.8)); v.SetDrill(mm(0.4))
    v.SetNet(net); v.SetLayerPair(fcu, bcu)
    board.Add(v)


# =============================================
# 第三部分：DRC检查和分析
# =============================================
def run_drc(pcb_file, drc_output):
    """运行KiCad DRC"""
    cmd = [
        r'D:\kicad\bin\kicad-cli.exe', 'pcb', 'drc',
        '--severity-all', '--format', 'json',
        '-o', drc_output, pcb_file
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    return result.returncode == 0


def analyze_drc(drc_file):
    """分析DRC结果"""
    with open(drc_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    unconnected = data.get('unconnected_items', [])
    violations = data.get('violations', [])
    
    vtypes = defaultdict(int)
    for v in violations:
        vtypes[v.get('type','')] += 1
    
    # 分类
    fixed_types = ['courtyards_overlap','silk_over_copper','silk_overlap',
                   'silk_edge_clearance','drill_out_of_range','solder_mask_bridge']
    fixed = sum(vtypes.get(t,0) for t in fixed_types)
    routing = len(violations) - fixed
    
    return {
        'unconnected': len(unconnected),
        'total_violations': len(violations),
        'fixed_violations': fixed,
        'routing_violations': routing,
        'types': dict(vtypes),
        'shorting': vtypes.get('shorting_items', 0),
        'crossing': vtypes.get('tracks_crossing', 0),
        'clearance': vtypes.get('clearance', 0),
        'hole_clearance': vtypes.get('hole_clearance', 0),
    }


# =============================================
# 主流程
# =============================================
def main():
    sys.stdout.reconfigure(encoding='utf-8')
    
    pcb_file = r'D:\thinkpad\Documents\cybewand_insta360\cybewand_insta360.kicad_pcb'
    drc_file = r'd:\win_workspace\CyberWand_Insta360\schematic\skidl\docs\DRC_iter.json'
    
    if not os.path.exists(pcb_file):
        print(f"文件不存在: {pcb_file}")
        sys.exit(1)
    
    print("=" * 70)
    print("CyberWand PCB 布局+布线+DRC 自动迭代器")
    print("=" * 70)
    
    # 加载
    board = pcbnew.LoadBoard(pcb_file)
    print(f"[OK] 加载: {pcb_file}")
    
    # 第1步：新布局
    print("\n" + "="*50)
    print("第1步：应用新布局")
    print("="*50)
    
    update_board_outline(board)
    apply_layout(board)
    update_zones(board)
    
    # 第2步：布线
    print("\n" + "="*50)
    print("第2步：智能布线")
    print("="*50)
    route_all(board)
    
    # 填充铜箔
    print("\n[铜箔] 填充...")
    zones = board.Zones()
    if len(zones) > 0:
        filler = pcbnew.ZONE_FILLER(board)
        filler.Fill(zones)
        print(f"  填充 {len(zones)} 个区域")
    
    # 保存
    print("\n[保存]...")
    pcbnew.SaveBoard(pcb_file, board)
    print(f"  [OK]")
    
    # 第3步：DRC
    print("\n" + "="*50)
    print("第3步：DRC检查")
    print("="*50)
    
    if run_drc(pcb_file, drc_file):
        result = analyze_drc(drc_file)
        print(f"\n  未连接: {result['unconnected']}")
        print(f"  总违规: {result['total_violations']}")
        print(f"    非布线(固定): {result['fixed_violations']}")
        print(f"    布线相关: {result['routing_violations']}")
        print(f"      短路: {result['shorting']}")
        print(f"      交叉: {result['crossing']}")
        print(f"      间距: {result['clearance']}")
        print(f"      孔距: {result['hole_clearance']}")
        
        print(f"\n  详细:")
        for t, c in sorted(result['types'].items(), key=lambda x: x[1], reverse=True):
            print(f"    {t:40s}: {c}")
    else:
        print("  [!] DRC运行失败")
    
    print("\n" + "=" * 70)
    print("迭代完成！")
    print("=" * 70)


if __name__ == '__main__':
    main()
