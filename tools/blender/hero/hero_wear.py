"""bh-023: the hero's worn equipment -> game/assets/characters/hero/wear/<item id>.glb + manifest.json.

  blender -b --factory-startup --python tools/blender/hero/hero_wear.py -- all | <ids...> | preview [ids or a+b+c outfits]

Every wearable base item has an entry (its own id); ids starting with "_" are the shared pieces the game adds itself:
the plain under-layers worn beneath boss regalia, and the shoes and breeches of a clothed hero without boots or
leggings. The item modules (hero_wear_torso.py: armour and inner garments; hero_wear_legs.py: leggings and the shared
legwear; hero_wear_ends.py: helms, gloves, boots, jewellery) register the rest.
"""
import importlib
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import hero_wear_kit as WK  # noqa: E402
from hero_wear_kit import K, M, item, pal, shell, attach  # noqa: E402

TINT = "raw:BH_Cloth_Primary"            # takes the colour the game gives the wearer (a boss set's cloth)


# ---- shared pieces ----------------------------------------------------------------------------------------------------
@item("_under_body", hide={"z": [0.875, 1.49], "sleeve": [0.23, 0.71]})
def under_body():
    """Trunk and arms (bh-024: the legs have their own under-layer, hero_wear_legs._under_legs)."""
    def sel(V):
        return WK.either(WK.trunk(V, 0.85, 1.53), WK.arms(V, 0.19, 0.735))
    return [shell(sel, 0.005, TINT, "suit")]


@item("_under_hands", hide={"glove": [0.735, 1.0]}, sides=True)
def under_hands():
    return [shell(lambda V: WK.hand(V, 1.0, 0.705), 0.004, TINT, "glove")]


@item("_under_feet", hide={"boot": [-1.0, 0.135]}, sides=True)
def under_feet():
    return [shell(lambda V: WK.foot(V, 1.0, 0.17), 0.008, TINT, "sock", relax=3)]


@item("_shoes", hide={"boot": [-1.0, 0.105]}, sides=True)
def shoes():
    """Plain turnshoes: what a clothed hero wears when no boots are equipped."""
    upper = shell(lambda V: WK.foot(V, 1.0, 0.145), 0.010, pal("leather"), "shoe", relax=4)
    cx, cy, rx, ry = WK.leg_section(0.135)
    cuff = K.ring_tube((cx, cy, 0.137), 1.0, 0.009, pal("darkleather"), axis="z", n=18).scale((rx + 0.014, ry + 0.014, 1), (cx, cy, 0.137))
    return [upper] + attach(cuff, bones=["shin.L", "foot.L"], keys=False)


# ---- item modules -----------------------------------------------------------------------------------------------------
for _m in ("hero_wear_torso", "hero_wear_ends", "hero_wear_legs", "hero_wear_special"):
    if os.path.exists(os.path.join(HERE, _m + ".py")):
        importlib.import_module(_m)

# items without a model of their own borrow one by kind: "category/weight/class" -> "category/weight" -> "category"
FALLBACK = {
    "helm/heavy": "iron_helm", "helm/cloth": "linen_hood", "helm": "iron_helm",
    "armor/heavy": "iron_hauberk", "armor/cloth": "apprentice_robe", "armor": "iron_hauberk",
    "armor/cloth/ranger": "traveler_coat", "armor/cloth/shadowblade": "traveler_coat",
    "inner_garment/heavy": "padded_gambeson", "inner_garment/cloth": "silk_undershirt", "inner_garment": "padded_gambeson",
    "gloves/heavy": "iron_gauntlet", "gloves/cloth": "silk_glove", "gloves": "silk_glove",
    "boots/heavy": "iron_sabaton", "boots/cloth": "soft_boot", "boots": "soft_boot",
    "leggings/heavy": "iron_cuisses", "leggings/cloth": "linen_trousers", "leggings": "linen_trousers",
    "leggings/cloth/ranger": "hide_leggings", "leggings/cloth/shadowblade": "cutpurse_trousers",
}


# ---- preview ----------------------------------------------------------------------------------------------------------
TORSO_IDS = set()
BOOT_IDS = set()
try:
    import hero_wear_torso as _T
    import hero_wear_ends as _E
    TORSO_IDS = {k for k, v in WK.REGISTRY.items() if v["fn"].__module__ == _T.__name__}
    BOOT_IDS = set(_E.BOOTS)
except Exception:  # noqa: BLE001
    pass

