"""
CyberWand PCB v3 - 避开ESP32底部GND焊盘
==========================================
关键修正:
1. ESP32-S3底部有大GND热焊盘(约25x18mm)，B.Cu走线必须绕开
2. C1-C3退耦电容移出ESP32 courtyard
3. B.Cu走线走板子边缘通道，不穿过ESP32中心
4. GND添加stitching vias帮助铜箔连通
"""
import pcbnew, math, sys, os, json, subprocess
from collections import defaultdict

def mm(v): return int(v * 1000000)
def to_mm(v): return v / 1000000

# 板框
BL, BT = 85.0, 20.0
BW, BH = 100.0, 180.0
BR, BB = BL+BW, BT+BH

# ESP32禁区(B.Cu走线不能穿过)
# 实际B.Cu只有12个0.6mm GND热过孔, 范围132.1~134.9, 106.1~108.9
# 加2mm margin即可
ESP_CX, ESP_CY = 133.5, 107.5
ESP_FORBID_X1 = 130.0  # 实际132.1 - 2mm
ESP_FORBID_X2 = 137.0  # 实际134.9 + 2mm
ESP_FORBID_Y1 = 104.0  # 实际106.1 - 2mm
ESP_FORBID_Y2 = 111.0  # 实际108.9 + 2mm

