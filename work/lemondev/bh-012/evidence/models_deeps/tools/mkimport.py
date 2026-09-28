"""Write <id>.glb.import next to the GLB, copied from necromancer.glb.import with paths re-hashed (no uid line)."""
import hashlib, sys, os
D = r"A:\Python\beyond-heroes\game\assets\characters"
src = open(os.path.join(D, "necromancer.glb.import")).read()
for cid in sys.argv[1:]:
    h = hashlib.md5(f"res://assets/characters/{cid}.glb".encode()).hexdigest()
    t = src.replace("necromancer.glb-4852b3683d3e97f7f033a2384cebda3a", f"{cid}.glb-{h}").replace(
        "assets/characters/necromancer.glb", f"assets/characters/{cid}.glb")
    t = "\n".join(l for l in t.splitlines() if not l.startswith("uid=")) + "\n"
    open(os.path.join(D, cid + ".glb.import"), "w").write(t)
    print("wrote", cid)
