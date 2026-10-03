"""bh-034: the four Ascendant tiers above Aether — Cosmic, Divine, Eternal, Primordial — as forty regalia collections.

Each tier has ten collections (three knight, three mage, two ranger, two shadowblade). Every collection is one set of
nine pieces: helm, armour, inner garment, leggings, gauntlets, boots, a jewel, a shield and its signature weapon,
so every tier has ten pieces of every equipment type (game/src/data/data_ascendant.gd keeps the same ids).

The armour is built by the bh-022 regalia builders (boss_regalia.py: fitted to the hero skeleton, wear() attaches
it) from each collection's own style (helm, torso, skirt, motif, cape) and palette, then a tier ornament layer is
added in model space: Cosmic orbit rings and starlit crests, Divine halos and wings, Eternal clock-dial crowns and
hourglasses, Primordial obsidian shards and molten veins. The weapons use the parametric weapon builders
(item_weapons.py, artisan_weapons.py) in the collection's palette with the same tier ornaments.

Ids: asc_<collection>_<piece> (piece: helm armor inner leggings gloves boots accessory shield weapon). Gloves and
boots also export a right-hand/right-foot model <id>_R.glb (the left one is <id>.glb, also the dropped model).
Materials are "<legend base>__it_asc_<collection>_<role>": MaterialLibrary lays the legend texture sets on them.

  blender -b --factory-startup --python tools/blender/items/ascendant_regalia.py -- [models] [icons] [tier...] [collection ids...]
"""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import item_kit as K  # noqa: E402
from item_kit import M, Rx, Ry, Rz  # noqa: E402
import boss_regalia as RG  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
ITEMS_DIR = os.path.join(ROOT, "game", "assets", "items")

TIERS = ["cosmic", "divine", "eternal", "primordial"]


def _t(tier, cls, weapon, helm, torso, skirt, motif, cape, shield, jewel, plate, trim, cloth, leather, glow, horn=None, plate_base=None):
    """One collection's style. plate/trim/cloth/leather/horn: sRGB hex; glow: emission hex."""
    pb = plate_base or {"cosmic": "BH_DarkSteel", "divine": "BH_HolyPlate", "eternal": "BH_Steel", "primordial": "BH_DragonPlate"}[tier]
    tb = {"cosmic": "BH_Silver", "divine": "BH_Gold", "eternal": "BH_Gold", "primordial": "BH_Crimson"}[tier]
    hb = "BH_Horn" if tier == "primordial" else "BH_Bone"
    return dict(tier=tier, cls=cls, weapon=weapon, helm=helm, torso=torso, skirt=skirt, motif=motif, cape=cape, shield_shape=shield,
                jewel=jewel, plate=(pb, plate, 0.9, 0.3), trim=(tb, trim, 1.0, 0.24), cloth=("BH_Cloth_Primary", cloth, 0.0, 0.88),
                leather=("BH_Leather", leather, 0.0, 0.66), horn=(hb, horn or trim, 0.0, 0.45), glow=glow)


