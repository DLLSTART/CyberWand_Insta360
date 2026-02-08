"""分析短路原因"""
import json, sys
from collections import defaultdict
sys.stdout.reconfigure(encoding='utf-8')

with open(r'd:\win_workspace\CyberWand_Insta360\schematic\skidl\docs\DRC_v2.json','r',encoding='utf-8') as f:
    data = json.load(f)

shorts = [v for v in data.get('violations',[]) if v.get('type')=='shorting_items']
print(f'shorts: {len(shorts)}')

patterns = defaultdict(int)
net_pairs = defaultdict(int)
for v in shorts:
    items = v.get('items',[])
    types = []
    nets = []
    for i in items:
        d = i.get('description','')
        if 'via' in d.lower():
            types.append('via')
        elif 'walk' in d.lower() or 'track' in d.lower():
            types.append('track')
        elif 'pad' in d.lower():
            types.append('pad')
        else:
            types.append('other')
        if '[' in d and ']' in d:
            net = d.split('[')[1].split(']')[0]
            nets.append(net)
    pattern = ' vs '.join(sorted(types))
    patterns[pattern] += 1
    if len(nets) >= 2:
        pair = tuple(sorted(nets[:2]))
        net_pairs[pair] += 1

print('\n=== short type distribution ===')
for p, c in sorted(patterns.items(), key=lambda x: x[1], reverse=True):
    print(f'  {p:30s}: {c}')

print('\n=== top shorting net pairs ===')
for (n1,n2), c in sorted(net_pairs.items(), key=lambda x: x[1], reverse=True)[:25]:
    print(f'  {n1:20s} <-> {n2:20s}: {c}')

# items_not_allowed详情
ina = [v for v in data.get('violations',[]) if v.get('type')=='items_not_allowed']
print(f'\n=== items_not_allowed: {len(ina)} ===')
ina_types = defaultdict(int)
for v in ina:
    for i in v.get('items',[]):
        d = i.get('description','')
        if 'via' in d.lower(): ina_types['via'] += 1
        elif 'walk' in d.lower() or 'track' in d.lower(): ina_types['track'] += 1
        else: ina_types['other:'+d[:40]] += 1
for t, c in sorted(ina_types.items(), key=lambda x:x[1], reverse=True):
    print(f'  {t:40s}: {c}')

# 未连接
unc = data.get('unconnected_items',[])
print(f'\n=== unconnected: {len(unc)} ===')
for u in unc:
    nets = []
    for i in u.get('items',[]):
        d = i.get('description','')
        if '[' in d and ']' in d:
            nets.append(d.split('[')[1].split(']')[0])
    print(f'  {", ".join(nets)}')
