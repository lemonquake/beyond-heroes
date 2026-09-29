"""Build only the fifty new weapons and twenty-one remodeled bows.

blender -b --factory-startup --python tools/blender/items/build_artisan.py -- all
python tools/blender/items/build_artisan.py icons-post
"""
import os
import sys
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
EVID=ROOT/'work/lemondev/tempo-armory/evidence/weapons'
os.environ['BH_ITEM_EVIDENCE']=str(EVID)
sys.path.insert(0,str(HERE))
rows=json.loads((HERE/'artisan_manifest.json').read_text())
old=json.loads((HERE/'items.json').read_text())
ids=list(dict.fromkeys([r['id'] for r in rows]+[r['id'] for r in old if r.get('weapon_type')=='bow']))

if 'icons-post' in sys.argv:
    import icons_post as P
    from PIL import Image, ImageDraw, ImageFont
    P.RAW=str(EVID/'icons/raw')
    P.EVID=str(EVID)
    for iid in ids:
        P.game_icon(str(Path(P.RAW)/(iid+'.png'))).save(str(Path(P.GAME_ICONS)/(iid+'.png')))
    for family in ['bow','crossbow','dagger','sword','axe']:
        selected=[r for r in rows if r['weapon_type']==family]
        sheet=Image.new('RGB',(1500,680),(24,28,37))
        draw=ImageDraw.Draw(sheet)
        title=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',30)
        label=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18)
        draw.text((24,14),family.title()+' designs',font=title,fill=(238,225,195))
        for j,row in enumerate(selected):
            x=(j%5)*300; y=64+(j//5)*304
            tile=Image.new('RGBA',(280,256),(40,43,53,255))
            icon=P.game_icon(str(Path(P.RAW)/(row['id']+'.png')),256)
            tile.alpha_composite(icon,(12,0))
            sheet.paste(tile.convert('RGB'),(x+10,y))
            draw.text((x+15,y+262),row['name'],font=label,fill=(225,218,204))
        sheet.save(EVID/('artisan_'+family+'.png'))
    P.sheet('existing_bows',[r['id'] for r in old if r.get('weapon_type')=='bow'],cols=7,cell=180)
else:
    import build_items as B
    args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['all']
    sys.argv=[sys.argv[0],'--']+args+ids
    B.main()
