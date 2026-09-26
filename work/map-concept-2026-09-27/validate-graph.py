"""Validate authored atlas data and synchronize its embedded offline copy.
Run: python validate-graph.py [--sync]
No game/save files are read or written.
"""
import json, math, pathlib, re, sys, heapq
ROOT = pathlib.Path(__file__).resolve().parent
raw = (ROOT / 'island-graph.json').read_text(encoding='utf-8')
g = json.loads(raw)
places = {p['id']:p for p in g['places']}
assert len(places) == len(g['places'])
assert len({e['id'] for e in g['edges']}) == len(g['edges'])
sx = g['scale']['width_m'] / g['scale']['width_px']
sy = g['scale']['height_m'] / g['scale']['height_px']
def length(e):
    return sum(math.hypot((b[0]-a[0])*sx,(b[1]-a[1])*sy) for a,b in zip(e['points'],e['points'][1:]))
adj = {p:[] for p in places}
for e in g['edges']:
    a,b = places[e['a']],places[e['b']]
    assert e['points'][0] == [a['x'],a['y']],e['id']
    assert e['points'][-1] == [b['x'],b['y']],e['id']
    if e['type'] != 'door':
        assert length(e)>0
        lake=g['lake']
        for x,y in zip(e['points'],e['points'][1:]):
            for i in range(101):
                t=i/100; px=x[0]+(y[0]-x[0])*t; py=x[1]+(y[1]-x[1])*t
                assert ((px-lake['cx'])/lake['rx'])**2+((py-lake['cy'])/lake['ry'])**2 > 1, (e['id'],'crosses lake')
    if not e.get('locked'):
        adj[e['a']].append((e['b'],length(e),e['id']))
        adj[e['b']].append((e['a'],length(e),e['id']))
def path(start,end,excluded=None):
    queue=[(0,start,[])]; seen=set()
    while queue:
        cost,node,edges=heapq.heappop(queue)
        if node in seen: continue
        seen.add(node)
        if node==end: return cost,edges
        for target,distance,eid in adj[node]:
            if eid!=excluded: heapq.heappush(queue,(cost+distance,target,edges+[eid]))
    return None
for p in places:
    assert (path('town',p) is not None) == (p!='throne'),p
assert path('town','forest','town_forest')
assert path('town','forest','mill_forest')
surface=[p for p in places.values() if p['kind']!='Underground']
surface_edges=[e for e in g['edges'] if e['type']!='door']
cycles=len(surface_edges)-len(surface)+1
assert cycles>=2
assert sum(bool(p.get('shrine')) for p in surface)==6
assert sum(bool(p.get('awakened')) for p in surface)==3
html_path=ROOT/'atlas-preview.html'
html=html_path.read_text(encoding='utf-8')
pattern=r'(<script id="graph-data" type="application/json">)[\s\S]*?(</script>)'
if '--sync' in sys.argv:
    html=re.sub(pattern,lambda m:m[1]+raw+m[2],html)
    html_path.write_text(html,encoding='utf-8')
embedded=re.search(pattern,html).group(0).split('>',1)[1].rsplit('</script>',1)[0]
assert json.loads(embedded)==g,'Embedded graph stale; run --sync'
assert 'fetch(' not in html,'Offline atlas must not fetch its data'
assert 'Game.travel' not in html,'Prototype must not claim game travel'
print(f'PASS: {len(places)} places, {len(g["edges"])} edges, {cycles} independent surface cycles, six shrines.')
print('PASS: endpoints, lake clearance, unlocked reachability, throne lock, independent forest approaches, offline embedded graph.')
for destination in ('forest','rise','temple','chapel','marsh','fields','cove','catacombs'):
    result=path('town',destination)
    print(f'town -> {destination}: {result[0]:.1f} m; {result[0]/5:.1f} s walking, no combat; '+', '.join(result[1]))
