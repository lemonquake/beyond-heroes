"""Distinct weapon silhouettes, authored as deterministic beveled geometry.

Every design has its own outline/mechanical construction. Shared palette follows
the game's PBR material naming so worn metal/wood detail survives runtime import.
"""
import math
import json
from pathlib import Path
import numpy as np
import item_kit as K
import item_weapons as W
from item_kit import M, Ry

MANIFEST = json.loads((Path(__file__).parent / "artisan_manifest.json").read_text())
METAL = ["steel", "bronze", "copper", "sunsteel", "darksteel", "moonsteel", "gold", "silver", "moonsteel", "brass"]
BODY = ["ash", "bone", "darkwood", "redwood", "wood", "blackiron", "horn", "blued", "darksteel", "darkwood"]
GLOW = ["pearl", "topaz", "emerald", "ember", "ruby", "shadow", "holy", "tide", "ice", "storm"]

def line(points, radius, mat, name="inlay"):
    return K.tube(points, [radius] * len(points), mat, n=6, name=name)

def smooth(points, steps=6):
    """Catmull-Rom interpolation keeps authored endpoints while softening organic limbs."""
    pts = [np.array(p, dtype=float) for p in points]
    padded = [pts[0]] + pts + [pts[-1]]
    out=[]
    for j in range(len(pts)-1):
        a,b,c,d=padded[j:j+4]
        for n in range(steps):
            t=n/steps
            out.append(tuple(.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t)))
    return out+[tuple(pts[-1])]

def plate(outline, mat, depth=.028, bevel=.004):
    return M.bevel(K.slab(outline, depth, mat), bevel, 1)

def sharpened(outline, mat, depth=.024):
    """A silver outer edge surrounding a raised darker blade face, both sides."""
    p = plate(outline, "bright", depth, .002)
    o = np.array(outline)
    center = o.mean(axis=0)
    inset = center + (o - center) * [.84, .92]
    return [p, plate(inset, mat, depth + .009, .002)]

def emblem(parts, x, z, i, r=.022):
    parts.append(K.ring_tube((x, -.027, z), r, .004, METAL[i], axis="y", n=12))
    parts.append(K.gem((x, -.027, z), r * .65, GLOW[i], rot=(90, 0, 0)))