def _hide_body(ob, V, ids):
    """Approximate the skin shader's cut-outs with a mask modifier, so previews show what the game shows."""
    ax = np.abs(V[:, 0])
    hidden = np.zeros(len(V), bool)
    for i in ids:
        h = WK.REGISTRY[i]["hide"]
        for k in ("z", "z2"):
            if k in h:
                hidden |= (ax < 0.27) & (V[:, 2] > h[k][0]) & (V[:, 2] < h[k][1])
        if "sleeve" in h:
            hidden |= (ax > h["sleeve"][0]) & (ax < h["sleeve"][1])
        if "glove" in h:
            hidden |= (ax > h["glove"][0]) & (ax < h["glove"][1])
        if "boot" in h:
            hidden |= (ax < 0.27) & (V[:, 2] > h["boot"][0]) & (V[:, 2] < h["boot"][1])
    g = ob.vertex_groups.get("hidden") or ob.vertex_groups.new(name="hidden")
    g.remove(list(range(len(V))))
    g.add([int(i) for i in np.nonzero(hidden)[0]], 1.0, "REPLACE")
    mod = ob.modifiers.get("HideSkin") or ob.modifiers.new("HideSkin", "MASK")
    mod.vertex_group = "hidden"
    mod.invert_vertex_group = True


def preview(outfits, clips=("run", "sword_2", "cast_heavy")):
    """Renders of each outfit ("a+b+c" = several pieces together) on the hero: rest pose front / back / side and a
    few library poses -> work/lemondev/bh-023/scratch/wear/<outfit>_*.png
    BH_WEAR_SHOTS=front,side,back,head,legs limits the rest-pose shots and BH_WEAR_CLIPS=run,... the poses (empty: none)."""
    shots = [x for x in os.environ.get("BH_WEAR_SHOTS", "front,back,side,head").split(",") if x]
    if "BH_WEAR_CLIPS" in os.environ:
        clips = tuple(x for x in os.environ["BH_WEAR_CLIPS"].split(",") if x)
    import bpy
    import bh_anim as A
    import bh_library as L
    import hero_body as HB
    r = HB.build_body()
    body, arm, rig = r["ob"], r["arm"], r["rig"]
    HB._preview_material(body)
    shot = HB._stage()
    out = os.path.join(WK.SCRATCH, "wear")
    os.makedirs(out, exist_ok=True)
    lib = {a.name: a for a in L.library()}
    acts = {c: A.bake_action(arm, rig, lib[c]) for c in clips}
    for outfit in outfits:
        ids = outfit.split("+")
        obs = []
        for i in ids:
            obs += WK.build_item(i, arm)
        # what the game leaves off (HeroWear.plan): a pair of leggings' outer groups under what is worn over them
        torso = [i for i in ids if WK.REGISTRY[i].get("skirt") is not None or i in TORSO_IDS]
        skirt = min([WK.REGISTRY[i].get("skirt") or 9.0 for i in torso] or [9.0])
        booted = any(i in BOOT_IDS for i in ids)
        skip = (["waist"] if torso else []) + (["hip"] if skirt < 0.80 else []) + (["knee"] if skirt < 0.45 else []) \
            + (["ankle_L", "ankle_R"] if booted else [])
        for o in list(obs):
            if o.name.split(".")[0] in ["wear_" + g for g in skip]:
                obs.remove(o)
                bpy.data.objects.remove(o)
        _hide_body(body, r["V"], ids)
        if arm.animation_data:
            arm.animation_data.action = None
        for pb in arm.pose.bones:
            pb.rotation_quaternion = (1, 0, 0, 0)
            pb.location = (0, 0, 0)
        tag = outfit.replace("+", "__")
        views = {"front": ((0, -6, 0.95), (0, 0, 0.95), 2.0, (700, 900)), "back": ((0, 6, 0.95), (0, 0, 0.95), 2.0, (700, 900)),
                 "side": ((6, -0.5, 0.95), (0, 0, 0.95), 2.0, (500, 900)), "head": ((2.2, -4.5, 1.85), (0, -0.03, 1.66), 0.62, (640, 640)),
                 "legs": ((2.6, -5.2, 0.62), (0, 0, 0.58), 1.25, (700, 800)),
                 "hips": ((0.8, -5.5, 0.95), (0, 0, 0.92), 0.5, (900, 900)), "legs_back": ((-2.6, 5.2, 0.62), (0, 0, 0.58), 1.25, (700, 800))}
        for v in shots:
            loc, tgt, sc, res = views[v]
            shot(os.path.join(out, "%s_%s.png" % (tag, v)), loc, tgt, sc, res)
        for c in clips:
            A.assign_action(arm, acts[c])
            f = lib[c].length // 2
            bpy.context.scene.frame_set(f)
            shot(os.path.join(out, "%s_%s.png" % (tag, c)), (3.2, -5.0, 1.5), (0, 0, 0.95), 2.3, (700, 800))
        for o in obs:
            bpy.data.objects.remove(o)
        print("[wear] preview", outfit)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if argv and argv[0] == "preview":
        preview(argv[1:] or list(WK.REGISTRY))
        return
    ids = list(WK.REGISTRY) if (not argv or "all" in argv) else [a for a in argv if a in WK.REGISTRY]
    missing = [a for a in argv if a != "all" and a not in WK.REGISTRY]
    if missing:
        print("[wear] unknown ids:", missing)
    rep = WK.export_items(ids)
    WK.write_manifest(ids, FALLBACK)
    print("[wear] %d pieces, %d triangles in all" % (len(rep), sum(rep.values())))


if __name__ == "__main__":
    main()