C, D, E, P = TIERS
# id: (tier, class, weapon, helm, torso, skirt, motif, cape, shield, jewel, plate, trim, cloth, leather, glow[, horn])
COLLECTIONS = {
    # ---- Cosmic: night-sky steel, starlight silver, nebula cloth --------------------------------------------------
    "starfall_vanguard": _t(C, "knight", "sword", "great", "plate", "tassets", "star", "long", "heater", "ring",
                            "2a2d5c", "c9d2ff", "1b1840", "1a1830", "a493ff"),
    "nebula_warlord": _t(C, "knight", "greatsword", "great", "plate", "tassets", "crescent", "tattered", "tower", "ring",
                         "3a2562", "dcc8ff", "24123e", "1e1428", "c58cff"),
    "orbit_sentinel": _t(C, "knight", "spear", "sallet", "plate", "tassets", "orbs", "split", "kite", "ring",
                         "22304e", "b8c8ea", "141e38", "1a2030", "8fb4ff"),
    "astral_magister": _t(C, "mage", "staff", "hood", "mantle", "robe", "star", "long", "round", "ring",
                          "b4bce6", "eef0ff", "221a4c", "1c1830", "9d8cff", plate_base="BH_Silver"),
    "voidweaver": _t(C, "mage", "wand", "crown", "mantle", "robe", "crescent", "tattered", "round", "pendant",
                     "5a4e98", "d4ccff", "100d26", "120f1e", "b07cff", plate_base="BH_Silver"),
    "eclipse_oracle": _t(C, "mage", "staff", "mitre", "mantle", "robe", "orbs", "fur", "kite", "pendant",
                         "403470", "e6dcff", "2a2062", "1c1830", "7f9cff", plate_base="BH_Silver"),
    "comet_strider": _t(C, "ranger", "bow", "sallet", "brigandine", "leather", "feather", "split", "round", "pendant",
                        "384878", "d6e0ff", "1a2448", "222838", "8ad0ff"),
    "meteor_marksman": _t(C, "ranger", "crossbow", "wrap", "brigandine", "scarves", "bolt", "scarf", "round", "brooch",
                          "2e3458", "c0c8f0", "3a3266", "2a2638", "a0a8ff"),
    "nightsky_reaver": _t(C, "shadowblade", "dagger", "hood", "harness", "leather", "crescent", "tattered", "round", "brooch",
                          "2a2448", "c4c0ec", "16122c", "18142a", "b494ff"),
    "starless_stalker": _t(C, "shadowblade", "claw", "cobra", "harness", "scarves", "serpent", "scarf", "round", "brooch",
                           "1c1c38", "a8b0e0", "0e0e22", "14142a", "6f8cff"),
    # ---- Divine: white-gold plate, ivory and sky cloth, sunlight -----------------------------------------------------
    "seraph_paladin": _t(D, "knight", "sword", "great", "plate", "tassets", "sun", "wings", "heater", "ring",
                         "f0ead8", "f2c868", "e8e2d0", "4a3626", "ffe9a0"),
    "archon_crusader": _t(D, "knight", "greataxe", "great", "plate", "tassets", "star", "long", "tower", "ring",
                          "e4dcc4", "e8b858", "2a4a7a", "3e2e20", "fff0b8"),
    "dawnward_templar": _t(D, "knight", "club", "sallet", "plate", "tassets", "feather", "long", "kite", "ring",
                           "ece6d6", "dcae5a", "8a2a2a", "3a2a20", "ffd890"),
    "hierophant": _t(D, "mage", "staff", "mitre", "mantle", "robe", "sun", "long", "round", "ring",
                     "f4e2b0", "f8d478", "f0ece0", "5a4630", "fff2c0", plate_base="BH_Gold"),
    "lightbinder": _t(D, "mage", "wand", "crown", "mantle", "robe", "star", "wings", "round", "pendant",
                      "e8e0c8", "f4cc70", "6a8cc8", "40342a", "ffeaa0", plate_base="BH_Gold"),
    "cantor_of_dawn": _t(D, "mage", "staff", "hood", "mantle", "robe", "feather", "long", "kite", "pendant",
                         "dcd2b8", "eac264", "c8b48a", "4a3a2a", "ffe2a8", plate_base="BH_Gold"),
    "zenith_archer": _t(D, "ranger", "bow", "circlet", "brigandine", "leaves", "feather", "wings", "round", "pendant",
                        "e6dec8", "e8c070", "4a7a5a", "4a3a26", "fff0c0"),
    "verdict_arbalist": _t(D, "ranger", "crossbow", "sallet", "brigandine", "leather", "bolt", "split", "round", "brooch",
                           "d8d2c0", "dcb060", "3a5a8a", "3a2c20", "fff4c8"),
    "sanctified_shade": _t(D, "shadowblade", "dagger", "hood", "harness", "scarves", "tear", "scarf", "round", "brooch",
                           "d0ccc0", "e0c078", "5a5a78", "2e2a30", "fff0d0"),
    "penitent_talon": _t(D, "shadowblade", "claw", "circlet", "harness", "leather", "feather", "split", "round", "brooch",
                         "c8c0ac", "d8a850", "6a2a2a", "2a2220", "ffd8a0"),
    # ---- Eternal: rose-gold and pearl over wine and deep teal, the hours ----------------------------------------
    "chronoguard": _t(E, "knight", "greatsword", "great", "plate", "tassets", "orbs", "long", "tower", "ring",
                      "8e6a68", "f0c8a8", "4a1630", "2e1a20", "ff7bb8"),
    "everlasting_bulwark": _t(E, "knight", "sword", "great", "plate", "tassets", "snow", "fur", "heater", "ring",
                              "6c8088", "e8c4a8", "1e3a44", "2a2226", "8ef0e0"),
    "aeonbreaker": _t(E, "knight", "axe", "sallet", "plate", "tassets", "shard", "tattered", "kite", "ring",
                      "6e5260", "e2b8a0", "3a1226", "261418", "ff8fc8"),
    "timeweaver": _t(E, "mage", "staff", "crown", "mantle", "robe", "orbs", "long", "round", "ring",
                     "b89c98", "f4d0b0", "3a1840", "2a1e24", "ff9ad0", plate_base="BH_Silver"),
    "hourglass_sage": _t(E, "mage", "wand", "hood", "mantle", "robe", "tear", "long", "round", "pendant",
                         "8ea4a4", "eccaa8", "1a3a40", "22201e", "9cf6e6", plate_base="BH_Silver"),
    "undying_seer": _t(E, "mage", "staff", "mitre", "mantle", "robe", "crescent", "tattered", "kite", "pendant",
                       "8c7484", "e4c0a8", "50183a", "2a1820", "ffa6d6", plate_base="BH_Silver"),
    "evertide_hunter": _t(E, "ranger", "bow", "circlet", "brigandine", "leaves", "leaf", "wings", "round", "pendant",
                          "6e8c86", "e8c8a8", "1e4a48", "2a2a22", "9af0e4"),
    "endless_volley": _t(E, "ranger", "crossbow", "wrap", "brigandine", "scarves", "star", "scarf", "round", "brooch",
                         "8a6a70", "e8c0a0", "5a2440", "30222a", "ff86c0"),
    "stillhour_assassin": _t(E, "shadowblade", "dagger", "hood", "harness", "leather", "crescent", "split", "round", "brooch",
                             "6a6078", "dcc0a8", "2a1a34", "1e1820", "e8a8ff"),
    "ouroboros_fang": _t(E, "shadowblade", "claw", "cobra", "harness", "scarves", "serpent", "tattered", "round", "brooch",
                         "587068", "e0bc98", "143430", "1a2420", "8cffd8"),
    # ---- Primordial: obsidian and old bone, cracked with living fire ---------------------------------------------
    "worldforger": _t(P, "knight", "greatsword", "great", "plate", "tassets", "dragon", "tattered", "tower", "ring",
                      "2a1c1c", "c86a38", "3a0e0c", "1e1210", "ff4a1c", "1c1414"),
    "titanblood_champion": _t(P, "knight", "sword", "great", "plate", "tassets", "flame", "long", "heater", "ring",
                              "3a1a16", "d08040", "5a1010", "24140e", "ff5a24", "201614"),
    "firstflame_warlord": _t(P, "knight", "greataxe", "sallet", "plate", "tassets", "shard", "fur", "kite", "ring",
                             "241a1a", "b85a30", "2a1410", "1a1210", "ff3a12", "2a2220"),
    "ashborn_archmage": _t(P, "mage", "staff", "mitre", "mantle", "robe", "flame", "tattered", "round", "ring",
                           "4a3a34", "d88a48", "2e1c1a", "22160e", "ff6a2a", "d8ccb8", plate_base="BH_DarkSteel"),
    "primeval_shaman": _t(P, "mage", "wand", "hood", "mantle", "robe", "antler", "fur", "round", "pendant",
                          "5a4234", "c89058", "3e2a1c", "2a1c12", "ffa040", "e0d4bc", plate_base="BH_DarkSteel"),
    "magma_oracle": _t(P, "mage", "staff", "crown", "mantle", "robe", "shard", "long", "kite", "pendant",
                       "2c2222", "e07a3a", "4a1a14", "201410", "ff4416", "1e1818", plate_base="BH_DarkSteel"),
    "wildroot_hunter": _t(P, "ranger", "bow", "circlet", "brigandine", "leaves", "antler", "split", "round", "pendant",
                          "3a3022", "b88a50", "2e3a1c", "2a2016", "ff8a2a", "d8ccb0"),
    "cinderbolt_ballista": _t(P, "ranger", "crossbow", "sallet", "brigandine", "leather", "dragon", "split", "round", "brooch",
                              "2e2420", "c47040", "3a1a12", "1e140e", "ff5420", "241c18"),
    "abyssal_fang": _t(P, "shadowblade", "dagger", "cobra", "harness", "leather", "serpent", "tattered", "round", "brooch",
                       "1e1818", "b0603a", "1a0c0c", "140c0a", "ff3020", "1a1414"),
    "elder_wyrm_talon": _t(P, "shadowblade", "claw", "hood", "harness", "scarves", "dragon", "scarf", "round", "brooch",
                           "302018", "c87848", "3a1612", "1e120c", "ff6424", "2a201a"),
}
ORDER = list(COLLECTIONS.keys())
PIECES = ["helm", "armor", "inner", "leggings", "gloves", "boots", "accessory", "shield", "weapon"]
# piece -> regalia slot that builds it (the jewel's slot depends on its kind)
PIECE_SLOT = {"helm": "helm", "armor": "armor", "inner": "inner_garment", "leggings": "leggings", "gloves": "gloves_1",
              "boots": "boots_1", "shield": "sub_weapon"}
