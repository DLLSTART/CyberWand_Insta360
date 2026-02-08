import json, sys
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')

with open(r'd:\win_workspace\CyberWand_Insta360\schematic\skidl\docs\DRC_v4.json','r',encoding='utf-8') as f:
    data = json.load(f)

unconnected = data.get('unconnected_items', [])
violations = data.get('violations', [])

print(f'未连接: {len(unconnected)}')
print(f'违规: {len(violations)}')

# 违规类型
vtypes = defaultdict(int)
for v in violations:
    vtypes[v.get('type','')] += 1

print('\n违规类型:')
for t, cnt in sorted(vtypes.items(), key=lambda x: x[1], reverse=True):
    print(f'  {t:40s}: {cnt}')

# 非布线相关的固定错误
fixed_types = ['courtyards_overlap','silk_over_copper','silk_overlap','silk_edge_clearance','drill_out_of_range','items_not_allowed']
fixed_count = sum(vtypes.get(t,0) for t in fixed_types)
print(f'\n非布线相关(元件/封装问题): {fixed_count}')
print(f'布线相关: {len(violations) - fixed_count}')

# 未连接详情
net_issues = defaultdict(int)
for item in unconnected:
    for sub in item.get('items',[]):
        desc = sub.get('description','')
        if '[' in desc and ']' in desc:
            net = desc.split('[')[1].split(']')[0]
            net_issues[net] += 1

print('\n未连接:')
for net, cnt in sorted(net_issues.items(), key=lambda x: x[1], reverse=True):
    print(f'  {net:20s}: {cnt}')

# 非GND未连接
print('\n非GND未连接详情:')
for item in unconnected:
    descs = [sub.get('description','') for sub in item.get('items',[])]
    is_gnd = any('[GND]' in d for d in descs)
    if not is_gnd:
        print(f'  ' + ' <-> '.join([d[:65] for d in descs]))

# 短路
shorts = [v for v in violations if v.get('type')=='shorting_items']
print(f'\n短路 ({len(shorts)}):')
for s in shorts[:15]:
    descs = [i.get('description','')[:65] for i in s.get('items',[])]
    print(f'  ' + ' | '.join(descs))

# 交叉
cross = [v for v in violations if v.get('type')=='tracks_crossing']
print(f'\n交叉 ({len(cross)}):')
for c in cross[:10]:
    descs = [i.get('description','')[:65] for i in c.get('items',[])]
    print(f'  ' + ' | '.join(descs))
