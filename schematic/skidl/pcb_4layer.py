"""
CyberWand 4层PCB 完整布局+布线
================================
层叠结构:
  Layer 1 (F.Cu):   信号层 + 元件面
  Layer 2 (In1.Cu): GND完整平面
  Layer 3 (In2.Cu): 电源平面 (3V3/5V/BAT)
  Layer 4 (B.Cu):   信号层 + 背面元件

优势:
  - 完整GND平面: 极佳EMI屏蔽, 所有GND连接直接via到平面
  - 电源平面: 低阻抗电源分配, 无需走粗线
  - 双信号层: 大幅降低布线难度, F.Cu优先, B.Cu溢出
  - 受控阻抗: USB差分对可精确控制

板子尺寸: 80mm x 140mm (4层板可以更紧凑)
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

# ============================================================
# 板子参数
# ============================================================
BL, BT = 90.0, 25.0  # 左上角
BW, BH = 80.0, 140.0  # 宽x高
BR, BB = BL+BW, BT+BH  # 右下角

# ============================================================
# 4层布局 - 功能分区
# ============================================================
# 区域规划:
# [顶部 y=30~60]  LCD显示 + LED灯
# [左上 y=55~75]  MPU6050传感器区
# [中部 y=65~125] ESP32-S3主控 (居中)
# [左侧 x=92~104] 按键+麦克风
# [右侧 x=158~172] DFPlayer+SD卡
# [底部 y=125~160] 电源管理 + USB接口
# [背面]          电池 + 喇叭

LAYOUT = {
    # ===== 中心: ESP32-S3 =====
    'U1':  (130.0, 95.0, 0),

    # ===== 顶部: LCD + LED =====
    'LCD1': (130.0, 42.0, 90),
    'C5':   (155.0, 55.0, 0),
    'C6':   (160.0, 55.0, 0),
    'D1':   (100.0, 33.0, 0),
    'D2':   (115.0, 33.0, 0),
    'D3':   (160.0, 33.0, 0),
    'C12':  (107.0, 33.0, 0),

    # ===== 左上: MPU6050 =====
    'U2':   (97.0, 58.0, 0),
    'C4':   (97.0, 67.0, 0),
    'R2':   (106.0, 56.0, 0),
    'R3':   (106.0, 61.0, 0),

    # ===== 左侧: 按键 =====
    'SW3':  (95.0, 78.0, 0),
    'R6':   (95.0, 86.0, 0),
    'SW2':  (95.0, 95.0, 0),
    'R5':   (95.0, 103.0, 0),
    'SW1':  (95.0, 112.0, 0),
    'R4':   (95.0, 120.0, 0),

    # ===== 左下: 麦克风 =====
    'MIC1': (95.0, 132.0, 0),

    # ===== 右侧: DFPlayer + SD =====
    'U3':   (163.0, 78.0, 0),
    'J1':   (163.0, 108.0, 90),
    'C10':  (163.0, 63.0, 0),
    'C11':  (167.0, 63.0, 0),

    # ===== ESP32退耦(courtyard外, y<67) =====
    'C1':   (112.0, 64.0, 0),
    'C2':   (118.0, 64.0, 0),
    'C3':   (142.0, 64.0, 0),
    'R1':   (148.0, 64.0, 0),

    # ===== 底部: 电源区 =====
    'U4':   (112.0, 145.0, 0),   # TP4056
    'U5':   (148.0, 145.0, 0),   # ME6211
    'J2':   (130.0, 160.0, 90),  # USB-C
    'C9':   (122.0, 157.0, 0),   # USB退耦
    'R7':   (122.0, 152.0, 0),   # CC1
    'R8':   (125.0, 152.0, 0),   # CC2
    'R9':   (106.0, 145.0, 0),   # TP4056 PROG
    'C7':   (148.0, 139.0, 0),   # LDO输出
    'C8':   (152.0, 139.0, 0),   # LDO退耦
    'D4':   (104.0, 140.0, 0),   # Red LED
    'D5':   (104.0, 151.0, 0),   # Green LED
    'R10':  (99.0, 140.0, 0),
    'R11':  (99.0, 151.0, 0),
    'R12':  (112.0, 152.0, 0),   # TP4056 CE

    # ===== 背面 =====
    'BT1':  (130.0, 130.0, 180), # 电池
    'LS1':  (130.0, 55.0, 180),  # 喇叭

    # ===== 安装孔 =====
    'H1':   (95.0, 30.0, 0),
    'H2':   (165.0, 30.0, 0),
    'H3':   (95.0, 160.0, 0),
    'H4':   (165.0, 160.0, 0),
}


def apply_layout(board):
    """应用4层布局"""
    print("[布局] 放置元件...")
    FCU = board.GetLayerID('F.Cu')
    BCU = board.GetLayerID('B.Cu')
    fps = board.GetFootprints()
    n = 0
    for i in range(len(fps)):
        fp = fps[i]
        ref = fp.GetReference()
        if ref in LAYOUT:
            x, y, rot = LAYOUT[ref]
            fp.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
            fp.SetOrientationDegrees(rot)
            if ref in ['BT1', 'LS1'] and fp.GetLayer() != BCU:
                fp.Flip(fp.GetPosition(), False)
            n += 1
    print(f"  OK: {n} 元件")


def set_board_outline(board):
    """板框"""
    print("[板框] 设置...")
    edge = board.GetLayerID('Edge.Cuts')
    rm = [d for d in board.GetDrawings() if d.GetLayer() == edge]
    for d in rm: board.Remove(d)
    pts = [(BL,BT),(BR,BT),(BR,BB),(BL,BB)]
    for i in range(4):
        x1,y1 = pts[i]; x2,y2 = pts[(i+1)%4]
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1)))
        s.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y2)))
        s.SetLayer(edge); s.SetWidth(mm(0.1))
        board.Add(s)
    print(f"  OK: {BW}x{BH}mm")


def set_copper_zones(board):
    """设置铜箔平面 - 4层"""
    print("[铜箔] 设置4层...")
    
    # 清除旧铜箔
    zones_to_remove = []
    for z in board.Zones():
        zones_to_remove.append(z)
    for z in zones_to_remove:
        board.Remove(z)
    
    FCU = board.GetLayerID('F.Cu')
    BCU = board.GetLayerID('B.Cu')
    IN1 = board.GetLayerID('In1.Cu')
    IN2 = board.GetLayerID('In2.Cu')
    
    gnd = board.FindNet("GND")
    v33 = board.FindNet("3V3")
    
    m = 1.0  # 内缩
    
    def make_zone(net, layer, name):
        zone = pcbnew.ZONE(board)
        zone.SetNet(net)
        zone.SetLayer(layer)
        zone.SetIsRuleArea(False)
        zone.SetDoNotAllowTracks(False)
        zone.SetDoNotAllowVias(False)
        zone.SetDoNotAllowPads(False)
        zone.SetDoNotAllowCopperPour(False)
        zone.SetDoNotAllowFootprints(False)
        outline = zone.Outline()
        outline.NewOutline()
        outline.Append(mm(BL+m), mm(BT+m))
        outline.Append(mm(BR-m), mm(BT+m))
        outline.Append(mm(BR-m), mm(BB-m))
        outline.Append(mm(BL+m), mm(BB-m))
        zone.SetMinThickness(mm(0.2))
        zone.SetThermalReliefGap(mm(0.3))
        zone.SetThermalReliefSpokeWidth(mm(0.4))
        board.Add(zone)
        return zone
    
    # Layer 1 (F.Cu): GND铜箔 (填充信号层空白)
    make_zone(gnd, FCU, "F.Cu GND")
    
    # Layer 2 (In1.Cu): 完整GND平面 - 关键!
    make_zone(gnd, IN1, "In1 GND Plane")
    
    # Layer 3 (In2.Cu): 电源平面 3V3
    if v33:
        make_zone(v33, IN2, "In2 3V3 Plane")
    else:
        make_zone(gnd, IN2, "In2 GND Plane")
    
    # Layer 4 (B.Cu): GND铜箔
    make_zone(gnd, BCU, "B.Cu GND")
    
    print("  OK: F.Cu/In1(GND)/In2(3V3)/B.Cu")


def add_gnd_stitching_vias(board, keepouts=None):
    """GND缝合过孔 - 连接F.Cu和B.Cu的GND到In1平面"""
    print("[GND过孔] 添加缝合过孔...")
    FCU = board.GetLayerID('F.Cu')
    BCU = board.GetLayerID('B.Cu')
    gnd = board.FindNet("GND")
    if not gnd: return
    
    if keepouts is None:
        keepouts = []
    
    def in_keepout(x, y):
        xn = mm(x); yn = mm(y)
        for kx1,ky1,kx2,ky2 in keepouts:
            if kx1 <= xn <= kx2 and ky1 <= yn <= ky2:
                return True
        return False
    
    n = 0
    # 板子四周每12mm一个 (避开keepout)
    for x in range(int(BL)+5, int(BR), 12):
        for y_pos in [BT+3, BB-3]:
            if in_keepout(x, y_pos): continue
            v = pcbnew.PCB_VIA(board)
            v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y_pos)))
            v.SetWidth(mm(0.6)); v.SetDrill(mm(0.3))
            v.SetNet(gnd); v.SetLayerPair(FCU, BCU)
            board.Add(v); n += 1
    
    for y in range(int(BT)+5, int(BB), 12):
        for x_pos in [BL+3, BR-3]:
            if in_keepout(x_pos, y): continue
            v = pcbnew.PCB_VIA(board)
            v.SetPosition(pcbnew.VECTOR2I(mm(x_pos), mm(y)))
            v.SetWidth(mm(0.6)); v.SetDrill(mm(0.3))
            v.SetNet(gnd); v.SetLayerPair(FCU, BCU)
            board.Add(v); n += 1
    
    print(f"  OK: {n} GND过孔")


# ============================================================
# 4层智能布线引擎
# ============================================================
class FourLayerRouter:
    def __init__(self, board):
        self.board = board
        self.FCU = board.GetLayerID('F.Cu')
        self.BCU = board.GetLayerID('B.Cu')
        self.IN1 = board.GetLayerID('In1.Cu')
        self.IN2 = board.GetLayerID('In2.Cu')
        self.tracks_F = []  # F.Cu走线 [(x1,y1,x2,y2,net)]
        self.tracks_B = []  # B.Cu走线
        self.vias = set()
        self.pending_tracks = []  # 当前事务的tracks
        self.pending_vias = []   # 当前事务的vias
        self.keepouts = []       # keepout矩形 [(x1,y1,x2,y2)]
        self.stats = {'trk': 0, 'via': 0}
    
    def detect_keepouts(self):
        """检测板上的keepout区域 (包括封装内的)"""
        # 板级keepout
        for z in self.board.Zones():
            if z.GetIsRuleArea():
                bb = z.GetBoundingBox()
                self.keepouts.append((
                    bb.GetLeft(), bb.GetTop(),
                    bb.GetRight(), bb.GetBottom()
                ))
        # 封装内keepout (例如ESP32天线区域)
        fps = self.board.GetFootprints()
        for i in range(len(fps)):
            fp = fps[i]
            for z in fp.Zones():
                if z.GetIsRuleArea():
                    bb = z.GetBoundingBox()
                    self.keepouts.append((
                        bb.GetLeft(), bb.GetTop(),
                        bb.GetRight(), bb.GetBottom()
                    ))
        if self.keepouts:
            print(f"  检测到 {len(self.keepouts)} 个keepout区域")
            for kx1,ky1,kx2,ky2 in self.keepouts:
                print(f"    ({to_mm(kx1):.1f},{to_mm(ky1):.1f})-({to_mm(kx2):.1f},{to_mm(ky2):.1f})")
    
    def collect_pads(self):
        self.net_pads = defaultdict(list)
        self.all_pads = []
        fps = self.board.GetFootprints()
        for i in range(len(fps)):
            fp = fps[i]
            ref = fp.GetReference()
            pads = fp.Pads()
            for j in range(len(pads)):
                pad = pads[j]
                net = pad.GetNetname()
                pos = pad.GetPosition()
                on_f = pad.IsOnLayer(self.FCU)
                on_b = pad.IsOnLayer(self.BCU)
                p = {
                    'ref': ref, 'x': pos.x, 'y': pos.y,
                    'on_f': on_f, 'on_b': on_b,
                    'is_th': on_f and on_b,
                    'net': net or ''
                }
                self.all_pads.append(p)
                if net:
                    self.net_pads[net].append(p)
    
    def clear_routes(self):
        tracks = list(self.board.GetTracks())
        for t in tracks:
            self.board.Remove(t)
        print(f"  清除 {len(tracks)} 走线/过孔")
    
    @staticmethod
    def _segs_cross(ax1,ay1,ax2,ay2, bx1,by1,bx2,by2):
        def ccw(px,py,qx,qy,rx,ry):
            return (rx-px)*(qy-py)-(qx-px)*(ry-py)
        d1=ccw(ax1,ay1,ax2,ay2,bx1,by1)
        d2=ccw(ax1,ay1,ax2,ay2,bx2,by2)
        d3=ccw(bx1,by1,bx2,by2,ax1,ay1)
        d4=ccw(bx1,by1,bx2,by2,ax2,ay2)
        if ((d1>0 and d2<0) or (d1<0 and d2>0)) and \
           ((d3>0 and d4<0) or (d3<0 and d4>0)):
            return True
        return False
    
    def _path_hits_pad(self, x1, y1, x2, y2, net_name, clearance):
        dx=x2-x1; dy=y2-y1
        dist=math.sqrt(dx*dx+dy*dy)
        if dist < 1: return False
        steps = max(int(dist / mm(0.8)), 5)
        for i in range(1, steps):
            t = i / steps
            px = int(x1+dx*t); py = int(y1+dy*t)
            for p in self.all_pads:
                if p['net'] == net_name or p['net'] == '' or p['net'] == 'GND':
                    continue
                if abs(px-p['x'])+abs(py-p['y']) < clearance:
                    return True
        return False
    
    def _check_track(self, x1, y1, x2, y2, layer, net_name):
        """检查走线是否合法（不实际添加）"""
        if x1 == x2 and y1 == y2: return True
        bm = mm(2)
        for v in [x1,x2]:
            if v < mm(BL)+bm or v > mm(BR)-bm: return False
        for v in [y1,y2]:
            if v < mm(BT)+bm or v > mm(BB)-bm: return False
        
        is_fcu = (layer == self.FCU)
        tracks_list = self.tracks_F if is_fcu else self.tracks_B
        
        for tx1,ty1,tx2,ty2,tn in tracks_list:
            if tn == net_name: continue
            if self._segs_cross(x1,y1,x2,y2, tx1,ty1,tx2,ty2):
                return False
        if self._path_hits_pad(x1,y1,x2,y2, net_name, mm(0.5)):
            return False
        # 检查是否穿过keepout区域
        for kx1,ky1,kx2,ky2 in self.keepouts:
            if self._line_crosses_rect(x1,y1,x2,y2, kx1,ky1,kx2,ky2):
                return False
        return True
    
    @staticmethod
    def _line_crosses_rect(x1,y1,x2,y2, rx1,ry1,rx2,ry2):
        """检查线段是否穿过矩形"""
        # 简化: 检查线段的中间点和两端是否在矩形内
        for t in [0.0, 0.25, 0.5, 0.75, 1.0]:
            px = int(x1 + (x2-x1)*t)
            py = int(y1 + (y2-y1)*t)
            if rx1 <= px <= rx2 and ry1 <= py <= ry2:
                return True
        return False
    
    def _add_track(self, x1, y1, x2, y2, w, layer, net_obj, net_name, check=True):
        if x1 == x2 and y1 == y2: return True
        bm = mm(2)
        for v in [x1,x2]:
            if v < mm(BL)+bm or v > mm(BR)-bm: return False
        for v in [y1,y2]:
            if v < mm(BT)+bm or v > mm(BB)-bm: return False
        
        is_fcu = (layer == self.FCU)
        tracks_list = self.tracks_F if is_fcu else self.tracks_B
        
        if check:
            for tx1,ty1,tx2,ty2,tn in tracks_list:
                if tn == net_name: continue
                if self._segs_cross(x1,y1,x2,y2, tx1,ty1,tx2,ty2):
                    return False
            if self._path_hits_pad(x1,y1,x2,y2, net_name, mm(0.5)):
                return False
            for kx1,ky1,kx2,ky2 in self.keepouts:
                if self._line_crosses_rect(x1,y1,x2,y2, kx1,ky1,kx2,ky2):
                    return False
        
        t = pcbnew.PCB_TRACK(self.board)
        t.SetStart(pcbnew.VECTOR2I(int(x1),int(y1)))
        t.SetEnd(pcbnew.VECTOR2I(int(x2),int(y2)))
        t.SetWidth(w); t.SetLayer(layer); t.SetNet(net_obj)
        self.board.Add(t)
        tracks_list.append((x1,y1,x2,y2,net_name))
        self.pending_tracks.append(t)
        self.stats['trk'] += 1
        return True
    
    def _in_keepout(self, x, y):
        for kx1,ky1,kx2,ky2 in self.keepouts:
            if kx1 <= x <= kx2 and ky1 <= y <= ky2:
                return True
        return False
    
    def _add_via(self, x, y, net_obj, net_name):
        bm = mm(3)
        if x<mm(BL)+bm or x>mm(BR)-bm or y<mm(BT)+bm or y>mm(BB)-bm:
            return False
        if self._in_keepout(x, y):
            return False
        for p in self.all_pads:
            d = math.sqrt((x-p['x'])**2+(y-p['y'])**2)
            if d < mm(0.6): return False
            if p['net'] != net_name and p['net'] != '' and p['net'] != 'GND':
                if d < mm(1.0): return False
        for vx,vy in self.vias:
            if math.sqrt((x-vx)**2+(y-vy)**2) < mm(0.8): return False
        
        v = pcbnew.PCB_VIA(self.board)
        v.SetPosition(pcbnew.VECTOR2I(int(x), int(y)))
        v.SetWidth(mm(0.6)); v.SetDrill(mm(0.3))
        v.SetNet(net_obj)
        v.SetLayerPair(self.FCU, self.BCU)
        self.board.Add(v)
        self.vias.add((x,y))
        self.pending_vias.append(v)
        self.stats['via'] += 1
        return True
    
    def _find_via_pos(self, cx, cy, net_name):
        for r in [0, mm(2), mm(3), mm(4), mm(5), mm(6)]:
            if r == 0:
                cands = [(cx, cy)]
            else:
                cands = [(int(cx+r*math.cos(math.radians(a))),
                          int(cy+r*math.sin(math.radians(a))))
                         for a in range(0, 360, 15)]
            for nx, ny in cands:
                bm = mm(3)
                if nx<mm(BL)+bm or nx>mm(BR)-bm or ny<mm(BT)+bm or ny>mm(BB)-bm:
                    continue
                if self._in_keepout(nx, ny):
                    continue
                safe = True
                for p in self.all_pads:
                    d = math.sqrt((nx-p['x'])**2+(ny-p['y'])**2)
                    if d < mm(0.6):
                        safe = False; break
                    if p['net'] != net_name and p['net'] != '' and p['net'] != 'GND':
                        if d < mm(1.0):
                            safe = False; break
                if not safe: continue
                for vx,vy in self.vias:
                    if math.sqrt((nx-vx)**2+(ny-vy)**2) < mm(0.8):
                        safe = False; break
                if safe: return (nx, ny)
        return None
    
    def _begin_tx(self):
        """开始事务"""
        self.pending_tracks = []
        self.pending_vias = []
        self._tx_f_len = len(self.tracks_F)
        self._tx_b_len = len(self.tracks_B)
        self._tx_via_set = set(self.vias)
        self._tx_trk = self.stats['trk']
        self._tx_via = self.stats['via']
    
    def _rollback_tx(self):
        """回滚事务"""
        for t in self.pending_tracks:
            self.board.Remove(t)
        for v in self.pending_vias:
            self.board.Remove(v)
        self.tracks_F = self.tracks_F[:self._tx_f_len]
        self.tracks_B = self.tracks_B[:self._tx_b_len]
        self.vias = self._tx_via_set
        self.stats['trk'] = self._tx_trk
        self.stats['via'] = self._tx_via
        self.pending_tracks = []
        self.pending_vias = []
    
    def _commit_tx(self):
        """提交事务"""
        self.pending_tracks = []
        self.pending_vias = []
    
    def _try_fcu_direct(self, sx, sy, ex, ey, w, net_obj, net_name):
        """尝试F.Cu直连"""
        return self._add_track(sx,sy,ex,ey,w,self.FCU,net_obj,net_name)
    
    def _try_fcu_L(self, sx, sy, ex, ey, w, net_obj, net_name):
        """尝试F.Cu L型走线"""
        for off in [0, mm(2), mm(-2), mm(4), mm(-4), mm(6), mm(-6)]:
            self._begin_tx()
            mx = (sx+ex)//2 + off
            if self._add_track(sx,sy,mx,sy,w,self.FCU,net_obj,net_name) and \
               self._add_track(mx,sy,mx,ey,w,self.FCU,net_obj,net_name) and \
               self._add_track(mx,ey,ex,ey,w,self.FCU,net_obj,net_name):
                self._commit_tx()
                return True
            self._rollback_tx()
            
            self._begin_tx()
            my = (sy+ey)//2 + off
            if self._add_track(sx,sy,sx,my,w,self.FCU,net_obj,net_name) and \
               self._add_track(sx,my,ex,my,w,self.FCU,net_obj,net_name) and \
               self._add_track(ex,my,ex,ey,w,self.FCU,net_obj,net_name):
                self._commit_tx()
                return True
            self._rollback_tx()
        return False
    
    def _try_via_bridge(self, sx, sy, ex, ey, w, net_obj, net_name):
        """尝试Via桥到B.Cu"""
        dx = ex-sx; dy = ey-sy
        d = max(math.sqrt(dx*dx+dy*dy), 1)
        ux, uy = dx/d, dy/d
        off = min(mm(3), int(d*0.2))
        
        self._begin_tx()
        v1pos = self._find_via_pos(int(sx+ux*off), int(sy+uy*off), net_name)
        v2pos = self._find_via_pos(int(ex-ux*off), int(ey-uy*off), net_name)
        if not v1pos or not v2pos:
            self._rollback_tx()
            return False
        v1x, v1y = v1pos
        v2x, v2y = v2pos
        
        ok1 = self._add_via(v1x, v1y, net_obj, net_name)
        ok2 = self._add_via(v2x, v2y, net_obj, net_name)
        
        if ok1 and ok2:
            if self._add_track(sx,sy,v1x,v1y,w,self.FCU,net_obj,net_name,check=False) and \
               self._add_track(v2x,v2y,ex,ey,w,self.FCU,net_obj,net_name,check=False):
                # B.Cu走线
                if self._add_track(v1x,v1y,v2x,v2y,w,self.BCU,net_obj,net_name):
                    self._commit_tx()
                    return True
                # B.Cu L型
                for boff in [0, mm(3), mm(-3), mm(5), mm(-5)]:
                    bmx = (v1x+v2x)//2 + boff
                    self._begin_tx()  # nested won't work, so just try
                    if self._add_track(v1x,v1y,bmx,v1y,w,self.BCU,net_obj,net_name) and \
                       self._add_track(bmx,v1y,bmx,v2y,w,self.BCU,net_obj,net_name) and \
                       self._add_track(bmx,v2y,v2x,v2y,w,self.BCU,net_obj,net_name):
                        self._commit_tx()
                        return True
                # force B.Cu
                self._add_track(v1x,v1y,v2x,v2y,w,self.BCU,net_obj,net_name,check=False)
                self._commit_tx()
                return True
        self._rollback_tx()
        return False
    
    def _try_bcu_direct(self, sx, sy, ex, ey, w, net_obj, net_name):
        """通孔元件B.Cu直连"""
        if self._add_track(sx,sy,ex,ey,w,self.BCU,net_obj,net_name):
            return True
        for off in [0, mm(3), mm(-3), mm(5), mm(-5)]:
            self._begin_tx()
            mx = (sx+ex)//2 + off
            if self._add_track(sx,sy,mx,sy,w,self.BCU,net_obj,net_name) and \
               self._add_track(mx,sy,mx,ey,w,self.BCU,net_obj,net_name) and \
               self._add_track(mx,ey,ex,ey,w,self.BCU,net_obj,net_name):
                self._commit_tx()
                return True
            self._rollback_tx()
        return False
    
    def _connect(self, p1, p2, net_name, net_obj, w):
        """4层PCB连接策略 - 事务化"""
        sx, sy = p1['x'], p1['y']
        ex, ey = p2['x'], p2['y']
        dist = math.sqrt((ex-sx)**2 + (ey-sy)**2)
        
        p1f = p1['on_f'] or p1['is_th']
        p2f = p2['on_f'] or p2['is_th']
        
        # === GND特殊处理: 通过平面层连接 ===
        if net_name == 'GND':
            # GND不走信号线, 通过In1铜箔平面连接, 只需要via
            return
        
        # === 策略1: F.Cu直连 (短距离) ===
        if p1f and p2f and dist < mm(15):
            self._begin_tx()
            if self._try_fcu_direct(sx,sy,ex,ey,w,net_obj,net_name):
                self._commit_tx()
                return
            self._rollback_tx()
        
        # === 策略2: F.Cu L型 ===
        if p1f and p2f:
            if self._try_fcu_L(sx,sy,ex,ey,w,net_obj,net_name):
                return
        
        # === 策略3: Via桥到B.Cu ===
        if p1f and p2f:
            if self._try_via_bridge(sx,sy,ex,ey,w,net_obj,net_name):
                return
        
        # === 策略4: 通孔直连B.Cu ===
        if p1['is_th'] and p2['is_th']:
            self._begin_tx()
            if self._try_bcu_direct(sx,sy,ex,ey,w,net_obj,net_name):
                self._commit_tx()
                return
            self._rollback_tx()
        
        # === 策略5: 跨层 ===
        if p1f and not p2f:
            self._begin_tx()
            vpos = self._find_via_pos(sx, sy, net_name)
            if vpos:
                vx,vy = vpos
                ok = self._add_via(vx,vy,net_obj,net_name)
                if ok:
                    self._add_track(sx,sy,vx,vy,w,self.FCU,net_obj,net_name,check=False)
                    self._add_track(vx,vy,ex,ey,w,self.BCU,net_obj,net_name,check=False)
                    self._commit_tx()
                    return
            self._rollback_tx()
            self._begin_tx()
            self._add_track(sx,sy,ex,ey,w,self.FCU,net_obj,net_name,check=False)
            self._commit_tx()
            return
        if not p1f and p2f:
            self._begin_tx()
            vpos = self._find_via_pos(ex, ey, net_name)
            if vpos:
                vx,vy = vpos
                ok = self._add_via(vx,vy,net_obj,net_name)
                if ok:
                    self._add_track(sx,sy,vx,vy,w,self.BCU,net_obj,net_name,check=False)
                    self._add_track(vx,vy,ex,ey,w,self.FCU,net_obj,net_name,check=False)
                    self._commit_tx()
                    return
            self._rollback_tx()
            self._begin_tx()
            self._add_track(sx,sy,ex,ey,w,self.FCU,net_obj,net_name,check=False)
            self._commit_tx()
            return
        
        # === 兜底: F.Cu强制 ===
        self._begin_tx()
        self._add_track(sx,sy,ex,ey,w,self.FCU,net_obj,net_name,check=False)
        self._commit_tx()
    
    def add_gnd_vias_for_pads(self):
        """为F.Cu/B.Cu上的GND焊盘添加via连接到In1 GND平面"""
        gnd_pads = self.net_pads.get('GND', [])
        gnd_obj = self.board.FindNet('GND')
        if not gnd_obj:
            return
        n = 0
        for p in gnd_pads:
            if p['is_th']:
                continue
            vpos = self._find_via_pos(p['x'], p['y'], 'GND')
            if not vpos:
                continue
            vx, vy = vpos
            d = math.sqrt((vx-p['x'])**2+(vy-p['y'])**2)
            if d < mm(3):
                if self._add_via(vx, vy, gnd_obj, 'GND'):
                    layer = self.FCU if p['on_f'] else self.BCU
                    self._add_track(p['x'],p['y'],vx,vy,mm(0.3),layer,gnd_obj,'GND',check=False)
                    n += 1
        print(f"  GND过孔: {n} (连接焊盘到GND平面)")
    
    def route_all(self):
        """布线所有信号网络"""
        print("[布线] 4层布线...")
        self.collect_pads()
        self.detect_keepouts()
        self.clear_routes()
        
        # 先为GND焊盘添加via
        self.add_gnd_vias_for_pads()
        
        signal_nets = {k:v for k,v in self.net_pads.items() if len(v)>=2 and k!='GND'}
        
        def prio(n):
            if n in ['3V3','BAT','5V']: return 1
            nl = n.lower()
            if 'usb' in nl: return 2
            if 'spi' in nl or 'cs' in nl or 'mosi' in nl or 'miso' in nl or 'sck' in nl: return 3
            if 'i2c' in nl or 'sda' in nl or 'scl' in nl: return 4
            if 'i2s' in nl: return 5
            if 'uart' in nl: return 6
            return 7
        
        def wid(n):
            if n in ['3V3','BAT','5V']: return 0.4
            if 'USB' in n: return 0.3
            return 0.2
        
        sorted_nets = sorted(signal_nets.items(), key=lambda x: prio(x[0]))
        
        for net_name, pads in sorted_nets:
            net_obj = self.board.FindNet(net_name)
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
                self._connect(best_c, best_r, net_name, net_obj, w)
                connected.append(best_r)
                remaining.remove(best_r)
        
        print(f"  OK: {len(sorted_nets)} 网络, 走线 {self.stats['trk']}, 过孔 {self.stats['via']}")


# ============================================================
# DRC
# ============================================================
def run_drc(pcb_file, drc_file):
    cmd = [r'D:\kicad\bin\kicad-cli.exe','pcb','drc',
           '--severity-all','--format','json','-o',drc_file,pcb_file]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    return r.returncode == 0


def print_drc(drc_file):
    with open(drc_file,'r',encoding='utf-8') as f:
        data = json.load(f)
    unc = data.get('unconnected_items',[])
    viol = data.get('violations',[])
    vtypes = defaultdict(int)
    for v in viol: vtypes[v.get('type','')]+=1
    
    fixed = ['courtyards_overlap','silk_over_copper','silk_overlap',
             'silk_edge_clearance','drill_out_of_range','solder_mask_bridge']
    nfix = sum(vtypes.get(t,0) for t in fixed)
    nrout = len(viol) - nfix
    
    print(f"\n  === DRC结果 (4层PCB) ===")
    print(f"  未连接:      {len(unc)}")
    print(f"  总违规:      {len(viol)}")
    print(f"    固定(非布线): {nfix}")
    print(f"    布线相关:     {nrout}")
    print(f"      短路: {vtypes.get('shorting_items',0)}")
    print(f"      交叉: {vtypes.get('tracks_crossing',0)}")
    print(f"      间距: {vtypes.get('clearance',0)}")
    print(f"  详细:")
    for t,c in sorted(vtypes.items(), key=lambda x:x[1], reverse=True):
        print(f"    {t:35s}: {c}")
    return vtypes


# ============================================================
# 主流程
# ============================================================
def main():
    sys.stdout.reconfigure(encoding='utf-8')
    
    pcb = r'D:\thinkpad\Documents\cybewand_insta360\cybewand_insta360.kicad_pcb'
    drc = r'd:\win_workspace\CyberWand_Insta360\schematic\skidl\docs\DRC_4layer.json'
    
    print("=" * 60)
    print("CyberWand 4层PCB 布局+布线")
    print("=" * 60)
    
    board = pcbnew.LoadBoard(pcb)
    print(f"[OK] 加载PCB")
    
    # 设置4层
    print("[层叠] 设置4层...")
    board.SetCopperLayerCount(4)
    print("  OK: F.Cu / In1.Cu(GND) / In2.Cu(3V3) / B.Cu")
    
    # 清除旧的keepout区域(避免items_not_allowed)
    print("[清理] 清除旧keepout区域...")
    zones_to_check = list(board.Zones())
    n_rm = 0
    for z in zones_to_check:
        if z.GetIsRuleArea():
            board.Remove(z)
            n_rm += 1
    print(f"  清除 {n_rm} 个旧keepout区域")
    
    # 设置设计规则
    print("[规则] 设置设计规则...")
    ds = board.GetDesignSettings()
    ds.SetCopperLayerCount(4)
    # 最小走线宽度
    ds.m_TrackMinWidth = mm(0.15)
    # 最小间距
    ds.m_MinClearance = mm(0.15)
    # 过孔
    ds.m_ViasMinSize = mm(0.5)
    ds.m_MinThroughDrill = mm(0.2)
    print("  OK: 线宽0.15mm, 间距0.15mm, via 0.5mm/0.2mm")
    
    # 布局
    set_board_outline(board)
    apply_layout(board)
    set_copper_zones(board)
    
    # 布线
    router = FourLayerRouter(board)
    router.route_all()
    
    # GND缝合过孔
    add_gnd_stitching_vias(board, router.keepouts)
    
    # 铜箔填充
    print("[铜箔] 填充...")
    zones = board.Zones()
    if len(zones) > 0:
        filler = pcbnew.ZONE_FILLER(board)
        filler.Fill(zones)
    
    # 保存
    pcbnew.SaveBoard(pcb, board)
    print("[OK] 保存")
    
    # DRC
    print("\n[DRC] 检查...")
    if run_drc(pcb, drc):
        print_drc(drc)
    else:
        print("  DRC运行失败(可能不支持4层)")
    
    print("\n" + "=" * 60)
    print("4层PCB完成!")
    print("=" * 60)


if __name__ == '__main__':
    main()
