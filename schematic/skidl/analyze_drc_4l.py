"""分析4层PCB的DRC结果"""
import json, sys
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')

with open(r'd:\win_workspace\CyberWand_Insta360\schematic\skidl\docs\DRC_4layer.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

viol = data.get('violations', [])
unc = data.get('unconnected_items', [])

# 1. 短路分析
shorts = [v for v in viol if v.get('type') == 'shorting_items']
print(f"=== 短路 ({len(shorts)}) ===")
net_pairs = defaultdict(int)
for v in shorts:
    items = v.get('items', [])
    nets = set()
    for it in items:
        desc = it.get('description', '')
        if '/Net-(' in desc or 'Net ' in desc:
            # Try to extract net name
            pass
        # Check for net in pos
        pos = it.get('pos', {})
    # Simpler: extract from description
    desc = v.get('description', '')
    net_pairs[desc[:80]] += 1

for d, c in sorted(net_pairs.items(), key=lambda x: x[1], reverse=True)[:15]:
    print(f"  {c:3d}x  {d}")

# 2. track_dangling分析
dangling = [v for v in viol if v.get('type') == 'track_dangling']
print(f"\n=== 悬空走线 ({len(dangling)}) ===")
layers = defaultdict(int)
for v in dangling:
    for it in v.get('items', []):
        desc = it.get('description', '')
        if 'F.Cu' in desc: layers['F.Cu'] += 1
        elif 'B.Cu' in desc: layers['B.Cu'] += 1
        elif 'In1' in desc: layers['In1.Cu'] += 1
        elif 'In2' in desc: layers['In2.Cu'] += 1
        else: layers['other'] += 1
for l, c in sorted(layers.items(), key=lambda x: x[1], reverse=True):
    print(f"  {l:10s}: {c}")

# 3. items_not_allowed
na = [v for v in viol if v.get('type') == 'items_not_allowed']
print(f"\n=== 不允许项 ({len(na)}) ===")
reasons = defaultdict(int)
for v in na:
    desc = v.get('description', '')
    reasons[desc[:80]] += 1
for d, c in sorted(reasons.items(), key=lambda x: x[1], reverse=True)[:10]:
    print(f"  {c:3d}x  {d}")

# 4. courtyards_overlap
co = [v for v in viol if v.get('type') == 'courtyards_overlap']
print(f"\n=== Courtyard重叠 ({len(co)}) ===")
for v in co:
    items = v.get('items', [])
    refs = [it.get('description', '')[:40] for it in items]
    print(f"  {' <-> '.join(refs)}")

# 5. 未连接
print(f"\n=== 未连接 ({len(unc)}) ===")
unc_nets = defaultdict(int)
for u in unc:
    items = u.get('items', [])
    for it in items:
        desc = it.get('description', '')
        unc_nets[desc[:60]] += 1
for d, c in sorted(unc_nets.items(), key=lambda x: x[1], reverse=True)[:20]:
    print(f"  {c:3d}x  {d}")

# 6. hole相关
hc = [v for v in viol if 'hole' in v.get('type', '')]
print(f"\n=== 孔位错误 ({len(hc)}) ===")
for v in hc[:10]:
    print(f"  {v.get('type')}: {v.get('description','')[:80]}")

# 7. clearance
cl = [v for v in viol if v.get('type') == 'clearance']
print(f"\n=== 间距违规 ({len(cl)}) ===")
cl_types = defaultdict(int)
for v in cl:
    desc = v.get('description', '')
    cl_types[desc[:60]] += 1
for d, c in sorted(cl_types.items(), key=lambda x: x[1], reverse=True)[:10]:
    print(f"  {c:3d}x  {d}")
