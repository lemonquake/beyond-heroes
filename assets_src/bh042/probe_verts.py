import bpy, sys, math
from mathutils import Matrix, Vector
a = sys.argv[sys.argv.index("--") + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
with bpy.data.libraries.load(a[0]) as (s, d):
    d.objects = list(s.objects)
o = next(x for x in d.objects if x and x.name == "Demon")
sc.collection.objects.link(o)
for mod in list(o.modifiers): o.modifiers.remove(mod)
o.parent = None
bpy.context.view_layer.update()
Y = Matrix.Rotation(math.radians(45), 4, "Z")
pts = [Y @ o.matrix_world @ v.co for v in o.data.vertices]
lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts))); hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
s = 1.8 / (hi.z - lo.z); off = Vector(((lo.x+hi.x)/2, (lo.y+hi.y)/2, lo.z))
P = [(p - off) * s for p in pts]
body = [p for p in P if p.y < -0.25]
print("BODY y range", min(p.y for p in body), max(p.y for p in body))
for zlo, zhi in [(0.0,0.2),(0.4,0.6),(0.8,1.0),(1.0,1.2),(1.2,1.4),(1.4,1.6),(1.6,1.8)]:
    sl = [p for p in body if zlo <= p.z < zhi]
    if sl:
        print("Z %.1f-%.1f  x[%.2f,%.2f] y[%.2f,%.2f] n=%d" % (zlo, zhi, min(p.x for p in sl), max(p.x for p in sl), min(p.y for p in sl), max(p.y for p in sl), len(sl)))
arm = [p for p in P if 1.0 < p.z < 1.45 and p.y < -0.3]
for side in (1, -1):
    sl = sorted([p for p in arm if p.x * side > 0.25], key=lambda p: -abs(p.x) - abs(p.y + 0.55))
    if sl: print("FAR", side, [tuple(round(c, 2) for c in sl[i]) for i in range(0, min(len(sl), 40), 8)])
fw = sorted([p for p in P if 1.0 < p.z < 1.5], key=lambda p: p.y)[:5]
print("MOST FORWARD", [tuple(round(c, 2) for c in p) for p in fw])
la = [p for p in P if 0.25 < p.x < 0.8 and 0.9 < p.z < 1.5 and -0.5 < p.y < 0.4]
for yb in [(-0.5,-0.3),(-0.3,-0.1),(-0.1,0.1),(0.1,0.3),(0.3,0.5)]:
    sl=[p for p in la if yb[0]<=p.y<yb[1]]
    if sl: print("LA y %.1f..%.1f x[%.2f,%.2f] z[%.2f,%.2f] n=%d" % (yb[0],yb[1],min(p.x for p in sl),max(p.x for p in sl),min(p.z for p in sl),max(p.z for p in sl),len(sl)))
