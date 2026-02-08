"""
CyberWand 4层PCB v2 - 重新设计
================================
核心改进:
1. 更大板面(90x150mm) + 更宽松元件间距
2. 信号总线有序布线(SPI/I2S/UART按组布线)
3. GND/3V3完全通过平面层 - 不走信号线
4. 5V/BAT走宽线在B.Cu
5. 严格碰撞检测 - 绝不强制放置
6. A*简化寻路避免交叉
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
# 板子参数 - 加大
# ============================================================
BL, BT = 85.0, 20.0   # 左上角
BW, BH = 90.0, 150.0  # 宽x高
BR, BB = BL+BW, BT+BH  # 右下角

# ============================================================
# 4层布局 - 功能分区, 更宽松间距
# ============================================================
# 区域规划 (90x150mm):
#
#   y=20~55:  LCD显示屏 + WS2812B LED灯带
#   y=55~70:  MPU6050 + LCD退耦 + ESP32退耦
#   y=70~115: ESP32-S3主控 (居中区域大)
#   y=82~120: 左侧按键, 右侧SD+DFPlayer+Mic
#   y=120~170: 电源管理区 (TP4056/ME6211/USB-C/电池/指示灯)
#
# ESP32 courtyard: ~(101,64)~(149,105.5) based on centered pos
# ESP32 antenna keepout: ~(101,64)~(149,85)

LAYOUT = {
    # ===== 中心: ESP32-S3 (y=90 center) =====
    'U1':  (130.0, 90.0, 0),

    # ===== ESP32退耦 (courtyard外上方, y<64) =====
    'C1':   (112.0, 59.0, 0),
    'C2':   (120.0, 59.0, 0),
    'C3':   (140.0, 59.0, 0),
    'R1':   (148.0, 59.0, 0),    # EN上拉
    'R12':  (156.0, 59.0, 0),    # IO46下拉

    # ===== 顶部: LCD显示屏 =====
    'LCD1': (130.0, 37.0, 90),
    'C5':   (158.0, 50.0, 0),   # LCD退耦1
    'C6':   (163.0, 50.0, 0),   # LCD退耦2

    # ===== 顶部: WS2812B LED =====
    'D1':   (96.0, 28.0, 0),
    'D2':   (108.0, 28.0, 0),
    'D3':   (120.0, 28.0, 0),
    'C12':  (96.0, 35.0, 0),    # LED退耦

    # ===== 左侧: MPU6050传感器区 =====
    'U2':   (96.0, 68.0, 0),
    'C4':   (96.0, 76.0, 0),    # MPU退耦
    'R2':   (96.0, 58.0, 0),    # SDA上拉 (courtyard外)
    'R3':   (100.0, 58.0, 0),   # SCL上拉 (courtyard外)

    # ===== 左侧: 按键区 (竖排, 间距大) =====
    'SW3':  (91.0, 85.0, 0),    # KEY_PLAY
    'R6':   (91.0, 92.0, 0),
    'SW2':  (91.0, 100.0, 0),   # KEY_SELECT
    'R5':   (91.0, 107.0, 0),
    'SW1':  (91.0, 115.0, 0),   # KEY_MODE
    'R4':   (91.0, 122.0, 0),

    # ===== 右侧: DFPlayer =====
    'U3':   (166.0, 75.0, 0),   # DFPlayer (上移)
    'C10':  (166.0, 63.0, 0),
    'C11':  (170.0, 63.0, 0),

    # ===== 右侧: SD卡 =====
    'J1':   (166.0, 110.0, 90),  # SD卡座 (下移)

    # ===== 右下: 麦克风 =====
    'MIC1': (166.0, 125.0, 0),

    # ===== 底部: 电源管理区 =====
    'U4':   (108.0, 140.0, 0),   # TP4056充电IC
    'U5':   (152.0, 140.0, 0),   # ME6211 LDO
    'J2':   (130.0, 163.0, 90),  # USB-C接口
    'C9':   (118.0, 160.0, 0),   # USB退耦
    'R7':   (121.0, 155.0, 0),   # CC1
    'R8':   (125.0, 155.0, 0),   # CC2
    'R9':   (101.0, 140.0, 0),   # TP4056 PROG
    'C7':   (152.0, 133.0, 0),   # LDO输入
    'C8':   (158.0, 133.0, 0),   # LDO输出

    # 充电指示灯 (左下)
    'D4':   (96.0, 137.0, 0),    # Red LED
    'D5':   (96.0, 145.0, 0),    # Green LED
    'R10':  (91.0, 137.0, 0),    # Red限流
    'R11':  (91.0, 145.0, 0),    # Green限流

    # ===== 背面元件 =====
    'BT1':  (130.0, 125.0, 180),  # 电池
    'LS1':  (130.0, 50.0, 180),   # 喇叭

    # ===== 安装孔 =====
    'H1':   (89.0, 24.0, 0),
    'H2':   (171.0, 24.0, 0),
    'H3':   (89.0, 166.0, 0),
    'H4':   (171.0, 166.0, 0),
}


def apply_layout(board):
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
    print("[铜箔] 设置4层...")
    for z in list(board.Zones()):
        board.Remove(z)
    
    FCU = board.GetLayerID('F.Cu')
    BCU = board.GetLayerID('B.Cu')
    IN1 = board.GetLayerID('In1.Cu')
    IN2 = board.GetLayerID('In2.Cu')
    gnd = board.FindNet("GND")
    v33 = board.FindNet("3V3")
    m = 1.0
    
    def make_zone(net, layer):
        zone = pcbnew.ZONE(board)
        zone.SetNet(net)
        zone.SetLayer(layer)
        zone.SetIsRuleArea(False)
        zone.SetDoNotAllowTracks(False)
        zone.SetDoNotAllowVias(False)
        zone.SetDoNotAllowPads(False)
        zone.SetDoNotAllowCopperPour(False)
        zone.SetDoNotAllowFootprints(False)
        # 创建轮廓 - 使用SHAPE_POLY_SET
        poly = pcbnew.SHAPE_POLY_SET()
        poly.NewOutline()
        poly.Append(mm(BL+m), mm(BT+m))
        poly.Append(mm(BR-m), mm(BT+m))
        poly.Append(mm(BR-m), mm(BB-m))
        poly.Append(mm(BL+m), mm(BB-m))
        zone.SetOutline(poly)
        zone.SetMinThickness(mm(0.2))
        zone.SetThermalReliefGap(mm(0.3))
        zone.SetThermalReliefSpokeWidth(mm(0.4))
        board.Add(zone)
    
    make_zone(gnd, FCU)
    make_zone(gnd, IN1)      # 完整GND平面
    if v33:
        make_zone(v33, IN2)   # 3V3电源平面
    else:
        make_zone(gnd, IN2)
    make_zone(gnd, BCU)
    print("  OK")


# ============================================================
# 4层路由器 v2
# ============================================================
class Router4L:
    def __init__(self, board):
        self.board = board
        self.FCU = board.GetLayerID('F.Cu')
        self.BCU = board.GetLayerID('B.Cu')
        self.tracks = {self.FCU: [], self.BCU: []}  # layer -> [(x1,y1,x2,y2,net)]
        self.vias = set()
        self.keepouts = []
        self.all_pads = []
        self.net_pads = defaultdict(list)
        self.n_trk = 0
        self.n_via = 0
    
    def init(self, pre_pads=None, pre_keepouts=None):
        if pre_keepouts:
            self.keepouts = pre_keepouts
        else:
            self._detect_keepouts()
        if pre_pads:
            self.all_pads = pre_pads
            for p in pre_pads:
                if p['net']:
                    self.net_pads[p['net']].append(p)
            print(f"  焊盘: {len(self.all_pads)}, 网络: {len(self.net_pads)}")
        else:
            self._collect_pads()
        self._clear_tracks()
    
    def _detect_keepouts(self):
        # 只从封装内获取keepout (例如ESP32天线区域)
        # 不迭代board.Zones()因为刚创建的zone对象有SWIG问题
        fps = self.board.GetFootprints()
        for i in range(len(fps)):
            fp = fps[i]
            try:
                fp_zones = fp.Zones()
                for j in range(len(fp_zones)):
                    z = fp_zones[j]
                    if z.GetIsRuleArea():
                        bb = z.GetBoundingBox()
                        self.keepouts.append((bb.GetLeft(),bb.GetTop(),bb.GetRight(),bb.GetBottom()))
            except Exception:
                pass
        # 手动添加ESP32天线keepout (基于之前的检测)
        # ESP32在(130,90), antenna keepout约(101,62)-(149,83)
        esp32_pos = LAYOUT.get('U1', (130, 90, 0))
        cx, cy = esp32_pos[0], esp32_pos[1]
        # ESP32-S3-WROOM-1 天线区域: 模块顶部约21mm高的区域
        ant_x1 = mm(cx - 24); ant_y1 = mm(cy - 28)
        ant_x2 = mm(cx + 24); ant_y2 = mm(cy - 7)
        if not any(abs(k[0]-ant_x1)<mm(1) and abs(k[1]-ant_y1)<mm(1) for k in self.keepouts):
            self.keepouts.append((ant_x1, ant_y1, ant_x2, ant_y2))
        print(f"  keepout区域: {len(self.keepouts)}")
        for kx1,ky1,kx2,ky2 in self.keepouts:
            print(f"    ({to_mm(kx1):.1f},{to_mm(ky1):.1f})-({to_mm(kx2):.1f},{to_mm(ky2):.1f})")
    
    def _collect_pads(self):
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
                p = {'ref':ref, 'x':pos.x, 'y':pos.y, 'on_f':on_f, 'on_b':on_b,
                     'is_th': on_f and on_b, 'net': net or ''}
                self.all_pads.append(p)
                if net:
                    self.net_pads[net].append(p)
        print(f"  焊盘: {len(self.all_pads)}, 网络: {len(self.net_pads)}")
    
    def _clear_tracks(self):
        # 走线已在外部清除 (zone操作前)
        pass
    
    def _in_keepout(self, x, y):
        for kx1,ky1,kx2,ky2 in self.keepouts:
            if kx1<=x<=kx2 and ky1<=y<=ky2:
                return True
        return False
    
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
    
    def _path_safe(self, x1, y1, x2, y2, layer, net_name, clearance=None):
        """检查走线段是否安全"""
        if clearance is None:
            clearance = mm(0.4)
        bm = mm(2)
        for v in [x1,x2]:
            if v<mm(BL)+bm or v>mm(BR)-bm: return False
        for v in [y1,y2]:
            if v<mm(BT)+bm or v>mm(BB)-bm: return False
        
        # 检查是否穿过keepout
        pts = 5
        dx = x2-x1; dy = y2-y1
        for t_i in range(pts+1):
            t = t_i / pts
            px = int(x1+dx*t); py = int(y1+dy*t)
            if self._in_keepout(px, py):
                return False
        
        # 检查不同网络走线交叉
        for tx1,ty1,tx2,ty2,tn in self.tracks[layer]:
            if tn == net_name: continue
            if self._segs_cross(x1,y1,x2,y2, tx1,ty1,tx2,ty2):
                return False
        
        # 检查是否穿过其他网络焊盘
        dist = math.sqrt(dx*dx+dy*dy)
        if dist < 1: return True
        steps = max(int(dist/mm(1.0)), 3)
        for s in range(1, steps):
            t = s/steps
            px = int(x1+dx*t); py = int(y1+dy*t)
            for p in self.all_pads:
                if p['net']==net_name or p['net']=='': continue
                # 焊盘在此层?
                if layer == self.FCU and not p['on_f'] and not p['is_th']: continue
                if layer == self.BCU and not p['on_b'] and not p['is_th']: continue
                d = math.sqrt((px-p['x'])**2+(py-p['y'])**2)
                if d < clearance:
                    return False
        return True
    
    def _add_trk(self, x1, y1, x2, y2, w, layer, net_obj, net_name):
        """添加走线 (仅在安全时)"""
        if x1==x2 and y1==y2: return True
        if not self._path_safe(x1,y1,x2,y2,layer,net_name):
            return False
        t = pcbnew.PCB_TRACK(self.board)
        t.SetStart(pcbnew.VECTOR2I(int(x1),int(y1)))
        t.SetEnd(pcbnew.VECTOR2I(int(x2),int(y2)))
        t.SetWidth(w); t.SetLayer(layer); t.SetNet(net_obj)
        self.board.Add(t)
        self.tracks[layer].append((x1,y1,x2,y2,net_name))
        self.n_trk += 1
        return True
    
    def _add_trk_force(self, x1, y1, x2, y2, w, layer, net_obj, net_name):
        """强制添加走线 (不检查交叉, 仅边界和keepout)"""
        if x1==x2 and y1==y2: return True
        bm = mm(2)
        for v in [x1,x2]:
            if v<mm(BL)+bm or v>mm(BR)-bm: return False
        for v in [y1,y2]:
            if v<mm(BT)+bm or v>mm(BB)-bm: return False
        # 仍然检查keepout
        dx=x2-x1; dy=y2-y1
        for t_i in range(6):
            t = t_i/5
            px=int(x1+dx*t); py=int(y1+dy*t)
            if self._in_keepout(px,py): return False
        
        t = pcbnew.PCB_TRACK(self.board)
        t.SetStart(pcbnew.VECTOR2I(int(x1),int(y1)))
        t.SetEnd(pcbnew.VECTOR2I(int(x2),int(y2)))
        t.SetWidth(w); t.SetLayer(layer); t.SetNet(net_obj)
        self.board.Add(t)
        self.tracks[layer].append((x1,y1,x2,y2,net_name))
        self.n_trk += 1
        return True
    
    def _safe_via(self, x, y, net_name):
        """检查via位置是否安全"""
        bm = mm(3)
        if x<mm(BL)+bm or x>mm(BR)-bm or y<mm(BT)+bm or y>mm(BB)-bm:
            return False
        if self._in_keepout(x,y): return False
        for p in self.all_pads:
            d = math.sqrt((x-p['x'])**2+(y-p['y'])**2)
            if d<mm(0.5): return False
            if p['net']!=net_name and p['net']!='' and p['net']!='GND':
                if d<mm(0.8): return False
        for vx,vy in self.vias:
            if math.sqrt((x-vx)**2+(y-vy)**2)<mm(0.7): return False
        return True
    
    def _add_via(self, x, y, net_obj, net_name):
        if not self._safe_via(x,y,net_name): return False
        v = pcbnew.PCB_VIA(self.board)
        v.SetPosition(pcbnew.VECTOR2I(int(x),int(y)))
        v.SetWidth(mm(0.5)); v.SetDrill(mm(0.25))
        v.SetNet(net_obj)
        v.SetLayerPair(self.FCU, self.BCU)
        self.board.Add(v)
        self.vias.add((x,y))
        self.n_via += 1
        return True
    
    def _find_via(self, cx, cy, net_name):
        for r in [0, mm(1.5), mm(2.5), mm(3.5), mm(4.5), mm(5.5), mm(7), mm(9), mm(12)]:
            if r == 0:
                cands = [(cx,cy)]
            else:
                cands = [(int(cx+r*math.cos(math.radians(a))),
                          int(cy+r*math.sin(math.radians(a))))
                         for a in range(0,360,15)]
            for nx,ny in cands:
                if self._safe_via(nx,ny,net_name):
                    return (nx,ny)
        return None
    
    def _crosses_keepout(self, x1, y1, x2, y2):
        """检查线段是否穿过keepout"""
        dx = x2-x1; dy = y2-y1
        for t_i in range(11):
            t = t_i/10
            px = int(x1+dx*t); py = int(y1+dy*t)
            if self._in_keepout(px, py):
                return True
        return False
    
    def _route_around_keepout(self, sx, sy, ex, ey, w, net_obj, net_name):
        """穿越keepout的特殊路由策略:
        F.Cu→via→B.Cu(侧面绕行)→via→F.Cu
        """
        side_left = mm(BL+5)
        side_right = mm(BR-5)
        
        for side_x in [side_left, side_right]:
            # 在起点附近找via - 尝试多个位置
            v1 = self._find_via(sx, sy, net_name)
            if not v1:
                # 向侧面偏移寻找
                for off in [mm(3), mm(-3), mm(5), mm(-5)]:
                    v1 = self._find_via(sx+off, sy, net_name)
                    if v1: break
            if not v1: continue
            v1x, v1y = v1
            
            v2 = self._find_via(ex, ey, net_name)
            if not v2:
                for off in [mm(3), mm(-3), mm(5), mm(-5)]:
                    v2 = self._find_via(ex+off, ey, net_name)
                    if v2: break
            if not v2: continue
            v2x, v2y = v2
            
            # 检查F.Cu短线是否安全
            ok_f1 = self._path_safe(sx,sy,v1x,v1y,self.FCU,net_name)
            ok_f2 = self._path_safe(v2x,v2y,ex,ey,self.FCU,net_name)
            if not (ok_f1 and ok_f2): continue
            
            # B.Cu: via1→侧边→via2 (3段L型)
            # via1 → (side_x, v1y) → (side_x, v2y) → via2
            s1 = self._path_safe(v1x,v1y,side_x,v1y,self.BCU,net_name)
            s2 = self._path_safe(side_x,v1y,side_x,v2y,self.BCU,net_name)
            s3 = self._path_safe(side_x,v2y,v2x,v2y,self.BCU,net_name)
            if s1 and s2 and s3:
                self._add_via(v1x,v1y,net_obj,net_name)
                self._add_via(v2x,v2y,net_obj,net_name)
                self._add_trk(sx,sy,v1x,v1y,w,self.FCU,net_obj,net_name)
                self._add_trk(v1x,v1y,side_x,v1y,w,self.BCU,net_obj,net_name)
                self._add_trk(side_x,v1y,side_x,v2y,w,self.BCU,net_obj,net_name)
                self._add_trk(side_x,v2y,v2x,v2y,w,self.BCU,net_obj,net_name)
                self._add_trk(v2x,v2y,ex,ey,w,self.FCU,net_obj,net_name)
                return True
            
            # 尝试不同的中间X位置
            for mid_off in [mm(5), mm(-5), mm(10), mm(-10)]:
                mx = side_x + mid_off
                s1 = self._path_safe(v1x,v1y,mx,v1y,self.BCU,net_name)
                s2 = self._path_safe(mx,v1y,mx,v2y,self.BCU,net_name)
                s3 = self._path_safe(mx,v2y,v2x,v2y,self.BCU,net_name)
                if s1 and s2 and s3:
                    self._add_via(v1x,v1y,net_obj,net_name)
                    self._add_via(v2x,v2y,net_obj,net_name)
                    self._add_trk(sx,sy,v1x,v1y,w,self.FCU,net_obj,net_name)
                    self._add_trk(v1x,v1y,mx,v1y,w,self.BCU,net_obj,net_name)
                    self._add_trk(mx,v1y,mx,v2y,w,self.BCU,net_obj,net_name)
                    self._add_trk(mx,v2y,v2x,v2y,w,self.BCU,net_obj,net_name)
                    self._add_trk(v2x,v2y,ex,ey,w,self.FCU,net_obj,net_name)
                    return True
        return False
    
    def _route_pair(self, p1, p2, net_name, net_obj, w):
        """路由一对焊盘"""
        sx, sy = p1['x'], p1['y']
        ex, ey = p2['x'], p2['y']
        dist = math.sqrt((ex-sx)**2+(ey-sy)**2)
        p1f = p1['on_f'] or p1['is_th']
        p2f = p2['on_f'] or p2['is_th']
        
        if net_name in ('GND',):
            return True  # GND通过平面层
        
        # 1. F.Cu直连
        if p1f and p2f:
            if self._add_trk(sx,sy,ex,ey,w,self.FCU,net_obj,net_name):
                return True
        
        # 2. F.Cu L型 (多种路径)
        if p1f and p2f:
            for off in [0, mm(2), mm(-2), mm(4), mm(-4), mm(6), mm(-6), mm(8), mm(-8)]:
                # 水平-垂直-水平
                mx = (sx+ex)//2 + off
                s1 = self._path_safe(sx,sy,mx,sy,self.FCU,net_name)
                s2 = self._path_safe(mx,sy,mx,ey,self.FCU,net_name)
                s3 = self._path_safe(mx,ey,ex,ey,self.FCU,net_name)
                if s1 and s2 and s3:
                    self._add_trk(sx,sy,mx,sy,w,self.FCU,net_obj,net_name)
                    self._add_trk(mx,sy,mx,ey,w,self.FCU,net_obj,net_name)
                    self._add_trk(mx,ey,ex,ey,w,self.FCU,net_obj,net_name)
                    return True
                # 垂直-水平-垂直
                my = (sy+ey)//2 + off
                s1 = self._path_safe(sx,sy,sx,my,self.FCU,net_name)
                s2 = self._path_safe(sx,my,ex,my,self.FCU,net_name)
                s3 = self._path_safe(ex,my,ex,ey,self.FCU,net_name)
                if s1 and s2 and s3:
                    self._add_trk(sx,sy,sx,my,w,self.FCU,net_obj,net_name)
                    self._add_trk(sx,my,ex,my,w,self.FCU,net_obj,net_name)
                    self._add_trk(ex,my,ex,ey,w,self.FCU,net_obj,net_name)
                    return True
        
        # 3. Via桥到B.Cu (F.Cu→Via→B.Cu→Via→F.Cu)
        if p1f and p2f:
            v1 = self._find_via(sx, sy, net_name)
            v2 = self._find_via(ex, ey, net_name)
            if v1 and v2:
                v1x,v1y = v1; v2x,v2y = v2
                # 先检查所有段是否可行
                ok_f1 = self._path_safe(sx,sy,v1x,v1y,self.FCU,net_name)
                ok_f2 = self._path_safe(v2x,v2y,ex,ey,self.FCU,net_name)
                ok_b = self._path_safe(v1x,v1y,v2x,v2y,self.BCU,net_name)
                if ok_f1 and ok_f2 and ok_b:
                    self._add_via(v1x,v1y,net_obj,net_name)
                    self._add_via(v2x,v2y,net_obj,net_name)
                    self._add_trk(sx,sy,v1x,v1y,w,self.FCU,net_obj,net_name)
                    self._add_trk(v1x,v1y,v2x,v2y,w,self.BCU,net_obj,net_name)
                    self._add_trk(v2x,v2y,ex,ey,w,self.FCU,net_obj,net_name)
                    return True
                # B.Cu L型
                if ok_f1 and ok_f2:
                    for boff in [0, mm(3), mm(-3), mm(5), mm(-5)]:
                        bmx = (v1x+v2x)//2 + boff
                        s1 = self._path_safe(v1x,v1y,bmx,v1y,self.BCU,net_name)
                        s2 = self._path_safe(bmx,v1y,bmx,v2y,self.BCU,net_name)
                        s3 = self._path_safe(bmx,v2y,v2x,v2y,self.BCU,net_name)
                        if s1 and s2 and s3:
                            self._add_via(v1x,v1y,net_obj,net_name)
                            self._add_via(v2x,v2y,net_obj,net_name)
                            self._add_trk(sx,sy,v1x,v1y,w,self.FCU,net_obj,net_name)
                            self._add_trk(v1x,v1y,bmx,v1y,w,self.BCU,net_obj,net_name)
                            self._add_trk(bmx,v1y,bmx,v2y,w,self.BCU,net_obj,net_name)
                            self._add_trk(bmx,v2y,v2x,v2y,w,self.BCU,net_obj,net_name)
                            self._add_trk(v2x,v2y,ex,ey,w,self.FCU,net_obj,net_name)
                            return True
        
        # 4. 通孔元件B.Cu直连
        if p1['is_th'] and p2['is_th']:
            if self._add_trk(sx,sy,ex,ey,w,self.BCU,net_obj,net_name):
                return True
            for off in [0, mm(3), mm(-3), mm(5), mm(-5), mm(7), mm(-7)]:
                mx = (sx+ex)//2 + off
                s1 = self._path_safe(sx,sy,mx,sy,self.BCU,net_name)
                s2 = self._path_safe(mx,sy,mx,ey,self.BCU,net_name)
                s3 = self._path_safe(mx,ey,ex,ey,self.BCU,net_name)
                if s1 and s2 and s3:
                    self._add_trk(sx,sy,mx,sy,w,self.BCU,net_obj,net_name)
                    self._add_trk(mx,sy,mx,ey,w,self.BCU,net_obj,net_name)
                    self._add_trk(mx,ey,ex,ey,w,self.BCU,net_obj,net_name)
                    return True
        
        # 4.5 Keepout绕行 (针对穿越天线区域的长距离路由)
        if p1f and p2f and self._crosses_keepout(sx,sy,ex,ey):
            if self._route_around_keepout(sx,sy,ex,ey,w,net_obj,net_name):
                return True
        
        # 5. Via桥+B.Cu L型 (更多选项)
        if p1f and p2f:
            for v_off in [mm(2), mm(3), mm(4), mm(5)]:
                for a in range(0, 360, 30):
                    v1 = self._find_via(int(sx+v_off*math.cos(math.radians(a))),
                                         int(sy+v_off*math.sin(math.radians(a))), net_name)
                    v2 = self._find_via(int(ex+v_off*math.cos(math.radians((a+180)%360))),
                                         int(ey+v_off*math.sin(math.radians((a+180)%360))), net_name)
                    if not v1 or not v2: continue
                    v1x,v1y = v1; v2x,v2y = v2
                    ok_f1 = self._path_safe(sx,sy,v1x,v1y,self.FCU,net_name)
                    ok_f2 = self._path_safe(v2x,v2y,ex,ey,self.FCU,net_name)
                    if not (ok_f1 and ok_f2): continue
                    # B.Cu直连
                    if self._path_safe(v1x,v1y,v2x,v2y,self.BCU,net_name):
                        self._add_via(v1x,v1y,net_obj,net_name)
                        self._add_via(v2x,v2y,net_obj,net_name)
                        self._add_trk(sx,sy,v1x,v1y,w,self.FCU,net_obj,net_name)
                        self._add_trk(v1x,v1y,v2x,v2y,w,self.BCU,net_obj,net_name)
                        self._add_trk(v2x,v2y,ex,ey,w,self.FCU,net_obj,net_name)
                        return True
                    # B.Cu L型
                    for boff in [0, mm(5), mm(-5), mm(10), mm(-10)]:
                        bmx = (v1x+v2x)//2 + boff
                        s1 = self._path_safe(v1x,v1y,bmx,v1y,self.BCU,net_name)
                        s2 = self._path_safe(bmx,v1y,bmx,v2y,self.BCU,net_name)
                        s3 = self._path_safe(bmx,v2y,v2x,v2y,self.BCU,net_name)
                        if s1 and s2 and s3:
                            self._add_via(v1x,v1y,net_obj,net_name)
                            self._add_via(v2x,v2y,net_obj,net_name)
                            self._add_trk(sx,sy,v1x,v1y,w,self.FCU,net_obj,net_name)
                            self._add_trk(v1x,v1y,bmx,v1y,w,self.BCU,net_obj,net_name)
                            self._add_trk(bmx,v1y,bmx,v2y,w,self.BCU,net_obj,net_name)
                            self._add_trk(bmx,v2y,v2x,v2y,w,self.BCU,net_obj,net_name)
                            self._add_trk(v2x,v2y,ex,ey,w,self.FCU,net_obj,net_name)
                            return True
        
        # 6. 通孔直连B.Cu (更多路径)
        if p1['is_th'] and p2['is_th']:
            for off in [mm(7), mm(-7), mm(10), mm(-10), mm(15), mm(-15)]:
                mx = (sx+ex)//2 + off
                s1 = self._path_safe(sx,sy,mx,sy,self.BCU,net_name)
                s2 = self._path_safe(mx,sy,mx,ey,self.BCU,net_name)
                s3 = self._path_safe(mx,ey,ex,ey,self.BCU,net_name)
                if s1 and s2 and s3:
                    self._add_trk(sx,sy,mx,sy,w,self.BCU,net_obj,net_name)
                    self._add_trk(mx,sy,mx,ey,w,self.BCU,net_obj,net_name)
                    self._add_trk(mx,ey,ex,ey,w,self.BCU,net_obj,net_name)
                    return True
        
        # 7. 跨层路由 (通孔→SMD或反向, 仅安全路由)
        v1 = self._find_via(sx, sy, net_name)
        v2 = self._find_via(ex, ey, net_name)
        if v1 and v2:
            v1x,v1y = v1; v2x,v2y = v2
            layer1 = self.FCU if p1f else self.BCU
            layer2 = self.FCU if p2f else self.BCU
            # 只在B.Cu路径安全时才执行
            ok_l1 = self._path_safe(sx,sy,v1x,v1y,layer1,net_name)
            ok_b = self._path_safe(v1x,v1y,v2x,v2y,self.BCU,net_name)
            ok_l2 = self._path_safe(v2x,v2y,ex,ey,layer2,net_name)
            if ok_l1 and ok_b and ok_l2:
                self._add_via(v1x,v1y,net_obj,net_name)
                self._add_via(v2x,v2y,net_obj,net_name)
                self._add_trk(sx,sy,v1x,v1y,w,layer1,net_obj,net_name)
                self._add_trk(v1x,v1y,v2x,v2y,w,self.BCU,net_obj,net_name)
                self._add_trk(v2x,v2y,ex,ey,w,layer2,net_obj,net_name)
                return True
        
        print(f"    [!] 无法路由 {net_name}: {p1['ref']}({to_mm(sx):.1f},{to_mm(sy):.1f})→{p2['ref']}({to_mm(ex):.1f},{to_mm(ey):.1f})")
        return False
    
    def route_gnd_vias(self):
        """为GND SMD焊盘添加via到GND平面"""
        gnd = self.board.FindNet('GND')
        if not gnd: return
        n = 0
        for p in self.net_pads.get('GND',[]):
            if p['is_th']: continue
            vpos = self._find_via(p['x'], p['y'], 'GND')
            if vpos:
                vx,vy = vpos
                d = math.sqrt((vx-p['x'])**2+(vy-p['y'])**2)
                if d < mm(3):
                    if self._add_via(vx,vy,gnd,'GND'):
                        layer = self.FCU if p['on_f'] else self.BCU
                        self._add_trk_force(p['x'],p['y'],vx,vy,mm(0.3),layer,gnd,'GND')
                        n += 1
        print(f"  GND via: {n}")
    
    def route_3v3_vias(self):
        """为3V3 SMD焊盘添加via到3V3电源平面"""
        v33 = self.board.FindNet('3V3')
        if not v33: return
        n = 0
        for p in self.net_pads.get('3V3',[]):
            if p['is_th']: continue
            vpos = self._find_via(p['x'], p['y'], '3V3')
            if vpos:
                vx,vy = vpos
                d = math.sqrt((vx-p['x'])**2+(vy-p['y'])**2)
                if d < mm(3):
                    if self._add_via(vx,vy,v33,'3V3'):
                        layer = self.FCU if p['on_f'] else self.BCU
                        self._add_trk_force(p['x'],p['y'],vx,vy,mm(0.35),layer,v33,'3V3')
                        n += 1
        print(f"  3V3 via: {n}")
    
    def route_signals(self):
        """路由所有信号网络"""
        # 排除GND和3V3 (通过平面层)
        skip = {'GND', '3V3'}
        signal_nets = {k:v for k,v in self.net_pads.items() if k not in skip and len(v)>=2}
        
        # 路由优先级
        def prio(n):
            if n in ('5V','BAT'): return 1
            nl = n.lower()
            if 'usb' in nl: return 2
            if 'spi' in nl: return 3
            if 'i2c' in nl: return 4
            if 'i2s' in nl: return 5
            if 'uart' in nl: return 6
            if 'key' in nl: return 7
            if 'led' in nl: return 8
            return 9
        
        def wid(n):
            if n in ('5V','BAT'): return 0.5
            return 0.2
        
        sorted_nets = sorted(signal_nets.items(), key=lambda x: prio(x[0]))
        routed = 0
        failed = 0
        
        failed_nets = []
        for net_name, pads in sorted_nets:
            net_obj = self.board.FindNet(net_name)
            if not net_obj:
                print(f"    [!] 网络 {net_name} 找不到net对象")
                continue
            w = mm(wid(net_name))
            
            # MST连接
            connected = [pads[0]]
            remaining = list(pads[1:])
            net_ok = True
            while remaining:
                best_d = float('inf')
                best_c = best_r = None
                for cp in connected:
                    for rp in remaining:
                        d = abs(cp['x']-rp['x'])+abs(cp['y']-rp['y'])
                        if d < best_d:
                            best_d = d; best_c = cp; best_r = rp
                if not best_c: break
                ok = self._route_pair(best_c, best_r, net_name, net_obj, w)
                if ok:
                    routed += 1
                else:
                    failed += 1
                    net_ok = False
                connected.append(best_r)
                remaining.remove(best_r)
            if not net_ok:
                failed_nets.append(net_name)
        
        print(f"  信号: 成功{routed}, 失败{failed}")
        if failed_nets:
            print(f"  失败网络: {failed_nets}")
    
    def route_all(self):
        print("[布线] 4层布线 v2...")
        self.route_gnd_vias()
        self.route_3v3_vias()
        self.route_signals()
        print(f"  走线: {self.n_trk}, 过孔: {self.n_via}")


def add_stitching_vias(board, keepouts):
    print("[GND缝合] ...")
    FCU = board.GetLayerID('F.Cu')
    BCU = board.GetLayerID('B.Cu')
    gnd = board.FindNet("GND")
    if not gnd: return
    
    def in_ko(x, y):
        xn=mm(x); yn=mm(y)
        for kx1,ky1,kx2,ky2 in keepouts:
            if kx1<=xn<=kx2 and ky1<=yn<=ky2: return True
        return False
    
    n = 0
    for x in range(int(BL)+4, int(BR), 15):
        for yp in [BT+3, BB-3]:
            if in_ko(x,yp): continue
            v = pcbnew.PCB_VIA(board)
            v.SetPosition(pcbnew.VECTOR2I(mm(x),mm(yp)))
            v.SetWidth(mm(0.5)); v.SetDrill(mm(0.25))
            v.SetNet(gnd); v.SetLayerPair(FCU,BCU)
            board.Add(v); n+=1
    for y in range(int(BT)+4, int(BB), 15):
        for xp in [BL+3, BR-3]:
            if in_ko(xp,y): continue
            v = pcbnew.PCB_VIA(board)
            v.SetPosition(pcbnew.VECTOR2I(mm(xp),mm(y)))
            v.SetWidth(mm(0.5)); v.SetDrill(mm(0.25))
            v.SetNet(gnd); v.SetLayerPair(FCU,BCU)
            board.Add(v); n+=1
    print(f"  OK: {n}")


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
    
    print(f"\n  === DRC结果 (4层PCB v2) ===")
    print(f"  未连接:      {len(unc)}")
    print(f"  总违规:      {len(viol)}")
    print(f"    短路:        {vtypes.get('shorting_items',0)}")
    print(f"    交叉:        {vtypes.get('tracks_crossing',0)}")
    print(f"    间距:        {vtypes.get('clearance',0)}")
    print(f"    keepout:     {vtypes.get('items_not_allowed',0)}")
    print(f"    悬空:        {vtypes.get('track_dangling',0)}")
    print(f"    Courtyard:   {vtypes.get('courtyards_overlap',0)}")
    print(f"  所有类型:")
    for t,c in sorted(vtypes.items(), key=lambda x:x[1], reverse=True):
        print(f"    {t:35s}: {c}")
    return vtypes


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    pcb = r'D:\thinkpad\Documents\cybewand_insta360\cybewand_insta360.kicad_pcb'
    drc = r'd:\win_workspace\CyberWand_Insta360\schematic\skidl\docs\DRC_4layer.json'
    
    print("="*60)
    print("CyberWand 4层PCB v2")
    print("="*60)
    
    board = pcbnew.LoadBoard(pcb)
    print("[OK] 加载")
    
    # ---- 在修改之前收集所有数据 ----
    print("[预收集] 收集焊盘和keepout数据...")
    FCU_id = board.GetLayerID('F.Cu')
    BCU_id = board.GetLayerID('B.Cu')
    
    # 收集封装keepout
    pre_keepouts = []
    fps0 = board.GetFootprints()
    for i in range(len(fps0)):
        fp = fps0[i]
        try:
            fp_zones = fp.Zones()
            for j in range(len(fp_zones)):
                z = fp_zones[j]
                if z.GetIsRuleArea():
                    bb = z.GetBoundingBox()
                    pre_keepouts.append((bb.GetLeft(),bb.GetTop(),bb.GetRight(),bb.GetBottom()))
        except Exception:
            pass
    
    # 添加ESP32天线keepout
    esp32_pos = LAYOUT.get('U1', (130, 90, 0))
    cx, cy = esp32_pos[0], esp32_pos[1]
    ant_ko = (mm(cx-24), mm(cy-28), mm(cx+24), mm(cy-7))
    if not any(abs(k[0]-ant_ko[0])<mm(1) and abs(k[1]-ant_ko[1])<mm(1) for k in pre_keepouts):
        pre_keepouts.append(ant_ko)
    print(f"  keepout: {len(pre_keepouts)}")
    
    # ---- 开始修改 ----
    board.SetCopperLayerCount(4)
    print("[层叠] 4层")
    
    ds = board.GetDesignSettings()
    ds.SetCopperLayerCount(4)
    ds.m_TrackMinWidth = mm(0.15)
    ds.m_MinClearance = mm(0.15)
    ds.m_ViasMinSize = mm(0.45)
    ds.m_MinThroughDrill = mm(0.2)
    ds.m_HoleToHoleMin = mm(0.15)
    try:
        ds.m_HoleClearance = mm(0.15)
    except Exception:
        pass
    
    set_board_outline(board)
    apply_layout(board)
    
    # ---- 在zone操作前收集焊盘数据 (layout后位置已更新) ----
    print("[收集] 布局后的焊盘数据...")
    pre_pads = []
    fps1 = board.GetFootprints()
    for i in range(len(fps1)):
        fp = fps1[i]
        ref = fp.GetReference()
        pads = fp.Pads()
        for j in range(len(pads)):
            pad = pads[j]
            net = pad.GetNetname()
            pos = pad.GetPosition()
            on_f = pad.IsOnLayer(FCU_id)
            on_b = pad.IsOnLayer(BCU_id)
            p = {'ref':ref, 'x':pos.x, 'y':pos.y, 'on_f':on_f, 'on_b':on_b,
                 'is_th': on_f and on_b, 'net': net or ''}
            pre_pads.append(p)
    print(f"  焊盘: {len(pre_pads)}")
    
    # 清除旧走线和过孔 (在zone操作前)
    print("[清除] 清除旧走线...")
    old_tracks = list(board.GetTracks())
    for t in old_tracks:
        board.Remove(t)
    print(f"  清除 {len(old_tracks)} 走线/过孔")
    
    # 现在才做zone操作 (会破坏SWIG包装器)
    set_copper_zones(board)
    
    router = Router4L(board)
    router.init(pre_pads=pre_pads, pre_keepouts=pre_keepouts)
    router.route_gnd_vias()
    router.route_3v3_vias()
    router.route_signals()
    print(f"  走线: {router.n_trk}, 过孔: {router.n_via}")
    
    add_stitching_vias(board, router.keepouts)
    
    # 铜箔填充
    print("[铜箔填充]...")
    zones = board.Zones()
    if len(zones)>0:
        filler = pcbnew.ZONE_FILLER(board)
        filler.Fill(zones)
    
    pcbnew.SaveBoard(pcb, board)
    print("[OK] 保存")
    
    print("\n[DRC] ...")
    if run_drc(pcb, drc):
        print_drc(drc)
    
    print("\n"+"="*60)

if __name__=='__main__':
    main()