JEWEL_SLOT = {"ring": "accessory_1", "pendant": "accessory_3", "brooch": "accessory_4"}

for _sid, _s in COLLECTIONS.items():
    RG.SETS[_sid] = _s
    RG.SHIELDED[_sid] = _s["shield_shape"]


def srgb(h):
    return RG.srgb(h)


def palette(sid):
    """The regalia palette (boss_regalia.palette under asc_ keys) plus this collection's weapon roles."""
    s = COLLECTIONS[sid]
    keys = {}
    for role in ("plate", "trim", "cloth", "leather", "horn"):
        base, hx, met, rough = s[role]
        k = "asc_%s_%s" % (sid, role)
        K.MAT[k] = (base, srgb(hx), met, rough, None, 0)
        keys[role] = k
    k = "asc_%s_mail" % sid
    K.MAT[k] = ("BH_Mail", srgb("8a8c90"), 1.0, 0.45, None, 0)
    keys["mail"] = k
    k = "asc_%s_dark" % sid
    K.MAT[k] = ("BH_Leather", srgb("141214"), 0.0, 0.8, None, 0)
    keys["dark"] = k
    g = srgb(s["glow"])
    k = "asc_%s_glow" % sid
    K.MAT[k] = ("BH_Emissive", g, 0.0, 0.25, g, 2.6)
    keys["glow"] = k
    k = "asc_%s_gem" % sid
    K.MAT[k] = ("BH_Gem", tuple(c * 0.7 for c in g), 0.0, 0.06, g, 1.4)
    keys["gem"] = k
    return keys


