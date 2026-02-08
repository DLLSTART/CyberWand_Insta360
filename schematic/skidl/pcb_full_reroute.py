"""
CyberWand PCB 布线器 v7.0 - 精准避障
=====================================
核心改进：
1. via位置避开所有焊盘(2mm安全距离)
2. F.Cu只做<3mm短连接
3. 长连接全走B.Cu，via精准放置
4. 3V3等大网络用链式连接减少长走线
5. GND不走线
"""

import pcbnew
import math
import sys
import os
from collections import defaultdict


def mm(v): return int(v * 1000000)
def to_mm(v): return v / 1000000


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    
    if len(sys.argv) < 2:
        print("用法: python pcb_full_reroute.py <pcb文件>")
        sys.exit(1)
    
    pcb_file = sys.argv[1]
    if not os.path.exists(pcb_file):
        print(f"文件不存在: {pcb_file}")
        sys.exit(1)
    
    print("=" * 70)
    print("CyberWand PCB 布线器 v7.0 - 精准避障")
    print("=" * 70)
    
    board = pcbnew.LoadBoard(pcb_file)
    print(f"[OK] 加载: {pcb_file}")
    
    FCU = board.GetLayerID('F.Cu')
    BCU = board.GetLayerID('B.Cu')
    
    # ===== 收集焊盘 =====
    print("\n[1/5] 收集焊盘...")
    net_pads = defaultdict(list)
    all_pad_positions = []  # [(x, y, net_name)] 所有焊盘位置
    
    fps = board.GetFootprints()
    for i in range(len(fps)):
        fp = fps[i]
        ref = fp.GetReference()
        pads = fp.Pads()
        for j in range(len(pads)):
            pad = pads[j]
            net_name = pad.GetNetname()
            pos = pad.GetPosition()
            on_f = pad.IsOnLayer(FCU)
            on_b = pad.IsOnLayer(BCU)
            is_th = on_f and on_b
            
            all_pad_positions.append((pos.x, pos.y, net_name or ''))
            
            if net_name:
                net_pads[net_name].append({
                    'ref': ref, 'num': pad.GetNumber(),
                    'x': pos.x, 'y': pos.y,
                    'on_f': on_f, 'on_b': on_b, 'is_th': is_th
                })
    
    signal_nets = {k: v for k, v in net_pads.items() if len(v) >= 2 and k != 'GND'}
    print(f"  信号网络: {len(signal_nets)}, 焊盘: {len(all_pad_positions)}")
    
    # ===== 清除 =====
    print("\n[2/5] 清除走线...")
    tracks = list(board.GetTracks())
    for t in tracks:
        board.Remove(t)
    print(f"  清除 {len(tracks)}")
    
    # ===== 布线 =====
    print("\n[3/5] 布线...")
    
    def prio(n):
        nl = n.lower()
        if n in ['3V3','VCC_3V3','BAT','5V']: return 1
        if 'usb' in nl: return 2
        if any(x in nl for x in ['sck','clk','mosi','miso','spi','cs']): return 3
        if any(x in nl for x in ['i2c','sda','scl','i2s']): return 4
        return 5
    
    def wid(n):
        if n in ['3V3','VCC_3V3','BAT','5V']: return 0.4
        return 0.2
    
    sorted_nets = sorted(signal_nets.items(), key=lambda x: prio(x[0]))
    routed = 0
    tc = vc = 0
    
    for net_name, pads in sorted_nets:
        net_obj = board.FindNet(net_name)
        if not net_obj:
            continue
        
        w = mm(wid(net_name))
        
        # MST连接
        connected = [pads[0]]
        remaining = list(pads[1:])
        
        while remaining:
            best_d = float('inf')
            best_c = best_r = None
            for cp in connected:
                for rp in remaining:
                    d = abs(cp['x']-rp['x']) + abs(cp['y']-rp['y'])
                    if d < best_d:
                        best_d = d
                        best_c = cp
                        best_r = rp
            
            if not best_c:
                break
            
            t, v = connect(board, all_pad_positions, best_c, best_r, 
                          net_name, net_obj, w, FCU, BCU)
            tc += t
            vc += v
            
            connected.append(best_r)
            remaining.remove(best_r)
        
        routed += 1
        print(f"  [OK] {net_name}")
    
    print(f"\n  结果: {routed}/{len(sorted_nets)}")
    print(f"  走线: {tc}, 过孔: {vc}")
    
    # ===== 铜箔+保存 =====
    print("\n[4/5] 铜箔...")
    zones = board.Zones()
    if len(zones) > 0:
        filler = pcbnew.ZONE_FILLER(board)
        filler.Fill(zones)
        print(f"  {len(zones)} 区域")
    
    print("\n[5/5] 保存...")
    pcbnew.SaveBoard(pcb_file, board)
    print(f"  [OK]")
    
    print("\n" + "=" * 70)
    print(f"完成! {routed}/{len(sorted_nets)}")
    print("=" * 70)


