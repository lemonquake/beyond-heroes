"""bh-042: Poly Haven CC0 texture sets for the Abyss dungeons -> game/assets/textures/ph_<id>_{albedo,normal,rough}.png
(1k, the game's texture naming; import settings copied from an existing set so they get VRAM compression and
mipmaps — bh-038). Provenance in assets_src/bh042/sources.json."""
import datetime, hashlib, io, json, os, re, urllib.request
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
GAME_TEX = os.path.join(HERE, "..", "..", "game", "assets", "textures")
IDS = ["medieval_blocks_02", "castle_wall_slates", "mossy_stone_wall", "seaworn_stone_tiles", "castle_brick_07", "dark_rock",
       "castle_brick_02_white", "rock_wall_08", "dark_rock_02", "rough_block_wall"]
UA = {"User-Agent": "BeyondHeroes-bh042-asset-fetch"}
src_path = os.path.join(HERE, "sources.json")
recs = json.load(open(src_path)) if os.path.exists(src_path) else []
have = {r.get("url") for r in recs}


def get(u):
    return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=180).read()


def import_file(kind, name):
    tmpl = open(os.path.join(GAME_TEX, "basalt_%s.png.import" % kind), encoding="utf-8").read()
    tmpl = re.sub(r'^uid=.*\n', "", tmpl, flags=re.M)
    tmpl = re.sub(r'^path\.[a-z0-9]+=.*\n', "", tmpl, flags=re.M)
    tmpl = re.sub(r'^dest_files=.*\n', "", tmpl, flags=re.M)
    tmpl = tmpl.replace("basalt_%s.png" % kind, "%s_%s.png" % (name, kind))
    open(os.path.join(GAME_TEX, "%s_%s.png.import" % (name, kind)), "w", encoding="utf-8").write(tmpl)


for pid in IDS:
    files = json.loads(get("https://api.polyhaven.com/files/" + pid))
    info = json.loads(get("https://api.polyhaven.com/info/" + pid))
    name = "ph_" + pid
    for kind, key in (("albedo", "Diffuse"), ("normal", "nor_gl"), ("rough", "Rough")):
        ent = files.get(key, {}).get("1k", {})
        ent = ent.get("png") or ent.get("jpg")
        if not ent:
            print("missing", pid, key)
            continue
        url = ent["url"]
        data = get(url)
        im = Image.open(io.BytesIO(data)).convert("RGB")
        if max(im.size) > 1024:
            im = im.resize((1024, 1024), Image.LANCZOS)
        out = os.path.join(GAME_TEX, "%s_%s.png" % (name, kind))
        im.save(out)
        import_file(kind, name)
        if url not in have:
            recs.append({"source": "Poly Haven", "url": url, "page": "https://polyhaven.com/a/" + pid, "name": info.get("name", pid),
                         "authors": list(info.get("authors", {}).keys()), "license": "CC0 1.0", "bytes": len(data),
                         "sha256": hashlib.sha256(data).hexdigest(), "downloaded": datetime.date.today().isoformat(),
                         "path": "game/assets/textures/%s_%s.png" % (name, kind)})
        print(pid, kind, im.size)
json.dump(recs, open(src_path, "w"), indent=1)
