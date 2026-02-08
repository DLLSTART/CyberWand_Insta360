import json, sys
from collections import defaultdict
sys.stdout.reconfigure(encoding='utf-8')

with open(r'd:\win_workspace\CyberWand_Insta360\schematic\skidl\docs\DRC_v5.json','r',encoding='utf-8') as f:
    data = json.load(f)

unconnected = data.get('unconnected_items', [])
violations = data.get('violations', [])

vtypes = defaultdict(int)
for v in violations:
    vtypes[v.get('type','')] += 1

# 固定问题（非布线）
fixed = ['courtyards_overlap','silk_over_copper','silk_overlap','silk_edge_clearance',
         'drill_out_of_range','items_not_allowed','solder_mask_bridge']
fixed_cnt = sum(vtypes.get(t,0) for t in fixed)
routing_cnt = len(violations) - fixed_cnt

print(f'未连接: {len(unconnected)}')
print(f'违规总计: {len(violations)}')
print(f'  非布线(固定): {fixed_cnt}')
print(f'  布线相关: {routing_cnt}')
print()

# 对比表
v1 = {'shorting_items':199, 'solder_mask_bridge':157, 'tracks_crossing':102,
      'hole_clearance':93, 'clearance':64, 'silk_over_copper':42,
      'courtyards_overlap':33, 'silk_overlap':32, 'hole_to_hole':29,
      'track_dangling':18, 'items_not_allowed':13, 'drill_out_of_range':12,
      'starved_thermal':10, 'via_dangling':5, 'copper_edge_clearance':4,
      'silk_edge_clearance':2, 'holes_co_located':2}

print(f'{"类型":40s} {"v1":>5s} {"v6":>5s} {"变化":>7s}')
print('-'*60)
for t in sorted(set(list(v1.keys()) + list(vtypes.keys()))):
    a = v1.get(t,0)
    b = vtypes.get(t,0)
    c = b - a
    s = '+' if c>0 else ('-' if c<0 else '=')
    print(f'{t:40s} {a:5d} {b:5d} {s}{abs(c):>6d}')

# 未连接网络
print()
net_u = defaultdict(int)
for item in unconnected:
    for sub in item.get('items',[]):
        d = sub.get('description','')
        if '[' in d and ']' in d:
            net_u[d.split('[')[1].split(']')[0]] += 1
for n,c in sorted(net_u.items(), key=lambda x:x[1], reverse=True):
    print(f'  未连接 {n}: {c}')

# 非GND未连接
print('\n非GND:')
for item in unconnected:
    descs = [sub.get('description','') for sub in item.get('items',[])]
    if not any('[GND]' in d for d in descs):
        print(f'  ' + ' <-> '.join([d[:65] for d in descs]))