def piece_slot(sid, piece):
    if piece == "accessory":
        return JEWEL_SLOT[COLLECTIONS[sid]["jewel"]]
    return PIECE_SLOT.get(piece, "main_weapon")


def item_id(sid, piece):
    return "asc_%s_%s" % (sid, piece)


# ------------------------------------------------------------------------------------------------- tier emblems
def tier_emblem(tier, size, m, depth=0.01):
    """The tier's mark, flat in the XZ plane facing -Y, centred on the origin (like boss_regalia.emblem)."""
    s = size
    T, G, W = m["trim"], m["glow"], m["gem"]
    out = []
    if tier == "cosmic":       # an eight-pointed star in an orbit ring
        out.append(RG.slab([(u * s, v * s) for u, v in RG.star_outline(0.5, 0.17, k=8, rot=90.0)], depth * 1.3, T))
        out.append(RG.slab([(u * s, v * s) for u, v in RG.star_outline(0.24, 0.1, k=4, rot=45.0)], depth * 2.2, G))
        out.append(K.ring_tube((0, 0, 0), 0.36 * s, 0.018 * s, T, axis="y", n=30))
    elif tier == "divine":     # a sunburst disc
        out.append(K.lathe([(0.0, 0.0), (0.2 * s, 0.0), (0.22 * s, depth), (0.0, depth * 1.6)], T, 24).rot(Rx(90)))
        for i in range(16):
            L = 0.5 if i % 2 == 0 else 0.34
            ray = [(-0.035 * s, 0.2 * s), (0.035 * s, 0.2 * s), (0.0, L * s)]
            out.append(RG.xform([RG.slab(ray, depth, T)], Ry(-i * 22.5))[0])
        out.append(K.gem((0, -depth * 1.8, 0), 0.1 * s, W, rot=(90, 0, 0)))
    elif tier == "eternal":    # an hourglass in a dial with twelve hour marks
        out.append(K.ring_tube((0, 0, 0), 0.42 * s, 0.022 * s, T, axis="y", n=36))
        for i in range(12):
            a = math.radians(i * 30)
            out.append(K.box(0.03 * s, depth, 0.07 * s, (0.36 * s * math.cos(a), 0, 0.36 * s * math.sin(a)), T).rot(Ry(-i * 30), (0.36 * s * math.cos(a), 0, 0.36 * s * math.sin(a))))
        glass = [(-0.16 * s, 0.24 * s), (0.16 * s, 0.24 * s), (0.02 * s, 0.0), (0.16 * s, -0.24 * s), (-0.16 * s, -0.24 * s), (-0.02 * s, 0.0)]
        out.append(RG.slab(glass, depth * 1.6, G))
        for z in (0.26, -0.26):
            out.append(K.box(0.4 * s, depth * 2.0, 0.035 * s, (0, 0, z * s), T))
    else:                      # primordial: a cracked obsidian shard with a molten core
        shard = [(0.0, 0.5 * s), (0.14 * s, 0.16 * s), (0.22 * s, 0.22 * s), (0.12 * s, -0.12 * s), (0.18 * s, -0.42 * s),
                 (0.0, -0.3 * s), (-0.16 * s, -0.44 * s), (-0.12 * s, -0.08 * s), (-0.24 * s, 0.12 * s), (-0.1 * s, 0.14 * s)]
        out.append(RG.slab(shard, depth * 1.4, m["horn"]))
        crack = [(0.0, 0.36 * s), (0.04 * s, 0.1 * s), (0.08 * s, -0.04 * s), (0.0, -0.22 * s), (-0.05 * s, -0.04 * s), (-0.03 * s, 0.1 * s)]
        out.append(RG.slab(crack, depth * 2.2, G))
    return out


def front(parts, c, R=None):
    return RG.xform(parts, R, c)


