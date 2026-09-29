"""Signature weapons and shields for the fifteen boss equipment collections.

blender -b --factory-startup --python tools/blender/items/boss_weapons.py
Palette and IDs follow BossSetVisuals.THEMES. Held origin is the normal grip.
"""
import os
import sys
import re
import json
import math
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(HERE))
os.environ['BH_ITEM_EVIDENCE']=str(ROOT/'work/lemondev/tempo-armory/evidence/boss-weapons')
import item_kit as K
import item_weapons as W
import item_gear as G
import artisan_weapons as A
import build_items as B

THEMES=[]
pattern=r'"([a-z_]+)": \["([^"]+)", "([0-9a-f]+)", "([0-9a-f]+)", "([0-9a-f]+)", "([a-z]+)", "([a-z]+)"\]'
for match in re.finditer(pattern,(ROOT/'game/src/actors/boss_set_visuals.gd').read_text()):
    THEMES.append(match.groups())
TWO_HANDED={'bow','crossbow','staff','spear','greatsword'}

def palette(theme):
    iid,name,body,trim,gem,family,cls=theme
    colors=[]
    for hexcolor in [body,trim,gem]:
        colors.append(tuple((int(hexcolor[j:j+2],16)/255)**2.2 for j in [0,2,4]))
    keys=[f'boss_{iid}_{s}' for s in ['body','trim','glow']]
    K.MAT[keys[0]]=('BH_Steel',colors[0],.72,.43,None,0)
    K.MAT[keys[1]]=('BH_Gold',colors[1],.90,.27,None,0)
    K.MAT[keys[2]]=('BH_Emissive',colors[2],.1,.25,colors[2],1.1)
    return keys

def remap(parts,keys):
    for part in parts:
        source=K.MAT[part.mat]
        if source[4] or source[0] in ['BH_Gem','BH_Aether']:
            part.mat=keys[2]
        elif part.mat in ['bright','silver','gold','brass','paleg','bronze','copper','sunsteel']:
            part.mat=keys[1]
        elif source[0] not in ['BH_Leather','BH_Cloth_Secondary']:
            part.mat=keys[0]
    return parts

def halo(parts,center,r,keys,count=8):
    x,y,z=center
    parts.append(K.ring_tube(center,r,.009,keys[1],axis='y',n=24))
    for j in range(count):
        a=math.tau*j/count
        p=(x+r*math.cos(a),y,z+r*math.sin(a))
        q=(x+(r+.04)*math.cos(a),y,z+(r+.04)*math.sin(a))
        parts.append(K.cone_spike(p,q,.008,keys[1]))
    parts.append(K.gem(center,r*.30,keys[2],rot=(90,0,0)))

def feathers(parts,x,z,side,keys,n=4):
    for j in range(n):
        points=[(x,z+j*.045),(x+side*.07,z+j*.045+.025),(x+side*(.12+j*.012),z+j*.045+.10),(x+side*.035,z+j*.045+.065)]
        parts.append(A.plate(points,keys[1],.010,.002))
        parts.append(K.gem((x+side*.052,-.014,z+j*.045+.045),.006,keys[2],rot=(90,0,0)))