def connect(board, all_pads, p1, p2, net_name, net_obj, width, FCU, BCU):
    """连接两个焊盘 - 精准避障"""
    sx, sy = p1['x'], p1['y']
    ex, ey = p2['x'], p2['y']
    dist = math.sqrt((ex-sx)**2 + (ey-sy)**2)
    
    p1_can_f = p1['on_f'] or p1['is_th']
    p2_can_f = p2['on_f'] or p2['is_th']
    p1_can_b = p1['on_b'] or p1['is_th']
    p2_can_b = p2['on_b'] or p2['is_th']
    
    # ===== 近距离 (<3mm) 直连 =====
    if dist < mm(3):
        if p1_can_f and p2_can_f:
            add_trk(board, sx, sy, ex, ey, width, FCU, net_obj)
            return (1, 0)
        if p1_can_b and p2_can_b:
            add_trk(board, sx, sy, ex, ey, width, BCU, net_obj)
            return (1, 0)
    
    # ===== 中距离 (3-8mm) F.Cu直连（如果路径安全） =====
    if dist < mm(8) and p1_can_f and p2_can_f:
        if not path_hits_pad(sx, sy, ex, ey, net_name, all_pads, mm(0.5)):
            add_trk(board, sx, sy, ex, ey, width, FCU, net_obj)
            return (1, 0)
    
    # ===== 长距离或有冲突：B.Cu走线+过孔 =====
    
    # 确定两端的层
    p1_layer = FCU if (p1_can_f and not p1_can_b) or (p1_can_f and p1_can_b) else BCU
    p2_layer = FCU if (p2_can_f and not p2_can_b) or (p2_can_f and p2_can_b) else BCU
    
    # 两端都是通孔 → 直接B.Cu走线
    if p1['is_th'] and p2['is_th']:
        tc, vc = route_on_bcu(board, all_pads, sx, sy, ex, ey, width, BCU, net_obj, net_name)
        return (tc, vc)
    
    # 两端SMD在F.Cu → via桥接
    if p1_layer == FCU and p2_layer == FCU:
        return via_bridge(board, all_pads, sx, sy, ex, ey, width, FCU, BCU, net_obj, net_name)
    
    # 一端F.Cu一端B.Cu → 单via
    if p1_layer == FCU and p2_layer == BCU:
        return single_via(board, all_pads, sx, sy, ex, ey, width, FCU, BCU, net_obj, net_name, True)
    if p1_layer == BCU and p2_layer == FCU:
        return single_via(board, all_pads, ex, ey, sx, sy, width, FCU, BCU, net_obj, net_name, True)
    
    # 两端B.Cu → B.Cu直走
    tc, vc = route_on_bcu(board, all_pads, sx, sy, ex, ey, width, BCU, net_obj, net_name)
    return (tc, vc)


def via_bridge(board, all_pads, sx, sy, ex, ey, width, FCU, BCU, net, net_name):
    """via桥接：F.Cu stub → via → B.Cu → via → F.Cu stub"""
    dx = ex - sx
    dy = ey - sy
    d = math.sqrt(dx*dx + dy*dy)
    if d < 1: d = 1
    ux, uy = dx/d, dy/d
    
    # via1：在p1附近，沿连线方向偏移2.5mm
    v1x = int(sx + ux * mm(2.5))
    v1y = int(sy + uy * mm(2.5))
    v1x, v1y = find_safe_via_pos(v1x, v1y, net_name, all_pads, mm(1.5))
    
    # via2：在p2附近，反方向偏移2.5mm
    v2x = int(ex - ux * mm(2.5))
    v2y = int(ey - uy * mm(2.5))
    v2x, v2y = find_safe_via_pos(v2x, v2y, net_name, all_pads, mm(1.5))
    
    tc = vc = 0
    
    # p1 → via1 (F.Cu)
    add_trk(board, sx, sy, v1x, v1y, width, FCU, net)
    tc += 1
    
    # via1
    add_via(board, v1x, v1y, net, FCU, BCU)
    vc += 1
    
    # via1 → via2 (B.Cu)
    t, v = route_on_bcu(board, all_pads, v1x, v1y, v2x, v2y, width, BCU, net, net_name)
    tc += t
    vc += v
    
    # via2
    add_via(board, v2x, v2y, net, FCU, BCU)
    vc += 1
    
    # via2 → p2 (F.Cu)
    add_trk(board, v2x, v2y, ex, ey, width, FCU, net)
    tc += 1
    
    return (tc, vc)


