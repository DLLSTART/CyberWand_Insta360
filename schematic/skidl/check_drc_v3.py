import json, sys
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')

with open(r'd:\win_workspace\CyberWand_Insta360\schematic\skidl\docs\DRC_v3.json','r',encoding='utf-8') as f:
    data = json.load(f)

unconnected = data.get('unconnected_items', [])
violations = data.get('violations', [])

print('=== DRC v3 对比 v1 ===')
print(f'v1: 75 未连接 + 817 违规 = 892')
print(f'v3: {len(unconnected)} 未连接 + {len(violations)} 违规 = {len(unconnected)+len(violations)}')
print()

# 未连接详情
net_issues = defaultdict(list)
for item in unconnected:
    descs = []
    for sub in item.get('items',[]):
        desc = sub.get('description','')
        descs.append(desc)
        if '[' in desc and ']' in desc:
            net = desc.split('[')[1].split(']')[0]
            net_issues[net].append(descs)

print('未连接网络统计:')
for net, items in sorted(net_issues.items(), key=lambda x: len(x[1]), reverse=True):
    print(f'  {net:25s}: {len(items)} 处')

# 显示非GND未连接
print('\n非GND未连接详情:')
for item in unconnected:
    descs = [sub.get('description','') for sub in item.get('items',[])]
    is_gnd = any('[GND]' in d for d in descs)
    if not is_gnd:
        print(f'  ' + ' <-> '.join([d[:70] for d in descs]))

# 违规类型
vtypes = defaultdict(int)
for v in violations:
    vtypes[v.get('type','')] += 1

print('\n违规类型对比:')
v1_types = {
    'shorting_items': 199,
    'solder_mask_bridge': 157,
    'tracks_crossing': 102,
    'hole_clearance': 93,
    'clearance': 64,
    'silk_over_copper': 42,
    'courtyards_overlap': 33,
    'silk_overlap': 32,
    'hole_to_hole': 29,
    'track_dangling': 18,
    'items_not_allowed': 13,
    'drill_out_of_range': 12,
    'starved_thermal': 10,
    'via_dangling': 5,
    'copper_edge_clearance': 4,
    'silk_edge_clearance': 2,
    'holes_co_located': 2,
}
print(f'  {"类型":40s} {"v1":>6s} {"v3":>6s} {"变化":>8s}')
print(f'  {"-"*40} {"-"*6} {"-"*6} {"-"*8}')

all_types = set(list(v1_types.keys()) + list(vtypes.keys()))
for t in sorted(all_types):
    v1 = v1_types.get(t, 0)
    v3 = vtypes.get(t, 0)
    change = v3 - v1
    arrow = '+' if change > 0 else ('-' if change < 0 else '=')
    print(f'  {t:40s} {v1:6d} {v3:6d} {arrow}{abs(change):>7d}')

# 短路详情
shorts = [v for v in violations if v.get('type')=='shorting_items']
print(f'\n短路详情 ({len(shorts)}个):')
for s in shorts[:15]:
    items = s.get('items',[])
    descs = [i.get('description','')[:70] for i in items]
    sep = ' | '
    print(f'  {sep.join(descs)}')

# 交叉详情
crossing = [v for v in violations if v.get('type')=='tracks_crossing']
print(f'\n走线交叉 ({len(crossing)}个，前10):')
for c in crossing[:10]:
    items = c.get('items',[])
    descs = [i.get('description','')[:70] for i in items]
    sep = ' | '
    print(f'  {sep.join(descs)}')
