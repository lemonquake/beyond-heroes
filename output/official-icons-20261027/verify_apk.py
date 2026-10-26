import json,re,zipfile,hashlib
from pathlib import Path
apk=Path('build/BeyondHeroes.apk');expected=Path('game/assets/ui/official/manifest.json').read_bytes()
fail=[]
with zipfile.ZipFile(apk) as z:
    names=set(z.namelist()); raw=z.read('assets/assets/ui/official/manifest.json');data=json.loads(raw)
    if raw!=expected:fail.append('Packaged artwork manifest differs from source')
    paths=[a['path'] for a in data['artifacts'].values()]+list(data['retained_artifacts'])+['res://assets/ui/borders/aether_forged.png']
    for path in paths:
        imported='assets/'+path.removeprefix('res://')+'.import'
        if imported not in names:fail.append('Missing import '+path);continue
        text=z.read(imported).decode()
        target=re.search(r'^path="([^"]+)"',text,re.M)
        if target is None or 'assets/'+target[1].removeprefix('res://') not in names:fail.append('Missing imported texture '+path)
    corrupt=z.testzip()
    if corrupt:fail.append('Corrupt APK entry '+corrupt)
    arch=sorted({p.split('/')[1] for p in names if p.startswith('lib/') and p.endswith('.so')})
out={'apk':str(apk),'sha256':hashlib.sha256(apk.read_bytes()).hexdigest(),'official_icons':len(data['artifacts']),'retained_icons':len(data['retained_artifacts']),'border':True,'architectures':arch,'failures':fail}
Path('output/official-icons-20261027/apk-probe.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out));raise SystemExit(bool(fail))
