import re, urllib.request, json, os, sys
from PIL import Image, ImageDraw
UA={"User-Agent":"Mozilla/5.0"}
def get(u):
    return urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=40).read()
keys=sys.argv[1].split(",")
seen=set(); rows=[]
for k in keys:
    try:
        h=get("https://opengameart.org/art-search-advanced?keys=%s&field_art_type_tid%%5B%%5D=10&field_art_licenses_tid%%5B%%5D=4&sort_by=count&sort_order=DESC"%k.replace(" ","%20")).decode("utf-8","replace")
    except Exception as e:
        print("ERR",k,e); continue
    for slug,title in re.findall(r'<a href="/content/([^"]+)">([^<]+)</a>',h)[:8]:
        if slug in seen: continue
        seen.add(slug)
        try:
            p=get("https://opengameart.org/content/"+slug).decode("utf-8","replace")
        except Exception: continue
        imgs=[u for u in re.findall(r'https://opengameart.org/sites/default/files/[^"\']+\.(?:png|jpg|jpeg|gif)',p) if "icon" not in u and "license_images" not in u and "pictures" not in u and "styles" not in u]
        files=re.findall(r'https://opengameart.org/sites/default/files/[^"\']+\.(?:zip|blend|glb|gltf|fbx|obj|7z|rar|dae)',p)
        if imgs:
            rows.append({"slug":slug,"title":title,"img":imgs[0],"files":sorted(set(files))})
json.dump(rows,open("oga_%s.json"%sys.argv[2],"w"),indent=1)
ims=[]
for r in rows:
    try:
        im=Image.open(__import__("io").BytesIO(get(r["img"]))).convert("RGB"); im.thumbnail((300,300))
        c=Image.new("RGB",(300,320),(25,25,28)); c.paste(im,(0,20)); ImageDraw.Draw(c).text((4,4),r["slug"][:44],fill=(255,255,0)); ims.append(c)
    except Exception: pass
cols=6; rows_n=(len(ims)+cols-1)//cols
S=Image.new("RGB",(300*cols,320*max(1,rows_n)),(0,0,0))
for i,c in enumerate(ims): S.paste(c,((i%cols)*300,(i//cols)*320))
S.save("oga_%s.jpg"%sys.argv[2]); print(len(ims))
