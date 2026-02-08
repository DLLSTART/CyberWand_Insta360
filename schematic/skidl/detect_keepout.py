"""检测ESP32 keepout区域和courtyard"""
import pcbnew, sys
sys.stdout.reconfigure(encoding='utf-8')

def to_mm(v): return v / 1000000

board = pcbnew.LoadBoard(r'D:\thinkpad\Documents\cybewand_insta360\cybewand_insta360.kicad_pcb')

# 检查所有zone
print("=== ZONES ===")
for z in board.Zones():
    is_rule = z.GetIsRuleArea()
    net = z.GetNet().GetNetname() if z.GetNet() else 'N/A'
    layer = board.GetLayerName(z.GetLayer())
    bb = z.GetBoundingBox()
    print(f"  RuleArea={is_rule}, net={net}, layer={layer}, "
          f"bbox=({to_mm(bb.GetLeft()):.1f},{to_mm(bb.GetTop()):.1f})-"
          f"({to_mm(bb.GetRight()):.1f},{to_mm(bb.GetBottom()):.1f})")
    if is_rule:
        print(f"    NoTracks={z.GetDoNotAllowTracks()}, NoVias={z.GetDoNotAllowVias()}")

# 检查ESP32封装
print("\n=== ESP32 (U1) ===")
fps = board.GetFootprints()
for i in range(len(fps)):
    fp = fps[i]
    ref = fp.GetReference()
    if ref == 'U1':
        pos = fp.GetPosition()
        bb = fp.GetBoundingBox()
        print(f"  pos: ({to_mm(pos.x):.1f}, {to_mm(pos.y):.1f})")
        print(f"  bbox: ({to_mm(bb.GetLeft()):.1f},{to_mm(bb.GetTop()):.1f})-"
              f"({to_mm(bb.GetRight()):.1f},{to_mm(bb.GetBottom()):.1f})")
        # 检查封装内部的区域
        for z in fp.Zones():
            is_rule = z.GetIsRuleArea()
            layer = board.GetLayerName(z.GetLayer())
            zbb = z.GetBoundingBox()
            print(f"  FP Zone: RuleArea={is_rule}, layer={layer}, "
                  f"bbox=({to_mm(zbb.GetLeft()):.1f},{to_mm(zbb.GetTop()):.1f})-"
                  f"({to_mm(zbb.GetRight()):.1f},{to_mm(zbb.GetBottom()):.1f})")
        # Courtyard
        cy = fp.GetCourtyard(0)  # F.Cu courtyard
        if cy and cy.OutlineCount() > 0:
            bb2 = cy.BBox()
            print(f"  Courtyard F: ({to_mm(bb2.GetLeft()):.1f},{to_mm(bb2.GetTop()):.1f})-"
                  f"({to_mm(bb2.GetRight()):.1f},{to_mm(bb2.GetBottom()):.1f})")

# 检查courtyard overlapping components
print("\n=== COURTYARD OVERLAPS ===")
for i in range(len(fps)):
    fp = fps[i]
    ref = fp.GetReference()
    if ref in ['C1','C2','C3','R1','C5','C6','D5','R9']:
        pos = fp.GetPosition()
        bb = fp.GetBoundingBox()
        print(f"  {ref:6s}: pos=({to_mm(pos.x):.1f},{to_mm(pos.y):.1f}), "
              f"bbox=({to_mm(bb.GetLeft()):.1f},{to_mm(bb.GetTop()):.1f})-"
              f"({to_mm(bb.GetRight()):.1f},{to_mm(bb.GetBottom()):.1f})")