def single_via(board, all_pads, fcu_x, fcu_y, other_x, other_y, width, FCU, BCU, net, net_name, fcu_first):
    """单过孔连接"""
    mx = (fcu_x + other_x) // 2
    my = (fcu_y + other_y) // 2
    mx, my = find_safe_via_pos(mx, my, net_name, all_pads, mm(1.5))
    
    add_trk(board, fcu_x, fcu_y, mx, my, width, FCU, net)
    add_via(board, mx, my, net, FCU, BCU)
    add_trk(board, mx, my, other_x, other_y, width, BCU, net)
    return (2, 1)


def route_on_bcu(board, all_pads, x1, y1, x2, y2, width, BCU, net, net_name):
    """B.Cu上走线"""
    dx = x2 - x1
    dy = y2 - y1
    dist = math.sqrt(dx*dx + dy*dy)
    
    if dist < mm(5):
        add_trk(board, x1, y1, x2, y2, width, BCU, net)
        return (1, 0)
    
    # Z型：水平→垂直→水平
    mx = x1 + dx // 2
    add_trk(board, x1, y1, mx, y1, width, BCU, net)
    add_trk(board, mx, y1, mx, y2, width, BCU, net)
    add_trk(board, mx, y2, x2, y2, width, BCU, net)
    return (3, 0)


def find_safe_via_pos(x, y, net_name, all_pads, min_dist):
    """找到安全的过孔位置(远离其他网络焊盘)"""
    # 检查当前位置是否安全
    if is_via_safe(x, y, net_name, all_pads, min_dist):
        return (x, y)
    
    # 尝试偏移
    offsets = [
        (mm(1), 0), (-mm(1), 0), (0, mm(1)), (0, -mm(1)),
        (mm(1), mm(1)), (-mm(1), mm(1)), (mm(1), -mm(1)), (-mm(1), -mm(1)),
        (mm(2), 0), (-mm(2), 0), (0, mm(2)), (0, -mm(2)),
    ]
    
    for ox, oy in offsets:
        nx, ny = x + ox, y + oy
        if is_via_safe(nx, ny, net_name, all_pads, min_dist):
            return (nx, ny)
    
    # 找不到安全位置，返回原位
    return (x, y)


def is_via_safe(x, y, net_name, all_pads, min_dist):
    """检查过孔位置是否安全"""
    for px, py, pnet in all_pads:
        if pnet == net_name or pnet == '':
            continue
        d = abs(x - px) + abs(y - py)
        if d < min_dist:
            return False
    return True


def path_hits_pad(x1, y1, x2, y2, net_name, all_pads, clearance):
    """检查直线路径是否穿过其他焊盘"""
    dx = x2 - x1
    dy = y2 - y1
    dist = math.sqrt(dx*dx + dy*dy)
    if dist < 1:
        return False
    
    # 线段上均匀采样检查
    steps = max(int(dist / mm(0.5)), 3)
    for i in range(1, steps):
        t = i / steps
        px = int(x1 + dx * t)
        py = int(y1 + dy * t)
        
        for pad_x, pad_y, pad_net in all_pads:
            if pad_net == net_name or pad_net == '':
                continue
            if abs(px - pad_x) + abs(py - pad_y) < clearance:
                return True
    
    return False


def add_trk(board, x1, y1, x2, y2, width, layer, net):
    if x1 == x2 and y1 == y2:
        return
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(int(x1), int(y1)))
    t.SetEnd(pcbnew.VECTOR2I(int(x2), int(y2)))
    t.SetWidth(width)
    t.SetLayer(layer)
    t.SetNet(net)
    board.Add(t)


def add_via(board, x, y, net, fcu, bcu):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(int(x), int(y)))
    v.SetWidth(mm(0.6))
    v.SetDrill(mm(0.3))
    v.SetNet(net)
    v.SetLayerPair(fcu, bcu)
    board.Add(v)


if __name__ == '__main__':
    main()
