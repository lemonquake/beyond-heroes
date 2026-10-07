"""bh-042: fetch the chosen CC0 OpenGameArt creatures into assets_src/bh042/oga/<slug>/ and record provenance."""
import datetime, hashlib, json, os, urllib.request, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
OGA = os.path.join(HERE, "oga")
PICK = ["giant-mutant", "3d-horror-game-monster", "darsh-undead-creature", "low-poly-werewolf", "glutton-demon",
        "cethiels-dragon-3d", "skull-prop", "forest-monster"]
rows = {r["slug"]: r for f in ("oga_a.json", "oga_b.json") for r in json.load(open(os.path.join(HERE, "previews", f)))}
src_path = os.path.join(HERE, "sources.json")
recs = json.load(open(src_path)) if os.path.exists(src_path) else []
have = {r.get("url") for r in recs}


def record(slug, title, url, path):
    d = open(path, "rb").read()
    if url in have:
        return
    recs.append({"source": "OpenGameArt", "page": "https://opengameart.org/content/" + slug, "title": title, "url": url,
                 "path": os.path.relpath(path, HERE).replace(os.sep, "/"), "bytes": len(d),
                 "sha256": hashlib.sha256(d).hexdigest(), "downloaded": datetime.date.today().isoformat(), "license": "CC0 1.0"})


for slug in PICK:
    r = rows[slug]
    os.makedirs(os.path.join(OGA, slug), exist_ok=True)
    for u in r["files"]:
        fn = os.path.join(OGA, slug, urllib.request.unquote(u.rsplit("/", 1)[1]))
        if not os.path.exists(fn):
            d = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=300).read()
            open(fn, "wb").write(d)
            print(fn, len(d))
        record(slug, r["title"], u, fn)
        if fn.lower().endswith(".zip"):
            try:
                zipfile.ZipFile(fn).extractall(os.path.join(OGA, slug))
            except Exception as e:
                print("unzip failed", fn, e)
for slug, title, u in [("demon-statue", "Demon statue", "https://opengameart.org/sites/default/files/demon_statue.blend"),
                       ("lava-golem", "lava golem", "https://opengameart.org/sites/default/files/golem_clean.blend.zip")]:
    record(slug, title, u, os.path.join(OGA, u.rsplit("/", 1)[1]))
json.dump(recs, open(src_path, "w"), indent=1)
print("records", len(recs))