# ============================================================
# 布局 - C1-C3移出ESP32 courtyard
# ============================================================
LAYOUT = {
    # ESP32 居中
    'U1':  (135.0, 105.0, 0),

    # ==== 顶区(y=28~55): LCD+LED ====
    'LCD1': (135.0, 48.0, 90),
    'C5':   (158.0, 48.0, 0),
    'C6':   (162.0, 48.0, 0),
    'D1':   (100.0, 32.0, 0),
    'D2':   (120.0, 32.0, 0),
    'D3':   (168.0, 32.0, 0),
    'C12':  (110.0, 32.0, 0),

    # ==== 左上(x=88~108, y=56~75): MPU6050 ====
    'U2':   (96.0, 62.0, 0),
    'C4':   (96.0, 72.0, 0),
    'R2':   (106.0, 60.0, 0),
    'R3':   (106.0, 65.0, 0),

    # ==== 左侧(x=88~100, y=80~140): 按键+麦克风 ====
    'SW3':  (92.0, 84.0, 0),
    'R6':   (92.0, 93.0, 0),
    'SW2':  (92.0, 102.0, 0),
    'R5':   (92.0, 111.0, 0),
    'SW1':  (92.0, 120.0, 0),
    'R4':   (92.0, 129.0, 0),
    'MIC1': (92.0, 145.0, 0),

    # ==== 右侧(x=165~178): DFPlayer+SD ====
    'U3':   (172.0, 82.0, 0),
    'J1':   (172.0, 118.0, 90),
    'C10':  (172.0, 65.0, 0),
    'C11':  (176.0, 65.0, 0),

    # ==== ESP32退耦(放在ESP32上方/左方，在courtyard外) ====
    'C1':   (108.0, 78.0, 0),   # ESP32左上角外
    'C2':   (112.0, 78.0, 0),
    'C3':   (116.0, 78.0, 0),
    'R1':   (108.0, 82.0, 0),

    # ==== 底区(y=150~195): 电源 ====
    'U4':   (115.0, 162.0, 0),
    'U5':   (155.0, 162.0, 0),
    'J2':   (135.0, 188.0, 90),
    'C9':   (125.0, 184.0, 0),
    'R7':   (123.0, 178.0, 0),
    'R8':   (129.0, 178.0, 0),
    'R9':   (108.0, 162.0, 0),
    'C7':   (153.0, 156.0, 0),
    'C8':   (160.0, 156.0, 0),
    'D4':   (105.0, 156.0, 0),
    'D5':   (105.0, 163.0, 0),
    'R10':  (99.0, 156.0, 0),
    'R11':  (99.0, 163.0, 0),
    'R12':  (115.0, 170.0, 0),

    # 背面
    'BT1':  (135.0, 148.0, 180),
    'LS1':  (135.0, 58.0, 180),

    # 安装孔
    'H1':   (90.0, 25.0, 0),
    'H2':   (180.0, 25.0, 0),
    'H3':   (90.0, 195.0, 0),
    'H4':   (180.0, 195.0, 0),
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


def set_zones(board):
    print("[铜箔] GND...")
    zones_to_remove = []
    for z in board.Zones():
        zones_to_remove.append(z)
    for z in zones_to_remove:
        board.Remove(z)
    gnd = board.FindNet("GND")
    if not gnd: print("  [!] 无GND"); return
    FCU = board.GetLayerID('F.Cu')
    BCU = board.GetLayerID('B.Cu')
    m = 1.5
    for ly in [FCU, BCU]:
        zone = pcbnew.ZONE(board)
        zone.SetNet(gnd)
        zone.SetLayer(ly)
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
        zone.SetMinThickness(mm(0.25))
        zone.SetThermalReliefGap(mm(0.5))
        zone.SetThermalReliefSpokeWidth(mm(0.5))
        board.Add(zone)
    print("  OK: 双面GND")


def add_gnd_vias(board):
    """添加GND缝合过孔帮助铜箔连通"""
    print("[GND过孔] 添加...")
    FCU = board.GetLayerID('F.Cu')
    BCU = board.GetLayerID('B.Cu')
    gnd = board.FindNet("GND")
    if not gnd: return
    
    n = 0
    # 在板子边缘和ESP32周围添加
    positions = []
    # 板子四边
    for x in range(int(BL)+5, int(BR)-4, 15):
        positions.append((x, BT+5))
        positions.append((x, BB-5))
    for y in range(int(BT)+5, int(BB)-4, 15):
        positions.append((BL+5, y))
        positions.append((BR-5, y))
    # ESP32禁区边缘
    for x in range(int(ESP_FORBID_X1), int(ESP_FORBID_X2)+1, 10):
        positions.append((x, ESP_FORBID_Y1-3))
        positions.append((x, ESP_FORBID_Y2+3))
    for y in range(int(ESP_FORBID_Y1), int(ESP_FORBID_Y2)+1, 10):
        positions.append((ESP_FORBID_X1-3, y))
        positions.append((ESP_FORBID_X2+3, y))
    
    for x, y in positions:
        if x < BL+3 or x > BR-3 or y < BT+3 or y > BB-3:
            continue
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
        v.SetWidth(mm(0.8))
        v.SetDrill(mm(0.4))
        v.SetNet(gnd)
        v.SetLayerPair(FCU, BCU)
        board.Add(v)
        n += 1
    print(f"  OK: {n} GND过孔")


# ============================================================
# 安全布线 - 避开ESP32底部
# ============================================================
class SafeRouter:
    def __init__(self, board):
        self.board = board
        self.FCU = board.GetLayerID('F.Cu')
        self.BCU = board.GetLayerID('B.Cu')
        self.tracks = {'F': [], 'B': []}
        self.vias = set()
        self.stats = {'trk': 0, 'via': 0, 'fail': 0}
    
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
    
    def _in_esp_zone(self, x, y):
        """点是否在ESP32禁区内"""
        return (mm(ESP_FORBID_X1) <= x <= mm(ESP_FORBID_X2) and
                mm(ESP_FORBID_Y1) <= y <= mm(ESP_FORBID_Y2))
    
    def _line_crosses_esp(self, x1, y1, x2, y2):
        """线段是否穿过ESP32禁区"""
        if self._in_esp_zone(x1, y1) or self._in_esp_zone(x2, y2):
            return True
        # 检查线段是否与禁区矩形相交
        fx1, fy1 = mm(ESP_FORBID_X1), mm(ESP_FORBID_Y1)
        fx2, fy2 = mm(ESP_FORBID_X2), mm(ESP_FORBID_Y2)
        edges = [
            (fx1,fy1, fx2,fy1),  # top
            (fx2,fy1, fx2,fy2),  # right
            (fx2,fy2, fx1,fy2),  # bottom
            (fx1,fy2, fx1,fy1),  # left
        ]
        for ex1,ey1,ex2,ey2 in edges:
            if self._segs_cross(x1,y1,x2,y2, ex1,ey1,ex2,ey2):
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
    
    def _add_track(self, x1, y1, x2, y2, w, layer, net_obj, net_name, check=True):
        if x1==x2 and y1==y2: return True
        # 板框检查
        bm = mm(2)
        for v in [x1,x2]:
            if v < mm(BL)+bm or v > mm(BR)-bm: return False
        for v in [y1,y2]:
            if v < mm(BT)+bm or v > mm(BB)-bm: return False
        
        ln = 'F' if layer == self.FCU else 'B'
        
        # B.Cu: 检查是否穿过ESP32禁区
        if ln == 'B' and self._line_crosses_esp(x1, y1, x2, y2):
            return False
        
        if check:
            # 两层都检查交叉和焊盘冲突
            for tx1,ty1,tx2,ty2,tn in self.tracks[ln]:
                if tn == net_name: continue
                if self._segs_cross(x1,y1,x2,y2, tx1,ty1,tx2,ty2):
                    return False
            if self._path_hits_pad(x1,y1,x2,y2, net_name, mm(0.8)):
                return False
        
        t = pcbnew.PCB_TRACK(self.board)
        t.SetStart(pcbnew.VECTOR2I(int(x1),int(y1)))
        t.SetEnd(pcbnew.VECTOR2I(int(x2),int(y2)))
        t.SetWidth(w); t.SetLayer(layer); t.SetNet(net_obj)
        self.board.Add(t)
        self.tracks[ln].append((x1,y1,x2,y2,net_name))
        self.stats['trk'] += 1
        return True
    
    def _add_via(self, x, y, net_obj, net_name):
        # 不能在ESP32禁区内
        if self._in_esp_zone(x, y):
            return False
        # 板框
        bm = mm(4)
        if x<mm(BL)+bm or x>mm(BR)-bm or y<mm(BT)+bm or y>mm(BB)-bm:
            return False
        # 离ALL焊盘(包括同网络) - 避免holes_co_located
        for p in self.all_pads:
            d = math.sqrt((x-p['x'])**2+(y-p['y'])**2)
            if d < mm(0.8): return False  # 离任何焊盘至少0.8mm
            if p['net'] != net_name and p['net'] != '' and p['net'] != 'GND':
                if d < mm(1.2): return False  # 离非同网焊盘1.2mm
        # 离已有via
        for vx,vy in self.vias:
            if math.sqrt((x-vx)**2+(y-vy)**2) < mm(1.0): return False
        
        v = pcbnew.PCB_VIA(self.board)
        v.SetPosition(pcbnew.VECTOR2I(int(x),int(y)))
        v.SetWidth(mm(0.8)); v.SetDrill(mm(0.4))
        v.SetNet(net_obj); v.SetLayerPair(self.FCU, self.BCU)
        self.board.Add(v)
        self.vias.add((x,y))
        self.stats['via'] += 1
        return True
    
    def _find_safe_via(self, cx, cy, net_name):
        for r in [0, mm(2), mm(3), mm(4), mm(5), mm(6), mm(8)]:
            if r == 0:
                candidates = [(cx, cy)]
            else:
                candidates = []
                for a in range(0, 360, 20):
                    nx = int(cx + r*math.cos(math.radians(a)))
                    ny = int(cy + r*math.sin(math.radians(a)))
                    candidates.append((nx, ny))
            for nx, ny in candidates:
                if self._in_esp_zone(nx, ny): continue
                bm = mm(4)
                if nx<mm(BL)+bm or nx>mm(BR)-bm or ny<mm(BT)+bm or ny>mm(BB)-bm:
                    continue
                safe = True
                # 检查所有焊盘
                for p in self.all_pads:
                    d = math.sqrt((nx-p['x'])**2+(ny-p['y'])**2)
                    if d < mm(0.8):  # 太近
                        safe = False; break
                    if p['net'] != net_name and p['net'] != '' and p['net'] != 'GND':
                        if d < mm(1.2):
                            safe = False; break
                if not safe: continue
                # 检查已有via
                for vx,vy in self.vias:
                    if math.sqrt((nx-vx)**2+(ny-vy)**2) < mm(1.0):
                        safe = False; break
                if safe:
                    return (nx, ny)
        return (cx, cy)
    
    def _path_hits_pad(self, x1, y1, x2, y2, net_name, clearance):
        dx=x2-x1; dy=y2-y1
        dist=math.sqrt(dx*dx+dy*dy)
        if dist < 1: return False
        steps = max(int(dist/mm(1.0)), 5)
        for i in range(1, steps):
            t = i/steps
            px=int(x1+dx*t); py=int(y1+dy*t)
            for p in self.all_pads:
                if p['net']==net_name or p['net']=='' or p['net']=='GND': continue
                if abs(px-p['x'])+abs(py-p['y']) < clearance:
                    return True
        return False
    
    def _route_around_esp(self, x1, y1, x2, y2, w, layer, net_obj, net_name):
        """B.Cu绕行ESP32: 走上/下/左/右通道"""
        fx1, fy1 = mm(ESP_FORBID_X1-3), mm(ESP_FORBID_Y1-3)
        fx2, fy2 = mm(ESP_FORBID_X2+3), mm(ESP_FORBID_Y2+3)
        
        # 添加偏移量避免多条绕行线重叠
        offset = mm(len(self.tracks['B']) % 5) * mm(0.5) 
        
        routes = []
        # 上绕
        routes.append(('up', [
            (x1, y1, x1, fy1-offset),
            (x1, fy1-offset, x2, fy1-offset),
            (x2, fy1-offset, x2, y2)
        ]))
        # 下绕
        routes.append(('down', [
            (x1, y1, x1, fy2+offset),
            (x1, fy2+offset, x2, fy2+offset),
            (x2, fy2+offset, x2, y2)
        ]))
        # 左绕
        routes.append(('left', [
            (x1, y1, fx1-offset, y1),
            (fx1-offset, y1, fx1-offset, y2),
            (fx1-offset, y2, x2, y2)
        ]))
        # 右绕
        routes.append(('right', [
            (x1, y1, fx2+offset, y1),
            (fx2+offset, y1, fx2+offset, y2),
            (fx2+offset, y2, x2, y2)
        ]))
        
        # 计算每条路径长度
        def path_len(r):
            return sum(math.sqrt((b-a)**2+(d-c)**2) for a,b,c,d in r[1])
        routes.sort(key=path_len)
        
        # 先尝试safe
        for name, segs in routes:
            ok = True
            for sx1,sy1,sx2,sy2 in segs:
                if not self._add_track(sx1,sy1,sx2,sy2,w,layer,net_obj,net_name):
                    ok = False; break
            if ok: return True
        
        # safe失败 → 强制最短路径(不检查交叉但仍避开ESP32)
        for name, segs in routes:
            all_ok = True
            for sx1,sy1,sx2,sy2 in segs:
                if self._line_crosses_esp(sx1,sy1,sx2,sy2):
                    all_ok = False; break
            if all_ok:
                for sx1,sy1,sx2,sy2 in segs:
                    self._add_track(sx1,sy1,sx2,sy2,w,layer,net_obj,net_name,check=False)
                return True
        
        # 最终fallback: 强制走F.Cu
        self._add_track(x1,y1,x2,y2,w,self.FCU,net_obj,net_name,check=False)
        return False
    
    def _connect(self, p1, p2, net_name, net_obj, w):
        sx,sy = p1['x'],p1['y']
        ex,ey = p2['x'],p2['y']
        dist = math.sqrt((ex-sx)**2+(ey-sy)**2)
        
        p1f = p1['on_f'] or p1['is_th']
        p2f = p2['on_f'] or p2['is_th']
        p1b = p1['on_b'] or p1['is_th']
        p2b = p2['on_b'] or p2['is_th']
        
        # ===== F.Cu短距直连(<8mm) =====
        if dist < mm(8) and p1f and p2f:
            if self._add_track(sx,sy,ex,ey,w,self.FCU,net_obj,net_name):
                return
        
        # ===== B.Cu直连(不穿ESP32) =====
        if p1b and p2b:
            if not self._line_crosses_esp(sx,sy,ex,ey):
                if self._add_track(sx,sy,ex,ey,w,self.BCU,net_obj,net_name):
                    return
            # L型: 多种偏移量
            for offset in [0, mm(3), mm(-3), mm(5), mm(-5), mm(8), mm(-8)]:
                mx = (sx+ex)//2 + offset
                # L型方案A: 水平→垂直
                if not self._line_crosses_esp(sx,sy,mx,sy) and not self._line_crosses_esp(mx,sy,mx,ey) and not self._line_crosses_esp(mx,ey,ex,ey):
                    if self._add_track(sx,sy,mx,sy,w,self.BCU,net_obj,net_name) and \
                       self._add_track(mx,sy,mx,ey,w,self.BCU,net_obj,net_name) and \
                       self._add_track(mx,ey,ex,ey,w,self.BCU,net_obj,net_name):
                        return
                my = (sy+ey)//2 + offset
                # L型方案B: 垂直→水平  
                if not self._line_crosses_esp(sx,sy,sx,my) and not self._line_crosses_esp(sx,my,ex,my) and not self._line_crosses_esp(ex,my,ex,ey):
                    if self._add_track(sx,sy,sx,my,w,self.BCU,net_obj,net_name) and \
                       self._add_track(sx,my,ex,my,w,self.BCU,net_obj,net_name) and \
                       self._add_track(ex,my,ex,ey,w,self.BCU,net_obj,net_name):
                        return
        
        # ===== 需要绕行ESP32 =====
        # F.Cu SMD → via → B.Cu绕行 → via → F.Cu SMD
        if p1f and p2f:
            v1x,v1y = self._find_safe_via(sx, sy, net_name)
            v2x,v2y = self._find_safe_via(ex, ey, net_name)
            
            ok1 = self._add_via(v1x,v1y,net_obj,net_name)
            ok2 = self._add_via(v2x,v2y,net_obj,net_name)
            
            if ok1 and ok2:
                # 完整via桥
                self._add_track(sx,sy,v1x,v1y,w,self.FCU,net_obj,net_name,check=False)
                self._add_track(v2x,v2y,ex,ey,w,self.FCU,net_obj,net_name,check=False)
                if self._line_crosses_esp(v1x,v1y,v2x,v2y):
                    self._route_around_esp(v1x,v1y,v2x,v2y,w,self.BCU,net_obj,net_name)
                else:
                    if not self._add_track(v1x,v1y,v2x,v2y,w,self.BCU,net_obj,net_name):
                        if not (self._add_track(v1x,v1y,v2x,v1y,w,self.BCU,net_obj,net_name) and
                                self._add_track(v2x,v1y,v2x,v2y,w,self.BCU,net_obj,net_name)):
                            self._add_track(v1x,v1y,v2x,v2y,w,self.BCU,net_obj,net_name,check=False)
            elif ok1 and not ok2:
                # 只有via1 → via1到目标走B.Cu
                self._add_track(sx,sy,v1x,v1y,w,self.FCU,net_obj,net_name,check=False)
                if self._line_crosses_esp(v1x,v1y,ex,ey):
                    self._route_around_esp(v1x,v1y,ex,ey,w,self.BCU,net_obj,net_name)
                else:
                    self._add_track(v1x,v1y,ex,ey,w,self.BCU,net_obj,net_name,check=False)
            elif not ok1 and ok2:
                self._add_track(v2x,v2y,ex,ey,w,self.FCU,net_obj,net_name,check=False)
                if self._line_crosses_esp(sx,sy,v2x,v2y):
                    self._route_around_esp(sx,sy,v2x,v2y,w,self.BCU,net_obj,net_name)
                else:
                    self._add_track(sx,sy,v2x,v2y,w,self.BCU,net_obj,net_name,check=False)
            else:
                # F.Cu直连
                self._add_track(sx,sy,ex,ey,w,self.FCU,net_obj,net_name,check=False)
            return
        
        # 通孔+通孔: B.Cu(可能绕行)
        if p1['is_th'] and p2['is_th']:
            if self._line_crosses_esp(sx,sy,ex,ey):
                self._route_around_esp(sx,sy,ex,ey,w,self.BCU,net_obj,net_name)
            else:
                if not self._add_track(sx,sy,ex,ey,w,self.BCU,net_obj,net_name):
                    if not (self._add_track(sx,sy,ex,sy,w,self.BCU,net_obj,net_name) and
                            self._add_track(ex,sy,ex,ey,w,self.BCU,net_obj,net_name)):
                        self._add_track(sx,sy,ex,ey,w,self.BCU,net_obj,net_name,check=False)
            return
        
        # 跨层
        if p1f and p2b:
            vx,vy = self._find_safe_via(sx, sy, net_name)
            ok = self._add_via(vx,vy,net_obj,net_name)
            if ok:
                self._add_track(sx,sy,vx,vy,w,self.FCU,net_obj,net_name,check=False)
                if self._line_crosses_esp(vx,vy,ex,ey):
                    self._route_around_esp(vx,vy,ex,ey,w,self.BCU,net_obj,net_name)
                else:
                    self._add_track(vx,vy,ex,ey,w,self.BCU,net_obj,net_name,check=False)
            else:
                self._add_track(sx,sy,ex,ey,w,self.FCU,net_obj,net_name,check=False)
            return
        
        if p1b and p2f:
            vx,vy = self._find_safe_via(ex, ey, net_name)
            ok = self._add_via(vx,vy,net_obj,net_name)
            if ok:
                if self._line_crosses_esp(sx,sy,vx,vy):
                    self._route_around_esp(sx,sy,vx,vy,w,self.BCU,net_obj,net_name)
                else:
                    self._add_track(sx,sy,vx,vy,w,self.BCU,net_obj,net_name,check=False)
                self._add_track(vx,vy,ex,ey,w,self.FCU,net_obj,net_name,check=False)
            else:
                self._add_track(sx,sy,ex,ey,w,self.BCU,net_obj,net_name,check=False)
            return
        
        # 默认
        self._add_track(sx,sy,ex,ey,w,self.FCU,net_obj,net_name,check=False)
    
    def route_all(self):
        print("[布线] 开始...")
        self.collect_pads()
        self.clear_routes()
        
        signal_nets = {k:v for k,v in self.net_pads.items() if len(v)>=2 and k!='GND'}
        
        def prio(n):
            if n in ['3V3','BAT','5V']: return 1
            nl = n.lower()
            if 'spi' in nl or 'cs' in nl or 'mosi' in nl or 'miso' in nl or 'sck' in nl: return 2
            if 'i2c' in nl or 'sda' in nl or 'scl' in nl: return 3
            if 'i2s' in nl: return 4
            if 'uart' in nl: return 5
            if 'lcd' in nl or 'led' in nl: return 6
            return 7
        
        def wid(n):
            return 0.5 if n in ['3V3','BAT','5V'] else 0.25
        
        sorted_nets = sorted(signal_nets.items(), key=lambda x: prio(x[0]))
        
        for net_name, pads in sorted_nets:
            net_obj = self.board.FindNet(net_name)
            if not net_obj: continue
            w = mm(wid(net_name))
            
            # MST
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
        
        print(f"  OK: {len(sorted_nets)} 网络, "
              f"走线 {self.stats['trk']}, 过孔 {self.stats['via']}")


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
    
    print(f"\n  === DRC结果 ===")
    print(f"  未连接:      {len(unc)}")
    print(f"  总违规:      {len(viol)}")
    print(f"    固定(非布线): {nfix}")
    print(f"    布线相关:     {nrout}")
    print(f"      短路:  {vtypes.get('shorting_items',0)}")
    print(f"      交叉:  {vtypes.get('tracks_crossing',0)}")
    print(f"      间距:  {vtypes.get('clearance',0)}")
    print(f"      孔距:  {vtypes.get('hole_clearance',0)}")
    print(f"      不允许: {vtypes.get('items_not_allowed',0)}")
    print(f"  详细:")
    for t,c in sorted(vtypes.items(), key=lambda x:x[1], reverse=True):
        print(f"    {t:35s}: {c}")
    return vtypes


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    
    pcb = r'D:\thinkpad\Documents\cybewand_insta360\cybewand_insta360.kicad_pcb'
    drc = r'd:\win_workspace\CyberWand_Insta360\schematic\skidl\docs\DRC_v3.json'
    
    print("=" * 60)
    print("CyberWand PCB v3 - 避开ESP32 GND焊盘")
    print("=" * 60)
    
    board = pcbnew.LoadBoard(pcb)
    print(f"[OK] 加载PCB")
    
    set_board_outline(board)
    apply_layout(board)
    set_zones(board)
    
    router = SafeRouter(board)
    router.route_all()
    
    print("[铜箔] 填充...")
    zones = board.Zones()
    if len(zones) > 0:
        filler = pcbnew.ZONE_FILLER(board)
        filler.Fill(zones)
    
    pcbnew.SaveBoard(pcb, board)
    print(f"[OK] 保存")
    
    print("\n[DRC] 检查...")
    if run_drc(pcb, drc):
        print_drc(drc)
    else:
        print("  DRC失败")
    
    print("\n" + "=" * 60)


if __name__ == '__main__':
    main()