def bow(s):
    i = s["design"]
    # x,z control polygons. These produce visibly different limb sweeps and proportions.
    profiles = [
        [(0,.08),(.06,.21),(.035,.39),(-.12,.59),(-.09,.72)],
        [(0,.08),(.07,.22),(-.02,.38),(-.17,.55),(-.08,.66)],
        [(0,.08),(.085,.19),(.10,.32),(-.13,.46),(-.18,.64)],
        [(0,.08),(.12,.22),(.08,.42),(-.10,.61),(-.16,.66)],
        [(0,.08),(.02,.25),(-.06,.47),(-.16,.67),(-.12,.74)],
        [(0,.08),(.14,.20),(.12,.37),(-.035,.55),(-.16,.59)],
        [(0,.08),(.10,.22),(.02,.42),(-.16,.57),(-.13,.71)],
        [(0,.08),(.12,.25),(.04,.49),(-.14,.63),(-.12,.78)],
        [(0,.08),(.075,.24),(.035,.41),(-.10,.53),(-.17,.68)],
        [(0,.08),(.05,.20),(.035,.38),(-.02,.56),(-.04,.65)],
    ]
    profile = profiles[i]
    parts = [W.grip(-.085,.085,.026,"darkleather",8)]
    for side in [-1,1]:
        pts = [(x,0,z * side * (.84 if i == 2 and side < 0 else 1)) for x,z in profile]
        limb=smooth(pts) if i not in [8,9] else pts
        radii=[(.025+.016*math.sin(math.pi*j/(len(limb)-1))-.013*j/(len(limb)-1),.020-.011*j/(len(limb)-1)) for j in range(len(limb))]
        parts.append(K.tube(limb,radii,BODY[i],n=10))
        parts.append(line([(x,-.022,z) for x,y,z in limb],.005,METAL[i]))
        # Laminated back and small bracing bands give the limbs material depth.
        parts.append(line([(x+.014,.010,z) for x,y,z in limb],.006,METAL[i]))
        for j in [1,2,3]:
            x,y,z=pts[j]
            parts.append(K.band(z,.028,.012,METAL[i],n=10).move((x,0,0)))
        # Each family has different secondary silhouette, not just a different color.
        if i in [0,4,6]:
            for j in range(3 if i != 6 else 5):
                z = .20 + j * (.11 if i != 6 else .075)
                x = .065 - j * .035
                leaf = [(x-.02,z-.03),(x+.09,z+.045),(x+.15,z+.16),(x+.055,z+.10),(x-.03,z+.035)]
                parts += sharpened([(x0,z0*side) for x0,z0 in leaf],METAL[i],.012)
        if i == 1:
            for j in range(3):
                z=.27+j*.12
                parts.append(K.tube([(.025,0,z*side),(.15-j*.04,0,(z+.06)*side),(.17-j*.04,0,(z+.16)*side)],[.018,.011,.001],"bone",n=7))
        if i == 2:
            parts.append(K.ring_tube((.09,0,.32*side),.105,.014,"bronze",axis="y",n=18,arc=270,a0=15))
            parts.append(K.cone_spike((.16,0,.32*side),(.08,0,.40*side),.015,"bone"))
        if i == 3:
            for j in range(3):
                z=.21+j*.12
                parts += sharpened([(.025,z*side),(.16,(z+.12)*side),(.12,(z-.01)*side)],"gold",.014)
        if i in [5,7]:
            pts2=[(x+.10*math.sin(j*math.pi/4),.015,z*side) for j,(x,z) in enumerate(profile)]
            parts.append(line(smooth(pts2),.013,METAL[i]))
            for j in [1,2,3]:
                parts.append(line([pts[j],pts2[j]],.007,METAL[i]))
        if i == 8:
            for j in range(3):
                parts.append(K.crystal((.09-j*.015,0,side*(.27+j*.13)),.23-j*.02,.035,"ice",rot=(0,side*25,0)))
        if i == 9:
            for y in [-.025,.025]:
                parts.append(line([(x,y,z*side) for x,z in profile],.012,"steel"))
            parts.append(K.ring_tube((-.04,0,.62*side),.085,.013,"brass",axis="y",n=20))
            for a in range(0,360,60):
                rad=math.radians(a)
                parts.append(line([(-.04,0,.62*side),(-.04+.076*math.cos(rad),0,.62*side+.076*math.sin(rad))],.006,"steel"))
        emblem(parts,profile[1][0],side*profile[1][1],i,.018)
    # A clear, tensioned string set behind the grip, with a short nocking wrap.
    tx,tz=profile[-1]
    parts.append(line([(tx,0,tz),(-.25,0,0),(tx,0,-tz*(.84 if i==2 else 1))],.0028,"linen"))
    parts.append(line([(-.25,0,-.026),(-.25,0,.026)],.006,"redleather"))
    if i == 3:
        parts.append(K.ring_tube((.04,0,0),.115,.014,"gold",axis="y",n=24))
    if i == 9:
        parts.append(line([(-.04,.015,.62),(-.11,.015,-.62)],.0025,"steel"))
    return parts

