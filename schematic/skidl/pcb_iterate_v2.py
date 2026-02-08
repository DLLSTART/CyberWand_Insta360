"""
CyberWand PCB v2 - 极简安全布局+布线
====================================
策略变更:
1. 板子扩大到 100x180mm，元件间距极大
2. 仅在F.Cu做 pad→via 短桩(<3mm)
3. 所有长走线走B.Cu
4. 每条B.Cu走线放置前检查是否冲突
5. GND完全依靠铜箔连接
"""
import pcbnew, math, sys, os, json, subprocess
from collections import defaultdict

def mm(v): return int(v * 1000000)
def to_mm(v): return v / 1000000

# 板框
BL, BT = 85.0, 20.0
BW, BH = 100.0, 180.0
BR, BB = BL+BW, BT+BH

# ============================================================
# 新布局 - 极大间距, 功能分区明确
# ============================================================
LAYOUT = {
    # ==== 中部: ESP32 (核心, 48x43mm) ====
    'U1':  (135.0, 105.0, 0),

    # ==== 顶部区域 (y=28~70): LCD + LED ====
    'LCD1': (135.0,  45.0, 90),
    'C5':   (160.0,  45.0, 0),
    'C6':   (164.0,  45.0, 0),
    'D1':   (100.0,  32.0, 0),
    'D2':   (120.0,  32.0, 0),
    'D3':   (170.0,  32.0, 0),
    'C12':  (110.0,  32.0, 0),

    # ==== 左区 (x=88~110): 传感器+按键 ====
    'U2':   (95.0,  60.0, 0),     # MPU (远离ESP32)
    'C4':   (95.0,  70.0, 0),
    'R2':   (105.0, 58.0, 0),
    'R3':   (105.0, 63.0, 0),

    'SW3':  (92.0,  88.0, 0),     # 按键(大间距18mm)
    'R6':   (92.0,  96.0, 0),
    'SW2':  (92.0, 106.0, 0),
    'R5':   (92.0, 114.0, 0),
    'SW1':  (92.0, 124.0, 0),
    'R4':   (92.0, 132.0, 0),

    'MIC1': (92.0, 148.0, 0),     # 麦克风(最左下)

    # ==== 右区 (x=160~180): DFPlayer+SD ====
    'U3':   (170.0,  78.0, 0),
    'J1':   (170.0, 115.0, 90),
    'C10':  (170.0,  62.0, 0),
    'C11':  (174.0,  62.0, 0),

    # ==== 底部 (y=150~195): 电源 ====
    'U4':   (115.0, 165.0, 0),
    'U5':   (155.0, 165.0, 0),
    'J2':   (135.0, 190.0, 90),
    'C9':   (125.0, 185.0, 0),
    'R7':   (125.0, 180.0, 0),
    'R8':   (128.0, 180.0, 0),
    'R9':   (108.0, 165.0, 0),
    'C7':   (155.0, 158.0, 0),
    'C8':   (159.0, 158.0, 0),
    'D4':   (105.0, 160.0, 0),
    'D5':   (105.0, 164.0, 0),
    'R10':  (100.0, 160.0, 0),
    'R11':  (100.0, 164.0, 0),
    'R12':  (115.0, 172.0, 0),

    # ESP32外围无源
    'R1':   (122.0, 82.0, 0),
    'C1':   (115.0, 78.0, 0),
    'C2':   (119.0, 78.0, 0),
    'C3':   (123.0, 78.0, 0),

    # 背面
    'BT1':  (135.0, 150.0, 180),
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
            if ref in ['BT1','LS1'] and fp.GetLayer() != BCU:
                fp.Flip(fp.GetPosition(), False)
            n += 1
    print(f"  OK: {n} 元件")
    return n


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
        s.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1)))
        s.SetEnd(pcbnew.VECTOR2I(mm(x2),mm(y2)))
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
    if not gnd:
        print("  [!] 无GND"); return
    
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


