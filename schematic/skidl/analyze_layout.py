"""分析当前PCB布局"""
import pcbnew, sys, math
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')
board = pcbnew.LoadBoard(r'D:\thinkpad\Documents\cybewand_insta360\cybewand_insta360.kicad_pcb')

def to_mm(v): return v / 1000000

# 板框
print("=== 板框 ===")
for d in board.GetDrawings():
    if d.GetLayer() == board.GetLayerID('Edge.Cuts'):
        bb = d.GetBoundingBox()
        print(f"  板框BB: ({to_mm(bb.GetLeft()):.1f}, {to_mm(bb.GetTop()):.1f}) - ({to_mm(bb.GetRight()):.1f}, {to_mm(bb.GetBottom()):.1f})")
        print(f"  尺寸: {to_mm(bb.GetWidth()):.1f} x {to_mm(bb.GetHeight()):.1f} mm")

# 元件位置
print("\n=== 元件位置 ===")
fps = board.GetFootprints()
components = []
for i in range(len(fps)):
    fp = fps[i]
    ref = fp.GetReference()
    val = fp.GetValue()
    pos = fp.GetPosition()
    rot = fp.GetOrientationDegrees()
    bb = fp.GetBoundingBox()
    w = to_mm(bb.GetWidth())
    h = to_mm(bb.GetHeight())
    layer = 'F' if fp.GetLayer() == board.GetLayerID('F.Cu') else 'B'
    
    components.append({
        'ref': ref, 'val': val,
        'x': to_mm(pos.x), 'y': to_mm(pos.y),
        'rot': rot, 'w': w, 'h': h, 'layer': layer
    })
    print(f"  {ref:6s} {val:25s} ({to_mm(pos.x):7.2f}, {to_mm(pos.y):7.2f}) rot={rot:6.1f} {w:.1f}x{h:.1f}mm [{layer}]")

# 分析间距问题
print("\n=== 间距过近的元件对 ===")
for i in range(len(components)):
    for j in range(i+1, len(components)):
        a = components[i]
        b = components[j]
        dx = abs(a['x'] - b['x'])
        dy = abs(a['y'] - b['y'])
        center_dist = math.sqrt(dx*dx + dy*dy)
        min_dist = (max(a['w'], a['h']) + max(b['w'], b['h'])) / 2
        
        if center_dist < min_dist * 0.8:  # 重叠或太近
            print(f"  [!] {a['ref']:6s} <-> {b['ref']:6s}: 中心距{center_dist:.1f}mm, 最小需要{min_dist:.1f}mm")

# 网络连接信息
print("\n=== 网络焊盘分布 ===")
net_pads = defaultdict(list)
for i in range(len(fps)):
    fp = fps[i]
    ref = fp.GetReference()
    pads = fp.Pads()
    for j in range(len(pads)):
        pad = pads[j]
        net = pad.GetNetname()
        if net:
            net_pads[net].append(ref)

for net in sorted(net_pads.keys()):
    refs = list(set(net_pads[net]))
    if len(refs) >= 2:
        print(f"  {net:25s}: {', '.join(sorted(refs))}")