def weapon(theme):
    iid,name,body,trim,gem,family,cls=theme
    keys=palette(theme)
    if iid=='dragonforge':
        parts=A.axe({'design':5})
        for side in [-1,1]:
            parts.append(K.tube([(side*.03,0,.49),(side*.15,0,.69),(side*.12,0,.86)],[.04,.027,.001],keys[1],n=8))
        for z in [.27,.34,.41]:
            parts.append(K.cone_spike((-.015,0,z),(-.11,0,z+.045),.019,keys[0]))
        halo(parts,(.13,-.035,.56),.065,keys,6)
    elif iid=='truth_of_raikuru':
        parts=A.crossbow({'design':9})
        for side in [-1,1]:
            parts.append(A.line([(side*.07,0,.26),(side*.09,0,.66),(side*.04,0,.92)],.012,keys[1]))
            parts.append(K.crystal((side*.09,0,.66),.24,.032,keys[2],rot=(0,side*13,0)))
        halo(parts,(0,-.13,.37),.105,keys,12)
    elif iid=='crimson_glory':
        parts=A.edged({'design':3,'family':'sword'})
        feathers(parts,0,.07,1,keys,3)
        feathers(parts,0,.07,-1,keys,3)
        for z in [.32,.49,.66]:
            parts.append(K.gem((0,-.024,z),.019,keys[2],rot=(90,0,0)))
    elif iid=='grievance_of_the_fairy':
        parts=A.bow({'design':5})
        for side in [-1,1]:
            feathers(parts,.10,side*.23,1,keys,5)
            parts.append(K.tube([(.02,0,side*.12),(.16,.01,side*.35),(.06,0,side*.59)],[.014,.010,.001],keys[1],n=8))
        halo(parts,(.08,0,0),.06,keys,6)
    elif iid=='wailing_mistress':
        parts=W.staff({'head':'crook','wood':'darkwood','metal':'silver','gem':'shadow','band':'silver','wobble':.03})
        for x in [-.11,.0,.11]:
            parts.append(A.line([(x,0,.68),(x,0,.39)],.006,keys[1]))
            parts.append(K.ring_tube((x,0,.36),.033,.006,keys[1],axis='y',n=16))
            parts.append(K.crystal((x,0,.29),.11,.024,keys[2]))
        parts.append(K.ring_tube((0,0,.73),.19,.012,keys[0],axis='y',n=28,arc=240,a0=-30))
    elif iid=='winter_court':
        parts=W.wand({'head':'branch','wood':'bone','orn':'silver','gem':'ice'})
        for side in [-1,1]:
            for j in range(3):
                parts.append(K.crystal((side*(.03+j*.035),0,.49+j*.025),.24-j*.025,.025,keys[2],rot=(0,side*(12+j*15),0)))
        halo(parts,(0,0,.46),.11,keys,8)
    elif iid=='sunken_crown':
        parts=W.spear({'head':'trident','shaft_top':.91,'shaft_bot':-.85,'head_len':.36,'head_mat':'bronze','glow':'tide','band_mat':'gold'})
        halo(parts,(0,0,1.05),.14,keys,5)
        for side in [-1,1]:
            parts.append(K.tube([(side*.075,0,.9),(side*.16,0,1.01),(side*.13,0,1.22)],[.017,.014,.001],keys[1],n=8))
    elif iid=='thunder_abbot':
        parts=W.staff({'head':'prongs','wood':'darkwood','metal':'gold','gem':'storm','band':'gold'})
        for z,r in [(.58,.09),(.76,.15),(.94,.09)]:
            parts.append(K.ring_tube((0,0,z),r,.013,keys[1],axis='z',n=24))
        parts.append(K.crystal((0,0,.8),.38,.050,keys[2]))
        for side in [-1,1]:
            parts.append(A.line([(side*.04,0,.60),(side*.11,0,.75),(side*.04,0,.72),(side*.13,0,.99)],.009,keys[2]))
    elif iid=='ashfall_pilgrim':
        parts=W.wand({'head':'skull','wood':'darkwood','orn':'bronze','gem':'ember'})
        for z,r in [(.38,.10),(.53,.07)]:
            parts.append(K.ring_tube((0,0,z),r,.011,keys[1],axis='z',n=20))
        for j in range(6):
            a=math.tau*j/6
            parts.append(A.line([(.1*math.cos(a),.1*math.sin(a),.38),(.07*math.cos(a),.07*math.sin(a),.53),(0,0,.62)],.008,keys[1]))
        parts.append(K.crystal((0,0,.49),.23,.044,keys[2]))
    elif iid=='starfall_hunter':
        parts=A.crossbow({'design':6})
        for side in [-1,1]:
            feathers(parts,side*.15,.40,side,keys,3)
        halo(parts,(0,-.12,.4),.14,keys,5)
        parts.append(K.crystal((0,-.06,.83),.14,.023,keys[2]))
    elif iid=='gale_nomad':
        parts=A.bow({'design':7})
        for side in [-1,1]:
            feathers(parts,.06,side*.22,1,keys,3)
        for j in range(3):
            parts.append(K.tube([(.04,.0,-.12),(.10+j*.025,.01,-.24),(.07+j*.04,.0,-.37)],[.007,.01,.001],keys[0],n=6))
    elif iid=='obsidian_oath':
        parts=A.edged({'design':8,'family':'sword'})
        for p in parts: p.scale((1.35,1.2,1.45))
        for side in [-1,1]:
            for z in [.29,.43,.57]:
                parts.append(K.cone_spike((side*.05,0,z),(side*.12,0,z+.06),.018,keys[0]))
        halo(parts,(0,0,.13),.10,keys,4)
        parts+=W.channel(.3,1.18,.013,.006,.023,keys[2])
    elif iid=='pale_requiem':
        parts=A.edged({'design':3,'family':'dagger'})
        for side in [-1,1]:
            parts.append(K.ring_tube((side*.09,0,.095),.075,.008,keys[1],axis='y',n=20,arc=220,a0=20 if side==1 else 160))
        parts.append(K.crystal((0,0,.38),.23,.017,keys[2]))
    elif iid=='serpent_veil':
        parts=W.claw({'len':.35,'blades':3,'spacing':.045,'hook':.10,'blade':'moonsteel','frame_mat':'gold','glow':'venom','spikes':True})
        parts.append(K.tube([(-.07,0,-.03),(-.10,0,.09),(.0,0,.18),(.10,0,.09),(.07,0,-.03)],[.02,.024,.025,.024,.02],keys[0],n=10))
        for side in [-1,1]:
            parts.append(K.gem((side*.045,-.04,.105),.013,keys[2],rot=(90,0,0)))
    else:
        parts=A.edged({'design':4,'family':'dagger'})
        parts.append(K.ring_tube((0,0,.20),.10,.012,keys[1],axis='y',n=24,arc=260,a0=25))
        parts.append(K.ring_tube((0,0,-.16),.050,.009,keys[1],axis='y',n=20))
        for side in [-1,1]:
            parts.append(K.cone_spike((side*.065,0,.11),(side*.10,0,.04),.012,keys[2]))
    return remap(parts,keys)

