"""Write game/assets/characters/<id>.glb.import from barrow_jarl's (same importer settings), uid line removed.
python mkimport.py <id> [<id> ...]"""
import hashlib, os, re, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", ".."))
CHAR = os.path.join(ROOT, "game", "assets", "characters")
src = open(os.path.join(CHAR, "barrow_jarl.glb.import")).read()
for cid in sys.argv[1:]:
    h = hashlib.md5(f"res://assets/characters/{cid}.glb".encode()).hexdigest()
    t = re.sub(r'^uid=.*\n', '', src, flags=re.M)
    t = t.replace("barrow_jarl.glb-aeb3b963fa65716ca0991ab460f93dec", f"{cid}.glb-{h}").replace("barrow_jarl.glb", f"{cid}.glb")
    assert "barrow" not in t
    open(os.path.join(CHAR, cid + ".glb.import"), "w", newline="\n").write(t)
    print("wrote", cid + ".glb.import")
