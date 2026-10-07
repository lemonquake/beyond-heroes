"""bh-042: download a free (CC0) Quaternius pack from itch.io through the page's own free-download flow and record
provenance (URL, date, size, SHA-256) in sources.json.  python itch_fetch.py <project> <outdir> [name-filter ...]"""
import hashlib, http.cookiejar, json, os, re, sys, urllib.parse, urllib.request, datetime

proj, out = sys.argv[1], sys.argv[2]
filters = sys.argv[3:]
os.makedirs(out, exist_ok=True)
jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
op.addheaders = [("User-Agent", "Mozilla/5.0 BeyondHeroes-bh042-asset-fetch")]
base = "https://quaternius.itch.io/" + proj


def get(url, data=None):
    body = urllib.parse.urlencode(data).encode() if data is not None else None
    with op.open(url, body, timeout=120) as r:
        return r.read().decode("utf-8", "replace")


page = get(base)
csrf = re.search(r'name="csrf_token" value="([^"]+)"', page) or re.search(r'"csrf_token":"([^"]+)"', page)
csrf = csrf.group(1)
dl = json.loads(get(base + "/download_url", {"csrf_token": csrf}))["url"]
print("download page", dl)
key = urllib.parse.unquote(dl.rsplit("/", 1)[1])
dpage = get(dl)
csrf2 = (re.search(r'name="csrf_token" value="([^"]+)"', dpage) or re.search(r'"csrf_token":"([^"]+)"', dpage)).group(1)
uploads = re.findall(r'data-upload_id="(\d+)".*?title="([^"]+)" class="name"', dpage, re.S)
seen = set()
recs_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sources.json")
recs = json.load(open(recs_path)) if os.path.exists(recs_path) else []
for uid, name in uploads:
    if uid in seen:
        continue
    seen.add(uid)
    if filters and not any(f.lower() in name.lower() for f in filters):
        print("skip", name)
        continue
    dest = os.path.join(out, name)
    if os.path.exists(dest):
        print("have", name)
        continue
    url = json.loads(get(base + "/file/%s?source=game_download&key=%s" % (uid, key), {"csrf_token": csrf2}))["url"]
    print("fetch", name)
    with op.open(url, timeout=1800) as r, open(dest + ".part", "wb") as f:
        while True:
            b = r.read(1 << 20)
            if not b:
                break
            f.write(b)
    os.replace(dest + ".part", dest)
    data = open(dest, "rb").read()
    recs.append({"source": "Quaternius (itch.io)", "page": base, "file": name, "path": os.path.relpath(dest, os.path.dirname(recs_path)).replace("\\", "/"),
                 "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(), "downloaded": datetime.date.today().isoformat(),
                 "license": "CC0 1.0"})
    json.dump(recs, open(recs_path, "w"), indent=1)
    print("done", name, len(data))