def shield(theme):
    iid,name,body,trim,gem,family,cls=theme
    keys=palette(theme)
    index=[t[0] for t in THEMES].index(iid)
    shapes={'dragonforge':'heater','crimson_glory':'tower','winter_court':'heater','ashfall_pilgrim':'round','pale_requiem':'heater','serpent_veil':'round','eclipse_dancer':'round'}
    parts=G.shield({'shape':shapes[iid],'w':.32 if iid=='crimson_glory' else .61,'h':.5,'r':.29,'face':'darksteel','rim':'gold','body':'darkwood','emblem':'sigil','gem':'ice'})
    halo(parts,(0,-.18,.045),.14,keys,3+index%7)
    if iid in ['dragonforge','winter_court','serpent_veil']:
        for side in [-1,1]:
            for j in range(3):
                parts.append(K.cone_spike((side*.22,-.06,.12+j*.08),(side*(.31+j*.012),-.04,.20+j*.08),.023,keys[1]))
    elif iid=='crimson_glory':
        feathers(parts,0,-.06,1,keys,5)
        feathers(parts,0,-.06,-1,keys,5)
        for part in parts[-20:]: part.move((0,-.16,0))
    elif iid=='pale_requiem':
        parts.append(K.ring_tube((0,-.17,.08),.23,.015,keys[1],axis='y',n=28,arc=235,a0=-25))
    elif iid=='eclipse_dancer':
        parts.append(K.ring_tube((0,-.16,0),.245,.014,keys[2],axis='y',n=28,arc=240,a0=30))
    else:
        for side in [-1,1]:
            parts.append(K.tube([(side*.11,-.06,-.10),(side*.14,-.08,-.27),(side*.10,-.06,-.42)],[.018,.012,.001],keys[1],n=7))
    return remap(parts,keys)

SPECS={}
ITEMS=[]
for theme in THEMES:
    for slot in ['main_weapon']+([] if theme[5] in TWO_HANDED else ['sub_weapon']):
        iid='boss_'+theme[0]+'_'+slot
        SPECS[iid]=(weapon if slot=='main_weapon' else shield,theme)
        ITEMS.append({'id':iid,'category':'weapon' if slot=='main_weapon' else 'shield','weapon_type':theme[5] if slot=='main_weapon' else ''})

def main():
    from build import reset,export_glb
    report=[]
    for item in ITEMS:
        reset()
        fn,theme=SPECS[item['id']]
        ob=B.build_object(item['id'],fn(theme))
        export_glb(str(ROOT/'game/assets/items'/(item['id']+'.glb')),[ob],animations=False)
        tris=K.M.tri_count(ob)
        assert tris<12000,(item['id'],tris)
        report.append({'id':item['id'],'tris':tris})
    target=ROOT/'work/lemondev/tempo-armory/evidence/boss-weapons'
    target.mkdir(parents=True,exist_ok=True)
    (target/'models_report.json').write_text(json.dumps(report,indent=2))
    print('BOSS_SIGNATURE_WEAPONS_DONE',len(report))

if __name__=='__main__':main()