def crossbow(s):
    i=s["design"]
    m,b=METAL[i],BODY[i]
    lengths=[.62,.79,.63,.73,.62,.70,.68,.76,.77,.73]
    tip=lengths[i]
    # Curved shoulder stock and receiver; the hand surrounds the narrow grip at origin.
    butts=[
        [(-.04,-.28),(.09,-.26),(.08,-.14),(.045,-.035)],
        [(-.035,-.34),(.035,-.36),(.065,-.21),(.04,-.02)],
        [(-.10,-.31),(.11,-.28),(.12,-.13),(.065,-.03)],
        [(-.06,-.29),(.045,-.34),(.085,-.18),(.035,-.03)],
        [(-.085,-.22),(.10,-.22),(.09,-.12),(.04,-.01)],
        [(-.06,-.32),(.10,-.28),(.06,-.23),(-.015,-.21),(.035,-.03)],
        [(-.07,-.26),(.06,-.31),(.105,-.24),(.075,-.13),(.04,-.03)],
        [(-.035,-.35),(.085,-.33),(.055,-.20),(.085,-.16),(.035,-.03)],
        [(-.07,-.35),(.09,-.32),(.125,-.20),(.075,-.12),(.055,-.03)],
        [(-.035,-.31),(.095,-.31),(.095,-.25),(.025,-.25),(.04,-.03)],
    ]
    stock=butts[i]+[(.05,tip-.11),(-.045,tip-.11),(-.038,.02),(-.07,-.12)]
    parts=[plate(stock,b,.10,.01), W.grip(-.07,.07,.03,"darkleather",7)]
    # Engraved stock edge, raised cheek plate and contrasting fastening screws.
    parts.append(line([(x,-.054,z) for x,z in butts[i]],.006,m))
    parts.append(plate([(-.036,-.20),(.038,-.19),(.036,-.10),(-.030,-.09)],m,.012,.003).move((0,-.056,0)))
    for z in [-.15,.08,.18,.28]:
        for x in [-.03,.03]:
            parts.append(K.gem((x,-.065,z),.009,"bright",rot=(90,0,0)))
    for z in [.27,.34,.41]:
        parts.append(K.box(.045,.012,.011,(0,-.072,z),m,.003))
    parts.append(K.box(.12,.115,.17,(0,0,.13),m,.015))
    # Paired rails leave a visible bolt channel.
    for x in [-.029,.029]:
        parts.append(K.box(.014,.026,tip-.16,(x,-.065,(tip+.14)/2),"steel",.004))
    parts.append(line([(0,-.08,.20),(0,-.08,tip+.075)],.007,"ash"))
    parts.append(K.cone_spike((0,-.08,tip+.05),(0,-.08,tip+.13),.017,"bright"))
    for x in [-1,1]:
        parts.append(plate([(0,.23),(x*.024,.18),(x*.024,.26)],"crimson",.01).move((0,-.084,0)))
    span=[.35,.29,.40,.33,.30,.46,.38,.36,.42,.33][i]
    for side in [-1,1]:
        pts=[(0,0,tip-.17),(side*span*.42,0,tip-.11),(side*span*.8,0,tip-.18),(side*span,0,tip-.27)]
        if i in [1,5,7]: pts[-1]=(side*span,0,tip-.08)
        cp=smooth(pts) if i in [0,1,2,5,8] else pts
        parts.append(K.tube(cp,[(.027-.014*j/(len(cp)-1),.022-.010*j/(len(cp)-1)) for j in range(len(cp))],m,n=8))
        parts.append(line([pts[-1],(0,-.06,.19)],.0035,"linen"))
        # Limb plates, screws, mechanical catches.
        for j in [1,2]:
            x,y,z=pts[j]
            parts.append(K.gem((x,-.03,z),.009,"bright",rot=(90,0,0)))
        if i in [2,8]:
            parts.append(K.tube([(side*.16,0,tip-.14),(side*.26,0,tip+.04),(side*.18,0,tip+.12)],[.025,.014,.001],"bone",n=8))
        if i == 3:
            parts.append(K.box(.015,.05,.43,(side*.075,0,.48),m,.004))
        if i == 5:
            for j in range(3):
                x=side*(.11+j*.085)
                parts+=sharpened([(x,tip-.20),(x+side*.13,tip+.02),(x+side*.075,tip-.22)],m,.012)
        if i == 7:
            for j in range(2):
                parts.append(K.crystal((side*(.18+j*.10),0,tip-.10),.22,.026,"ice",rot=(0,side*35,0)))
        if i == 9:
            parts.append(K.ring_tube((side*span,0,tip-.22),.074,.011,"brass",axis="y",n=20))
            parts.append(line([(side*span-.06,0,tip-.22),(side*span+.06,0,tip-.22)],.006,"steel"))
    parts.append(K.ring_tube((0,0,tip+.03),.076,.012,m,axis="y",n=14,arc=280,a0=-50))
    # Open trigger guard with visible trigger.
    parts.append(K.ring_tube((.045,0,.04),.068,.007,m,axis="y",n=16,arc=260,a0=220))
    parts.append(line([(.05,0,.085),(.075,0,.04)],.009,"steel"))
    if i in [1,4]:
        parts.append(line([(.05,.055,.19),(.09,.055,.45),(.025,.055,.61)],.014,m,"loading_lever"))
    if i in [5,9]:
        parts.append(line([(-.025,0,-.04),(-.10,0,-.19),(-.08,0,-.31),(.07,0,-.29)],.016,m,"open_stock_frame"))
    if i == 4:
        parts.append(K.box(.19,.085,.23,(0,-.115,.35),b,.012))
        for x in [-.065,-.0325,0,.0325,.065]:
            parts.append(line([(x,-.165,.27),(x,-.165,.57)],.008,"ash"))
            parts.append(K.cone_spike((x,-.165,.56),(x,-.165,.62),.012,"steel"))
    if i in [6,9]:
        for radius in ([.13] if i==6 else [.10,.065]):
            parts.append(K.ring_tube((0,-.08,.36),radius,.009,m,axis="y",n=24))
        for a in range(0,360,45):
            rad=math.radians(a)
            parts.append(line([(0,-.08,.36),(.12*math.cos(rad),-.08,.36+.12*math.sin(rad))],.004,m))
    if i==8:
        for x in [-.06,.06]:
            for z in [.56,.63,.70]:
                parts.append(K.cone_spike((x,-.035,z),(x*.4,-.075,z+.02),.012,"bone"))
    emblem(parts,0,.13,i,.03)
    return parts