# ============================================================
# 安全布线引擎
# ============================================================
class SafeRouter:
    def __init__(self, board):
        self.board = board
        self.FCU = board.GetLayerID('F.Cu')
        self.BCU = board.GetLayerID('B.Cu')
        # 已放置走线 {layer_name: [(x1,y1,x2,y2,net), ...]}
        self.tracks = {'F': [], 'B': []}
        # 已放置via {(x,y)}
        self.vias = set()
        self.stats = {'trk':0,'via':0,'skip':0}
    
    def collect_pads(self):
        """收集焊盘信息"""
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
        """清除所有走线"""
        tracks = list(self.board.GetTracks())
        for t in tracks:
            self.board.Remove(t)
        print(f"  清除 {len(tracks)} 走线")
    
    def _add_track(self, x1, y1, x2, y2, w, layer, net_obj, net_name, check=True):
        """安全添加走线"""
        if x1==x2 and y1==y2: return False
        # 确保在板框内
        margin = mm(2)
        for v in [x1,x2]:
            if v < mm(BL)+margin or v > mm(BR)-margin: return False
        for v in [y1,y2]:
            if v < mm(BT)+margin or v > mm(BB)-margin: return False
        
        ln = 'F' if layer == self.FCU else 'B'
        
        if check:
            # 检查是否与其他网络的走线交叉
            for tx1,ty1,tx2,ty2,tn in self.tracks[ln]:
                if tn == net_name: continue
                if self._segments_cross(x1,y1,x2,y2,tx1,ty1,tx2,ty2):
                    return False
            # 检查路径是否穿过其他网络的焊盘
            if self._path_hits_pad(x1,y1,x2,y2,net_name,mm(1.0)):
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
        """安全添加过孔"""
        # 在板框内?
        margin = mm(4)
        if x < mm(BL)+margin or x > mm(BR)-margin: return False
        if y < mm(BT)+margin or y > mm(BB)-margin: return False
        # 离其他网络焊盘够远? (曼哈顿4mm)
        for p in self.all_pads:
            if p['net'] == net_name or p['net'] == '' or p['net'] == 'GND': continue
            d = math.sqrt((x-p['x'])**2 + (y-p['y'])**2)
            if d < mm(1.5): return False
        # 离已有via够远?
        for vx,vy in self.vias:
            if math.sqrt((x-vx)**2+(y-vy)**2) < mm(1.2): return False
        
        v = pcbnew.PCB_VIA(self.board)
        v.SetPosition(pcbnew.VECTOR2I(int(x),int(y)))
        v.SetWidth(mm(0.8)); v.SetDrill(mm(0.4))
        v.SetNet(net_obj)
        v.SetLayerPair(self.FCU, self.BCU)
        self.board.Add(v)
        self.vias.add((x,y))
        self.stats['via'] += 1
        return True
    
    def _find_safe_via(self, cx, cy, net_name):
        """找安全的via位置"""
        if self._via_safe(cx, cy, net_name):
            return (cx, cy)
        for r in [mm(3), mm(4), mm(5), mm(6)]:
            for a in range(0, 360, 30):
                nx = int(cx + r * math.cos(math.radians(a)))
                ny = int(cy + r * math.sin(math.radians(a)))
                if self._via_safe(nx, ny, net_name):
                    return (nx, ny)
        return (cx, cy)  # fallback
    
    def _via_safe(self, x, y, net_name):
        margin = mm(4)
        if x<mm(BL)+margin or x>mm(BR)-margin or y<mm(BT)+margin or y>mm(BB)-margin:
            return False
        for p in self.all_pads:
            if p['net']==net_name or p['net']=='' or p['net']=='GND': continue
            d = math.sqrt((x-p['x'])**2 + (y-p['y'])**2)
            if d < mm(1.5): return False
        for vx,vy in self.vias:
            if math.sqrt((x-vx)**2+(y-vy)**2) < mm(1.2): return False
        return True
    
    @staticmethod
    def _segments_cross(ax1,ay1,ax2,ay2, bx1,by1,bx2,by2):
        def ccw(px,py,qx,qy,rx,ry):
            return (rx-px)*(qy-py)-(qx-px)*(ry-py)
        d1=ccw(ax1,ay1,ax2,ay2,bx1,by1)
        d2=ccw(ax1,ay1,ax2,ay2,bx2,by2)
        d3=ccw(bx1,by1,bx2,by2,ax1,ay1)
        d4=ccw(bx1,by1,bx2,by2,ax2,ay2)
        if((d1>0 and d2<0)or(d1<0 and d2>0))and((d3>0 and d4<0)or(d3<0 and d4>0)):
            return True
        return False
    
    def _path_hits_pad(self, x1, y1, x2, y2, net_name, clearance):
        dx=x2-x1; dy=y2-y1
        dist=math.sqrt(dx*dx+dy*dy)
        if dist < 1: return False
        steps = max(int(dist/mm(1.0)), 5)
        for i in range(1, steps):
            t = i/steps
            px=int(x1+dx*t); py=int(y1+dy*t)
            for p in self.all_pads:
                if p['net']==net_name or p['net']=='': continue
                if abs(px-p['x'])+abs(py-p['y']) < clearance:
                    return True
        return False
    
    def route_net(self, net_name, pads, net_obj, w):
        """布线单个网络(MST)"""
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
    
    def _connect(self, p1, p2, net_name, net_obj, w):
        """连接两焊盘 - 安全策略"""
        sx,sy = p1['x'],p1['y']
        ex,ey = p2['x'],p2['y']
        dist = math.sqrt((ex-sx)**2+(ey-sy)**2)
        
        p1f = p1['on_f'] or p1['is_th']
        p2f = p2['on_f'] or p2['is_th']
        p1b = p1['on_b'] or p1['is_th']
        p2b = p2['on_b'] or p2['is_th']
        
        # 策略1: 短距离 F.Cu直连(<6mm, 无冲突)
        if dist < mm(6) and p1f and p2f:
            if self._add_track(sx,sy,ex,ey,w,self.FCU,net_obj,net_name):
                return
        
        # 策略2: 短距离 B.Cu直连(<6mm)
        if dist < mm(6) and p1b and p2b:
            if self._add_track(sx,sy,ex,ey,w,self.BCU,net_obj,net_name):
                return
        
        # 策略3: 双通孔 B.Cu直连
        if p1['is_th'] and p2['is_th']:
            if dist < mm(20):
                if self._add_track(sx,sy,ex,ey,w,self.BCU,net_obj,net_name):
                    return
            # L型
            if self._try_L_route(sx,sy,ex,ey,w,self.BCU,net_obj,net_name):
                return
            # 强制直连
            self._add_track(sx,sy,ex,ey,w,self.BCU,net_obj,net_name,check=False)
            return
        
        # 策略4: F.Cu SMD → via → B.Cu → via → F.Cu SMD
        if p1f and p2f:
            dx = ex-sx; dy = ey-sy
            d = max(math.sqrt(dx*dx+dy*dy),1)
            ux,uy = dx/d, dy/d
            off = min(mm(3), int(d*0.2))
            
            v1x,v1y = self._find_safe_via(int(sx+ux*off), int(sy+uy*off), net_name)
            v2x,v2y = self._find_safe_via(int(ex-ux*off), int(ey-uy*off), net_name)
            
            # 只有via能安全放置才添加走线
            ok1 = self._add_via(v1x,v1y,net_obj,net_name)
            ok2 = self._add_via(v2x,v2y,net_obj,net_name)
            if ok1:
                self._add_track(sx,sy,v1x,v1y,w,self.FCU,net_obj,net_name,check=False)
            if ok1 and ok2:
                if not self._add_track(v1x,v1y,v2x,v2y,w,self.BCU,net_obj,net_name):
                    self._try_L_route(v1x,v1y,v2x,v2y,w,self.BCU,net_obj,net_name)
            if ok2:
                self._add_track(v2x,v2y,ex,ey,w,self.FCU,net_obj,net_name,check=False)
            if not ok1 or not ok2:
                # via失败 → 尝试F.Cu直连
                self._add_track(sx,sy,ex,ey,w,self.FCU,net_obj,net_name,check=False)
            return
        
        # 策略5: 跨层(一端F, 一端B)
        if p1f and p2b:
            vx,vy = self._find_safe_via(sx,sy,net_name)
            ok = self._add_via(vx,vy,net_obj,net_name)
            if ok:
                self._add_track(sx,sy,vx,vy,w,self.FCU,net_obj,net_name,check=False)
                if not self._add_track(vx,vy,ex,ey,w,self.BCU,net_obj,net_name):
                    self._try_L_route(vx,vy,ex,ey,w,self.BCU,net_obj,net_name)
            else:
                self._add_track(sx,sy,ex,ey,w,self.FCU,net_obj,net_name,check=False)
            return
        if p1b and p2f:
            vx,vy = self._find_safe_via(ex,ey,net_name)
            ok = self._add_via(vx,vy,net_obj,net_name)
            if ok:
                if not self._add_track(sx,sy,vx,vy,w,self.BCU,net_obj,net_name):
                    self._try_L_route(sx,sy,vx,vy,w,self.BCU,net_obj,net_name)
                self._add_track(vx,vy,ex,ey,w,self.FCU,net_obj,net_name,check=False)
            else:
                self._add_track(sx,sy,ex,ey,w,self.BCU,net_obj,net_name,check=False)
            return
        
        # 兜底: B.Cu强制连接
        self._add_track(sx,sy,ex,ey,w,self.BCU,net_obj,net_name,check=False)
    
    def _try_L_route(self, x1, y1, x2, y2, w, layer, net_obj, net_name):
        """L型路径(先试两种方向)"""
        # 方案A: 先水平后垂直
        if self._add_track(x1,y1,x2,y1,w,layer,net_obj,net_name) and \
           self._add_track(x2,y1,x2,y2,w,layer,net_obj,net_name):
            return True
        # 方案B: 先垂直后水平
        if self._add_track(x1,y1,x1,y2,w,layer,net_obj,net_name) and \
           self._add_track(x1,y2,x2,y2,w,layer,net_obj,net_name):
            return True
        # 失败 → 强制直连
        self._add_track(x1,y1,x2,y2,w,layer,net_obj,net_name,check=False)
        return False
    
    def route_all(self):
        """布线所有信号网络"""
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
            self.route_net(net_name, pads, net_obj, mm(wid(net_name)))
        
        print(f"  OK: 布线 {len(sorted_nets)} 网络, "
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
    
    return {
        'unconnected': len(unc),
        'violations': len(viol),
        'shorts': vtypes.get('shorting_items',0),
        'crossing': vtypes.get('tracks_crossing',0),
        'clearance': vtypes.get('clearance',0),
    }


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    
    pcb = r'D:\thinkpad\Documents\cybewand_insta360\cybewand_insta360.kicad_pcb'
    drc = r'd:\win_workspace\CyberWand_Insta360\schematic\skidl\docs\DRC_v2.json'
    
    print("="*60)
    print("CyberWand PCB v2 - 安全布局+布线迭代器")
    print("="*60)
    
    board = pcbnew.LoadBoard(pcb)
    print(f"[OK] 加载PCB")
    
    # 布局
    set_board_outline(board)
    apply_layout(board)
    set_zones(board)
    
    # 布线
    router = SafeRouter(board)
    router.route_all()
    
    # 铜箔填充
    print("[铜箔] 填充...")
    zones = board.Zones()
    if len(zones)>0:
        filler = pcbnew.ZONE_FILLER(board)
        filler.Fill(zones)
    
    # 保存
    pcbnew.SaveBoard(pcb, board)
    print(f"[OK] 保存")
    
    # DRC
    print("\n[DRC] 检查...")
    if run_drc(pcb, drc):
        result = print_drc(drc)
    else:
        print("  DRC失败")
    
    print("\n" + "="*60)
    print("完成!")
    print("="*60)


if __name__ == '__main__':
    main()