# ------------------------------------------------------------------------------------------------- tier ornaments
def helm_ornaments(tier, m, sid):
    """Above and around the head (model space: crown of the head ~ z 1.95, front -Y)."""
    out = []
    G, T, W = m["glow"], m["trim"], m["gem"]
    if tier == "cosmic":
        # a tilted orbit ring round the crown, five star gems riding it, a star crest at the brow
        ring = K.ring_tube((0, 0.02, 2.0), 0.25, 0.007, T, axis="z", n=40).rot(Rx(16), (0, 0.02, 2.0))
        out.append(ring)
        for i in range(5):
            a = math.radians(i * 72 + 18)
            p = np.array((0.25 * math.cos(a), 0.02 + 0.25 * math.sin(a), 2.0))
            p = (Rx(16) @ (p - np.array((0, 0.02, 2.0)))) + np.array((0, 0.02, 2.0))
            out.append(K.gem(tuple(p), 0.022, G if i % 2 == 0 else W, facets=4, rot=(0, 45, 0)))
        out += front(tier_emblem(tier, 0.11, m), (0, -0.18, 1.9))
    elif tier == "divine":
        # a halo standing behind the head, with rays, and small wings at the temples
        out.append(K.ring_tube((0, 0.17, 1.99), 0.2, 0.012, G, axis="y", n=48))
        out.append(K.ring_tube((0, 0.175, 1.99), 0.235, 0.005, T, axis="y", n=48))
        for i in range(12):
            a = math.radians(i * 30)
            out.append(K.cone_spike((0.24 * math.cos(a), 0.18, 1.99 + 0.24 * math.sin(a)),
                                    (0.31 * math.cos(a), 0.18, 1.99 + 0.31 * math.sin(a)), 0.01, T))
        for sx in (-1, 1):
            for j in range(3):
                o = [(0.0, 0.0), (0.05, 0.02 + j * 0.01), (0.15 - j * 0.02, 0.09 + j * 0.03), (0.04, 0.05)]
                out.append(RG.slab([(sx * u, v) for u, v in o], 0.006, T).move((sx * 0.16, 0.02 - j * 0.02, 1.8 + j * 0.03)))
    elif tier == "eternal":
        # a clock-dial crown: two counter rings with hour marks, an hourglass crest
        for r, z in ((0.2, 1.97), (0.15, 2.02)):
            out.append(K.ring_tube((0, 0.01, z), r, 0.006, T, axis="z", n=44))
        for i in range(12):
            a = math.radians(i * 30)
            out.append(K.cone_spike((0.2 * math.cos(a), 0.01 + 0.2 * math.sin(a), 1.97),
                                    (0.2 * math.cos(a), 0.01 + 0.2 * math.sin(a), 2.02 + (0.04 if i % 3 == 0 else 0.0)), 0.008, T))
        out += front(tier_emblem(tier, 0.13, m), (0, -0.17, 1.95))
        out.append(K.crystal((0, 0.01, 2.1), 0.12, 0.03, G))
    else:
        # a crown of obsidian shards with molten seams, and two swept horns
        for i in range(9):
            a = math.radians(-90 + i * 40)              # i = 0 at the brow (front is -Y)
            base = (0.15 * math.cos(a), 0.01 + 0.16 * math.sin(a), 1.9)
            L = 0.26 if i == 0 else (0.18 if i in (1, 8) else 0.12)
            lean = 18.0                                  # each shard leans outward from the head
            out.append(K.crystal((base[0] * 1.08, base[1] * 1.08, 1.9 + L * 0.45), L, 0.03, m["horn"],
                                 rot=(lean * math.sin(a), -lean * math.cos(a), 0)))
            out.append(K.cone_spike(base, (base[0] * 1.1, base[1] * 1.1, 1.9 + L * 0.6), 0.006, G))
        for sx in (-1, 1):
            out.append(RG.horn([(sx * 0.14, 0.06, 1.84), (sx * 0.24, 0.1, 1.9), (sx * 0.3, 0.16, 2.02), (sx * 0.28, 0.24, 2.12)], 0.035, m["horn"]))
    return out


def armor_ornaments(tier, m, sid):
    """On the chest (z ~1.3, front y ~ -0.2) and shoulders (x ~ +-0.3, z ~1.5)."""
    out = front(tier_emblem(tier, 0.17, m, 0.012), (0, -0.215, 1.34))
    G, T = m["glow"], m["trim"]
    for sx in (-1, 1):
        c = (sx * 0.34, 0.0, 1.62)
        if tier == "cosmic":
            # three stars set into the pauldron's face
            for i in range(3):
                out.append(K.gem((sx * (0.27 + i * 0.045), -0.105, 1.53 - abs(i - 1) * 0.02), 0.016, G, facets=4, rot=(90, 0, 45)))
        elif tier == "divine":
            for j in range(4):
                o = [(0.0, 0.0), (0.06, 0.02), (0.2 - j * 0.03, 0.12 + j * 0.02), (0.05, 0.06)]
                out.append(RG.slab([(sx * u, v) for u, v in o], 0.007, T).move((sx * 0.3, 0.06 + j * 0.02, 1.6 + j * 0.035)))
        elif tier == "eternal":
            # a small dial on the pauldron's face
            out += small_mark(tier, m, (sx * 0.31, -0.11, 1.52), 0.07)
        else:
            for j in range(3):
                b = (sx * (0.28 + j * 0.06), 0.02 - j * 0.03, 1.6)
                out.append(K.crystal((b[0] + sx * 0.03, b[1], b[2] + 0.1), 0.2 - j * 0.04, 0.03, m["horn"], rot=(0, sx * -20, 0)))
                out.append(K.cone_spike((b[0], b[1] - 0.01, b[2] + 0.02), (b[0] + sx * 0.04, b[1] - 0.01, b[2] + 0.14 - j * 0.03), 0.006, G))
    if tier == "primordial":      # molten seams across the chest plate
        for sx in (-1, 1):
            pts = [(sx * 0.05, -0.215, 1.46), (sx * 0.12, -0.21, 1.38), (sx * 0.1, -0.22, 1.28), (sx * 0.16, -0.205, 1.18)]
            out.append(K.tube(pts, [0.005, 0.006, 0.005, 0.003], G, n=5))
    return out


