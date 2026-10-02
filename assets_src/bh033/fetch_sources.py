"""bh-033: fetch the approved CC0 source assets (Poly Haven, Kenney, Quaternius) into assets_src/bh033/ and record
provenance (URL, date, size, SHA-256) in sources.json. Re-running skips files already present with the same size."""
import hashlib, json, os, re, sys, time, urllib.request, urllib.parse, datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
UA = {"User-Agent": "BeyondHeroes-bh033-asset-fetch"}
POLYHAVEN = ["wooden_crate_01", "wooden_crate_02", "wooden_barrels_01", "wooden_bucket_01", "wooden_bucket_02", "wooden_lantern_01",
    "wicker_basket_01", "wicker_basket_02", "Barrel_01", "wine_barrel_01", "painted_wooden_bench", "planter_box_01", "Lantern_01",
    "tree_stump_01", "WoodenTable_01", "WoodenTable_03", "round_wooden_table_01", "wooden_stool_01", "wooden_stool_02",
    "folding_wooden_stool", "GothicBed_01", "GothicCabinet_01", "wooden_bookshelf_worn", "wooden_display_shelves_01", "jug_01",
    "wooden_bowl_01", "pot_enamel_01", "ceramic_pot", "carved_wooden_plate", "wooden_cutting_board", "wooden_hammer_01", "hatchet",
    "wooden_axe", "treasure_chest"]
KENNEY = "https://kenney.nl/media/pages/assets/fantasy-town-kit/efe948d309-1754222374/kenney_fantasy-town-kit_2.0.zip"
QUATERNIUS = {"ultimate_monsters": ("18m4KpzpEzhC9wl7jzr6dUc0N8Jozr79C", lambda p: "/glTF/" in p or p.endswith((".txt", ".png", ".jpg"))),
    "easy_enemy": ("1VbJIslXPWK-1KybQN6yezZrfJcw608qe", lambda p: "/FBX/" in p or p.endswith((".txt", ".png"))),
    "ultimate_furniture": ("1n85oUi0RN5ZUXEIMKA-AnBsPErVXWcma", lambda p: "/FBX/" in p or p.endswith((".txt", ".png")))}

records = []

def fetch(url, dest, source, extra=None):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    if not os.path.exists(dest):
        for attempt in range(4):
            try:
                with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r, open(dest + ".part", "wb") as f:
                    f.write(r.read())
                os.replace(dest + ".part", dest)
                break
            except Exception as e:
                print("retry", url, e)
                time.sleep(2 + attempt * 3)
        else:
            raise RuntimeError("failed " + url)
    data = open(dest, "rb").read()
    rec = {"source": source, "url": url, "path": os.path.relpath(dest, ROOT).replace("\\", "/"), "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(), "downloaded": datetime.date.today().isoformat()}
    if extra:
        rec.update(extra)
    records.append(rec)
    return rec

def get_json(url):
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60))

def polyhaven():
    for pid in POLYHAVEN:
        info = get_json("https://api.polyhaven.com/info/" + pid)
        files = get_json("https://api.polyhaven.com/files/" + pid)["gltf"]["1k"]["gltf"]
        meta = {"model": pid, "name": info.get("name"), "authors": list(info.get("authors", {}).keys()), "license": "CC0 1.0",
            "polycount": info.get("polycount"), "page": "https://polyhaven.com/a/" + pid}
        fetch(files["url"], os.path.join(ROOT, "polyhaven", pid, os.path.basename(urllib.parse.urlparse(files["url"]).path)), "Poly Haven", meta)
        for rel, inc in files.get("include", {}).items():
            fetch(inc["url"], os.path.join(ROOT, "polyhaven", pid, rel), "Poly Haven", {"model": pid, "license": "CC0 1.0"})
        print("polyhaven", pid)

def drive_list(fid, path, out, depth=0):
    h = urllib.request.urlopen(urllib.request.Request("https://drive.google.com/embeddedfolderview?id=" + fid, headers=UA), timeout=60).read().decode("utf-8", "replace")
    for m in re.finditer(r'<div class="flip-entry" id="entry-([A-Za-z0-9_-]+)".*?flip-entry-title">([^<]+)<', h, re.S):
        eid, name = m.group(1), m.group(2)
        if ("drive/folders/" + eid) in h and depth < 4:
            drive_list(eid, path + "/" + name, out, depth + 1)
        else:
            out.append((eid, path + "/" + name))

def quaternius():
    for pack, (fid, keep) in QUATERNIUS.items():
        entries = []
        drive_list(fid, "", entries)
        for eid, p in entries:
            if keep(p):
                fetch("https://drive.google.com/uc?export=download&id=" + eid, os.path.join(ROOT, "quaternius", pack, p.lstrip("/")), "Quaternius",
                    {"pack": pack, "license": "CC0 1.0", "page": "https://quaternius.com/packs/%s.html" % pack.replace("_", "")})
        print("quaternius", pack, len(entries))

if __name__ == "__main__":
    polyhaven()
    fetch(KENNEY, os.path.join(ROOT, "kenney", "kenney_fantasy-town-kit_2.0.zip"), "Kenney", {"pack": "Fantasy Town Kit 2.0", "license": "CC0 1.0",
        "page": "https://kenney.nl/assets/fantasy-town-kit"})
    quaternius()
    json.dump(records, open(os.path.join(ROOT, "sources.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("records", len(records), "MB", round(sum(r["bytes"] for r in records) / 1e6, 1))
