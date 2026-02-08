import json, sys
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')

with open(r'd:\win_workspace\CyberWand_Insta360\schematic\skidl\docs\DRC_v2.json','r',encoding='utf-8') as f:
    data = json.load(f)

unconnected = data.get('unconnected_items', [])
violations = data.get('violations', [])

print('=== DRC v2 分析 ===')
print(f'未连接: {len(unconnected)}')
print(f'违规: {len(violations)}')
print()

# 未连接网络
net_issues = defaultdict(int)
unconn_details = []
for item in unconnected:
    descs = []
    for sub in item.get('items',[]):
        desc = sub.get('description','')
        descs.append(desc)
        if '[' in desc and ']' in desc:
            net = desc.split('[')[1].split(']')[0]
            net_issues[net] += 1
    unconn_details.append(descs)

print('未连接网络:')
for net, cnt in sorted(net_issues.items(), key=lambda x: x[1], reverse=True):
    print(f'  {net:25s}: {cnt}')

print('\n未连接详情:')
for descs in unconn_details[:15]:
    print(f'  - ' + ' <-> '.join([d[:60] for d in descs]))

# 违规类型
vtypes = defaultdict(int)
for v in violations:
    vtypes[v.get('type','')] += 1

print('\n违规类型:')
for t, cnt in sorted(vtypes.items(), key=lambda x: x[1], reverse=True):
    print(f'  {t:40s}: {cnt}')

# 各类详情
for vtype in ['shorting_items', 'tracks_crossing', 'clearance', 'hole_clearance']:
    items_of_type = [v for v in violations if v.get('type') == vtype]
    print(f'\n{vtype} 详情 ({len(items_of_type)}个，前8个):')
    for v in items_of_type[:8]:
        descs = [i.get('description','')[:70] for i in v.get('items',[])]
        sep = ' | '
        print(f'  {sep.join(descs)}')