def small_mark(tier, m, c, size=0.05, R=None):
    return front(tier_emblem(tier, size, m, 0.006), c, R)


def ornaments(tier, slot, m, sid):
    if slot == "helm":
        return helm_ornaments(tier, m, sid)
    if slot == "armor":
        return armor_ornaments(tier, m, sid)
    if slot == "inner_garment":
        return small_mark(tier, m, (0, -0.16, 1.02), 0.08)
    if slot == "leggings":
        return small_mark(tier, m, (0.1, -0.12, 0.74), 0.05) + small_mark(tier, m, (-0.1, -0.12, 0.74), 0.05)
    if slot.startswith("gloves"):
        return small_mark(tier, m, (0.6, -0.07, 1.445), 0.045)
    if slot.startswith("boots"):
        return small_mark(tier, m, (0.1, -0.09, 0.36), 0.05)
    if slot == "accessory_1":
        return [K.gem((0.785, -0.03, 1.47), 0.012, m["glow"], rot=(90, 0, 0))]
    if slot == "accessory_3":
        return small_mark(tier, m, (0, -0.29, 1.255), 0.04)
    if slot == "accessory_4":
        return [K.ring_tube((-0.2, -0.25, 1.43), 0.07, 0.004, m["glow"], axis="y", n=24)]
    if slot == "sub_weapon":
        return small_mark(tier, m, (0, -0.2, -0.3), 0.12)
    return []


# ------------------------------------------------------------------------------------------------- weapons
def weapon_parts(sid):
    """The collection's signature weapon in the hand-socket convention (grip at the origin, long axis +Z)."""
    import item_weapons as W
    import artisan_weapons as A
    s = COLLECTIONS[sid]
    m = palette(sid)
    tier, wt = s["tier"], s["weapon"]
    B, T, G, L = m["plate"], m["trim"], m["glow"], m["leather"]
    # the plate colour is a metal on a weapon (a cloth plate base would read as felt)
    K.MAT[B] = ("BH_Steel" if tier != "primordial" else "BH_DarkSteel",) + K.MAT[B][1:]
    variant = ORDER.index(sid) % 10
    if wt == "sword":
        parts = W.sword({"len": 0.96, "w": (0.058, 0.036), "shape": ["waisted", "leaf", "straight", "waisted"][TIERS.index(tier)], "blade": B,
                         "guard": "winged", "guard_half": 0.15, "guard_mat": T, "grip_mat": L, "pommel": "spike", "pommel_mat": T,
                         "gem": m["gem"], "glow": G, "lugs": True})
    elif wt == "greatsword":
        parts = W.sword({"len": 1.24, "z0": 0.135, "w": (0.074, 0.05), "thick": 0.009, "shape": "waisted" if variant % 2 else "straight",
                         "blade": B, "guard": "winged", "guard_half": 0.22, "guard_mat": T, "grip_len": 0.34, "grip_r": 0.018,
                         "grip_mat": L, "pommel": "disc", "pommel_mat": T, "gem": m["gem"], "glow": G, "lugs": True})
    elif wt in ("axe", "greataxe"):
        parts = W.axe({"two_handed": wt == "greataxe", "head": ["moon", "broad", "crescent", "bearded"][TIERS.index(tier)],
                       "double": wt == "greataxe", "head_mat": B, "band_mat": T, "haft_mat": "darkwood", "spike_mat": T,
                       "head_scale": 1.3 if wt == "greataxe" else 1.1, "glow": G, "pommel": True, "wrap": L})
    elif wt == "spear":
        parts = W.spear({"head": "lance", "head_len": 0.44, "head_mat": B, "shaft_mat": "darkwood", "band_mat": T, "glow": G})
    elif wt == "club":
        parts = W.club({"kind": "flanged", "head_mat": B, "flanges": 8, "glow": G, "grip_mat": L, "haft_mat": "darkwood"})
    elif wt == "staff":
        parts = W.staff({"head": ["star", "orb", "orb", "shards"][TIERS.index(tier)] if variant % 2 == 0 else ["orb", "star", "prongs", "fork"][TIERS.index(tier)],
                         "gem": m["gem"], "wood": "darkwood", "metal": T, "band": T})
    elif wt == "wand":
        parts = W.wand({"wood": "darkwood", "head": ["claw", "sun", "claw", "skull"][TIERS.index(tier)], "gem": m["gem"], "orn": T})
    elif wt == "bow":
        parts = W.bow({"len": 0.8, "bend": 0.13, "recurve": 0.11, "limb_mat": B, "orn": T, "glow": G, "wraps": L})
    elif wt == "crossbow":
        parts = A.crossbow({"design": (variant + TIERS.index(tier) * 3) % 10})
        parts = _remap(parts, m)
    elif wt == "dagger":
        parts = W.dagger({"len": 0.33, "shape": ["crescent", "kris", "crescent", "kris"][TIERS.index(tier)], "blade": B, "guard_mat": T,
                          "glow": G, "gem": m["gem"], "grip_mat": L})
    else:  # claw
        parts = W.claw({"blades": 3, "len": 0.33, "hook": 0.07, "blade": B, "frame_mat": T, "glow": G, "spikes": True, "plate_mat": T})
    parts += weapon_ornaments(tier, wt, parts, m)
    return parts