def edged(s):
    i=s["design"]; family=s["family"]
    dagger=family=="dagger"
    L=(.30 if dagger else .81)*[1,1.05,.92,1.10,.98,1.04,1,.92,1.12,1.08][i]
    width=(.055 if dagger else .075)
    # Normalized, explicit blade outlines. Open forks are true silhouette gaps.
    profiles=[
        [(-.30,0),(-.48,.66),(-.78,.90),(-.25,1.05),(.18,.90),(.40,.32),(.30,0)],
        [(-.25,0),(-.50,.45),(-.80,.78),(-.45,1.0),(.10,.83),(.36,.28),(.28,0)],
        [(-.3,0),(-.75,.35),(-.82,.60),(0,1),(.82,.60),(.75,.35),(.3,0)],
        [(-.3,0),(-.32,.52),(-.9,.63),(-.7,.93),(-.45,.76),(-.2,.7),(0,1.08),(.2,.7),(.45,.76),(.7,.93),(.9,.63),(.32,.52),(.3,0)],
        [(-.28,0),(-.95,.45),(-.92,.86),(-.15,1.05),(-.30,.73),(.18,.53),(.43,.12),(.3,0)],
        [(-.3,0),(-.65,.2),(-.15,.4),(-.70,.6),(-.18,.78),(0,1.06),(.30,.8),(-.04,.60),(.43,.4),(-.02,.2),(.3,0)],
        [(-.4,0),(-.40,.14),(-.75,.21),(-.4,.25),(-.72,.34),(-.4,.4),(-.72,.49),(-.4,.55),(-.68,.63),(-.4,.69),(-.35,.86),(.28,1),(.50,.28),(.38,0)],
        [(-.3,0),(-.9,.35),(-1.1,.6),(-.65,.82),(0,1.02),(.60,.88),(.92,.6),(.7,.34),(.3,0)],
        [(-.3,0),(-.58,.45),(-.43,1.04),(-.06,.57),(0,.32),(.06,.57),(.43,1.04),(.58,.45),(.3,0)],
        [(-.25,0),(-.23,.64),(-.10,.91),(0,1.1),(.1,.91),(.23,.64),(.25,0)],
    ]
    if not dagger:
        if i==0: profiles[i]=[(-.22,0),(-.20,.78),(0,1.1),(.20,.78),(.22,0)]
        if i==3:
            profiles[i]=[(math.sin(t*math.pi*7)*.23-.4,t) for t in np.linspace(0,.9,18)]+[(0,1.08)]+[(math.sin(t*math.pi*7)*.23+.4,t) for t in np.linspace(.9,0,18)]
        if i==5: profiles[i]=profiles[8]
        if i==7: profiles[i]=[(-.4,0),(-.5,.30),(-1,.68),(-1.6,1.03),(-.45,.86),(.35,.54),(.38,0)]
        if i==8: profiles[i]=[(-.6,0),(-.7,.72),(0,1.06),(.7,.72),(.6,0)]
    outline=[(x*width,.10+z*L) for x,z in profiles[i]]
    parts=sharpened(outline,METAL[i],.018 if dagger else .022)
    parts.append(W.grip(-.09,.078,.017 if dagger else .021,["leather","navy","forest","redleather","darkleather"][i%5],8))
    parts.append(W.pommel(-.12,.026 if dagger else .033,METAL[i],["spike","ring","disc","round"][i%4]))
    half=.082 if dagger else .14
    if i in [0,2,3,5,8]:
        for side in [-1,1]:
            guard=[(0,.085),(side*half*.6,.05),(side*half,.14),(side*half*.75,.095),(side*half*.45,.12),(0,.12)]
            parts+=sharpened(guard,METAL[i],.018)
    elif i==1 or (i==7 and not dagger):
        parts.append(W.crossguard(.085,half,METAL[i],curve=.035))
        for y in [-.022,.022]:
            parts.append(line([(half*.8,y,.1),(half,y,-.01),(.07,y,-.11),(0,y,-.12)],.008,METAL[i]))
    elif i==4:
        parts.append(K.ring_tube((0,0,.085),half,.01,METAL[i],axis="y",n=24,arc=230,a0=-25))
    elif i==9:
        parts.append(K.ring_tube((0,0,.085),half*.68,.009,METAL[i],axis="y",n=20))
        for side in [-1,1]:
            parts.append(K.cone_spike((side*half*.6,0,.085),(side*half*1.3,0,.11),.017,METAL[i]))
        parts.append(K.ring_tube((0,0,-.145),.043,.009,METAL[i],axis="y",n=16))
    else:
        parts.append(W.crossguard(.085,half,METAL[i],curve=-.04,flare=1.5))
    if i==7 and dagger:
        for side in [-1,1]:
            for j in range(3):
                parts.append(plate([(0,.09),(side*(.06+j*.02),.055-j*.018),(side*(.065+j*.02),.09)],"copper",.014))
    emblem(parts,0,.09,i,.018 if dagger else .023)
    # Geometric runes, small enough to preserve the blade but readable close-up.
    if i not in [3,5,8]:
        for j in range(3):
            z=.16+L*(.15+j*.14)
            parts.append(line([(-.008,-.018,z+.018),(0,-.018,z),(.009,-.018,z+.018)],.0025,GLOW[i]))
    return parts

def axe(s):
    i=s["design"]; m=METAL[i]
    # Head polygons use a unit grid, with genuinely different gaps, edges and hooks.
    profiles=[
        [(0,0),(.55,.20),(1.0,.60),(.8,.05),(.55,-.12),(.2,-.09)],
        [(0,.08),(.4,.28),(.85,.5),(1,.12),(.92,-.75),(.57,-.85),(.62,-.38),(.3,-.12),(0,-.12)],
        [(0,.08),(.45,.38),(.85,.8),(1.05,.36),(1.10,-.10),(.92,-.67),(.58,-.78),(.78,-.33),(.75,.20),(.4,.1),(0,-.1)],
        [(0,.14),(.22,.64),(1.0,.68),(1.08,.45),(1.08,-.44),(.8,-.48),(.36,-.23),(0,-.12)],
        [(0,.08),(.25,.35),(.63,.66),(.97,.50),(.75,.12),(.30,-.2),(0,-.08)],
        [(0,.12),(.38,.45),(.82,.75),(.69,.38),(.43,.13),(.85,.3),(1.05,.13),(.72,-.04),(.95,-.25),(.8,-.60),(.55,-.35),(.2,-.12),(0,-.12)],
        [(0,.12),(.25,.50),(.6,.65),(.95,.45),(1.1,.05),(.95,-.40),(.6,-.60),(.25,-.45),(0,-.12)],
        [(0,.13),(.55,.27),(1.15,.70),(.97,.12),(.40,-.10),(0,-.12)],
        [(0,.05),(.28,.58),(.7,.78),(1.05,.45),(1.08,-.42),(.85,-.61),(.58,-.48),(.75,-.3),(.84,.3),(.65,.50),(.47,.34),(.27,-.12),(0,-.12)],
        [(0,.12),(.46,.62),(.8,.82),(.61,.40),(1.1,.46),(.76,-.02),(.94,-.35),(.45,-.22),(.16,-.08),(0,-.12)],
    ]
    scale=.30; z=.51
    parts=[W.haft(-.18,.71,.022,BODY[i]),W.grip(-.10,.12,.024,"darkleather",8)]
    head=[(x*scale,z+y*scale) for x,y in profiles[i]]
    parts+=sharpened(head,m,.035)
    if i==4:
        parts+=sharpened([(-x,z0+.04) for x,z0 in head],m,.035)
    else:
        parts.append(K.cone_spike((-.015,0,z),(-.17 if i in [0,7] else -.10,0,z+.07),.025,m))
    for zz in [.35,.39,.52,.62]: parts.append(K.band(zz,.029,.026,m,n=10))
    if i in [3,6,9]:
        for j in range(4):
            zz=.42+j*.08
            parts.append(K.cone_spike((.27,0,zz),(.315+(j%2)*.02,0,zz+.03),.012,m))
    if i==6:
        parts.append(K.ring_tube((.18,-.026,z),.09,.008,"gold",axis="y",n=20))
    if i==7:
        parts.append(K.crystal((.15,0,z+.08),.31,.025,"ice",rot=(0,53,0)))
    if i in [1,5,8]:
        parts.append(line([(0,0,.21),(-.07,0,.37),(-.05,0,.56)],.014,m))
    emblem(parts,.055,z,i,.034)
    parts.append(W.pommel(-.20,.027,m,"ring" if i%2 else "spike"))
    return parts

SPECS = {}
for row in MANIFEST:
    family=row["weapon_type"]
    fn={"bow":bow,"crossbow":crossbow,"dagger":edged,"sword":edged,"axe":axe}[family]
    SPECS[row["id"]]=(fn,dict(design=row["design"],family=family))

# Existing bow IDs keep their stats, saves and loot rules but receive real silhouettes.
OLD_BOWS=["hunters_bow","composite_bow","warden_longbow","shortbow","recurve_bow","hornbow","siege_greatbow","galewing_bow","fowling_bow","yew_longbow","thornback_bow","frostwing_bow","stormstring_greatbow"]
for j,iid in enumerate(OLD_BOWS): SPECS[iid]=(bow,dict(design=j%10,family="bow"))
for j,(iid,(builder,spec)) in enumerate(json.loads((Path(__file__).parent / "depth_specs.json").read_text()).items()):
    if builder == "bow":
        SPECS[iid]=(bow,dict(design=j%10,family="bow"))