def _remap(parts, m):
    """Artisan designs come in their own palette: metals to the plate, gold-like trims to the trim, glows to the glow."""
    for p in parts:
        src = K.MAT.get(p.mat)
        if src is None:
            continue
        if src[4] or src[0] in ("BH_Gem", "BH_Aether", "BH_Emissive"):
            p.mat = m["glow"]
        elif p.mat in ("bright", "silver", "gold", "brass", "paleg", "bronze", "copper", "sunsteel"):
            p.mat = m["trim"]
        elif src[0] not in ("BH_Leather", "BH_Cloth_Secondary", "BH_Wood"):
            p.mat = m["plate"]
    return parts


def weapon_ornaments(tier, wt, parts, m):
    V = np.vstack([p.V for p in parts])
    lo, hi = V.min(0), V.max(0)
    G, T, W = m["glow"], m["trim"], m["gem"]
    out = []
    long_z = wt not in ("bow", "crossbow", "claw")
    # the point the ornament circles: 62 % up a long weapon, the riser of a bow, the stock of a crossbow
    if long_z:
        c = (0.0, 0.0, lo[2] + (hi[2] - lo[2]) * (0.62 if wt not in ("staff", "wand", "spear", "club", "axe", "greataxe") else 0.86))
        r = max(0.06, min(0.14, (hi[0] - lo[0]) * 0.55))
    else:
        c = tuple((lo + hi) / 2)
        r = 0.11
    if tier == "cosmic":
        out.append(K.ring_tube(c, r, 0.005, T, axis="z", n=36).rot(Rx(18), c))
        for i in range(3):
            a = math.radians(i * 120 + 30)
            p = (Rx(18) @ np.array((r * math.cos(a), r * math.sin(a), 0.0))) + np.array(c)
            out.append(K.gem(tuple(p), 0.014, G, facets=4))
    elif tier == "divine":
        out.append(K.ring_tube(c, r * 0.9, 0.007, G, axis="y", n=36))
        for i in range(8):
            a = math.radians(i * 45)
            out.append(K.cone_spike((c[0] + r * 0.95 * math.cos(a), c[1], c[2] + r * 0.95 * math.sin(a)),
                                    (c[0] + r * 1.3 * math.cos(a), c[1], c[2] + r * 1.3 * math.sin(a)), 0.006, T))
        if long_z:
            for sx in (-1, 1):
                for j in range(3):
                    o = [(0.0, 0.0), (0.03, 0.01), (0.09 - j * 0.015, 0.05 + j * 0.012), (0.025, 0.03)]
                    out.append(RG.slab([(sx * u, v) for u, v in o], 0.005, T).move((sx * 0.03, 0.0, 0.02 + j * 0.018)))
    elif tier == "eternal":
        for k_, rr in enumerate((r, r * 0.72)):
            out.append(K.ring_tube(c, rr, 0.005, T, axis="z", n=36).rot(Rx(25 if k_ == 0 else -25), c))
        out.append(K.crystal(c, r * 0.9, 0.018, G))
        if long_z:
            out.append(K.ring_tube((0, 0, lo[2] + 0.01), 0.03, 0.006, T, axis="z", n=18))
    else:
        if long_z:
            n = 5
            for i in range(n):
                z = lo[2] + (hi[2] - lo[2]) * (0.3 + 0.5 * i / (n - 1))
                sx = -1 if i % 2 else 1
                out.append(K.crystal((sx * 0.035, 0.0, z), 0.09, 0.014, m["horn"], rot=(0, sx * 40, 0)))
                out.append(K.cone_spike((sx * 0.02, 0.0, z - 0.02), (sx * 0.06, 0.0, z + 0.03), 0.004, G))
        else:
            for i in range(4):
                a = math.radians(i * 90 + 45)
                out.append(K.crystal((c[0] + r * math.cos(a), c[1], c[2] + r * math.sin(a)), 0.08, 0.014, m["horn"]))
        out.append(K.sphere(0.022, c if not long_z else (0, 0, lo[2] + (hi[2] - lo[2]) * 0.15), G, 10, 8))
    return out


# ------------------------------------------------------------------------------------------------- build
def build_piece(sid, piece, mirror=False):
    """Parts of one piece in its attachment frame (weapons: the hand socket). mirror: the right glove / boot."""
    s = COLLECTIONS[sid]
    if piece == "weapon":
        return weapon_parts(sid)
    m = palette(sid)
    slot = piece_slot(sid, piece)
    if mirror:
        slot = slot[:-1] + "2"
    if piece in ("gloves", "boots"):
        base_slot = slot[:-1] + "1"
        parts = RG.piece_parts(sid, base_slot, m) + ornaments(s["tier"], base_slot, m, sid)
        if mirror:
            parts = [p.mirrored(False) for p in parts]
            for p in parts:
                p.bone = RG.swap_bone(p.bone)
    else:
        parts = RG.piece_parts(sid, slot, m) + ornaments(s["tier"], slot, m, sid)
    return RG.to_frame(parts, slot)


def todo_for(sids):
    out = []
    for sid in sids:
        for piece in PIECES:
            out.append((sid, piece, False))
            if piece in ("gloves", "boots"):
                out.append((sid, piece, True))
    return out


def export_models(sids, log=print):
    import json
    sys.path.insert(0, K.CHARS)
    from build import reset
    report = []
    for sid, piece, mirror in todo_for(sids):
        reset()
        iid = item_id(sid, piece)
        parts = build_piece(sid, piece, mirror)
        obs = RG.objects_for(iid, parts)
        path = os.path.join(ITEMS_DIR, iid + ("_R" if mirror else "") + ".glb")
        RG._export(path, obs)
        tris = sum(M.tri_count(o) for o in obs)
        report.append({"id": iid + ("_R" if mirror else ""), "tris": tris, "objects": [o.name for o in obs]})
        log("[ascendant] %-46s %6d tris  %s" % (os.path.basename(path), tris, ",".join(o.name for o in obs[1:])))
    out = os.path.join(ROOT, "work", "lemondev", "bh-034", "evidence")
    os.makedirs(out, exist_ok=True)
    name = "models_report_%s.json" % ("all" if len(sids) == len(ORDER) else "_".join(sorted({COLLECTIONS[s]["tier"] for s in sids})))
    with open(os.path.join(out, name), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1)
    return report


ICON_VIEW = dict(RG.ICON_VIEW)


def render_icons(sids, raw_dir, log=print):
    import bpy
    from mathutils import Vector
    sys.path.insert(0, K.CHARS)
    from build import reset
    import build_items as B
    os.makedirs(raw_dir, exist_ok=True)
    for sid in sids:
        for piece in PIECES:
            reset()
            iid = item_id(sid, piece)
            s = COLLECTIONS[sid]
            slot = piece_slot(sid, piece)
            if piece == "weapon":
                parts = weapon_parts(sid)
            else:
                m = palette(sid)
                parts = RG.piece_parts(sid, slot, m) + ornaments(s["tier"], slot, m, sid)
                if piece == "armor":
                    parts = [p for p in parts if p.name not in ("cape", "scarf")]
            for p in parts:
                p.bone = None
            pitch, yaw, R = ICON_VIEW[slot]
            if R is not None:
                c = np.mean(np.vstack([p.V for p in parts]), 0)
                for p in parts:
                    p.rot(R, c)
            obs = RG.objects_for(iid, parts, textured=True)
            cam = B._studio(256)
            if piece == "weapon":
                pitch, yaw = B._pose_for({"category": "weapon", "weapon_type": s["weapon"], "id": iid}, obs[0])
            bpy.context.view_layer.update()
            pts = [o.matrix_world @ Vector(cc) for o in obs for cc in o.bound_box]
            c = sum(pts, Vector()) / len(pts)
            for o in obs:
                o.location -= c
            bpy.context.view_layer.update()
            p_, y_ = math.radians(pitch), math.radians(yaw)
            d = Vector((math.sin(y_) * math.cos(p_), -math.cos(y_) * math.cos(p_), math.sin(p_)))
            cam.location = d * 10.0
            cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
            bpy.context.view_layer.update()
            inv = cam.matrix_world.inverted()
            q = [inv @ (o.matrix_world @ Vector(cc)) for o in obs for cc in o.bound_box]
            ext = max(max(v.x for v in q) - min(v.x for v in q), max(v.y for v in q) - min(v.y for v in q))
            cam.data.ortho_scale = ext * 1.1
            cx = (max(v.x for v in q) + min(v.x for v in q)) / 2
            cy = (max(v.y for v in q) + min(v.y for v in q)) / 2
            cam.location = cam.matrix_world @ Vector((cx, cy, 0.0))
            cam.data.clip_start = 0.01
            cam.data.clip_end = 100
            bpy.context.scene.render.filepath = os.path.join(raw_dir, iid + ".png")
            bpy.ops.render.render(write_still=True)
            log("[icon] %s" % iid)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    targets = [a for a in argv if a in ("models", "icons")] or ["models"]
    tiers = [a for a in argv if a in TIERS]
    sids = [a for a in argv if a in COLLECTIONS] or [s for s in ORDER if not tiers or COLLECTIONS[s]["tier"] in tiers]
    raw = os.environ.get("BH_ASC_RAW", os.path.join(ROOT, "work", "lemondev", "bh-034", "scratch", "icons_raw"))
    if "models" in targets:
        export_models(sids)
    if "icons" in targets:
        render_icons(sids, raw)
    print("[ascendant] done", len(sids), "collections")


if __name__ == "__main__":
    main()
