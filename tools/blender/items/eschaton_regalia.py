"""bh-041: Eschaton — the tier past Primordial. Lape the Ancient alone makes it, and only from the highest-tier lots.

Primordial is the oldest thing in the world; Eschaton is the last. The pieces are mirror chrome over black chrome with
a prismatic glow: an eclipse emblem (a black disc in a chrome corona with blade rays), a floating halo of chrome
blades behind the helm, blades rising from the pauldrons, and a ring of chrome shards on every weapon.

Catalogue (game/src/data/data_eschaton.gd keeps the same ids):
  * forty collections, ten per class (knight, mage, ranger, shadowblade); each a set of helm, armour, inner garment,
    leggings, gauntlets, boots and a jewel (and a shield for the knights' collections):
        esc_<collection>_<piece>
  * ten weapons of every weapon type each class masters, made for that class (knight 7 types, mage 2, ranger 5,
    shadowblade 4 = 180):  esc_w_<class>_<weapon type>_<0..9>; weapon n wears collection n's palette.
The armour is built by the bh-022 regalia builders (boss_regalia.py, fitted to the hero skeleton) from each collection's
style, like the Ascendant pieces (ascendant_regalia.py), with the Eschaton ornaments added in model space.
Materials are "BH_Chrome__it_esc_<collection>_<role>" / "BH_BlackChrome__..."; MaterialLibrary gives them the chrome
surface in the game. Gloves and boots also export <id>_R.glb (the right hand / foot).

  blender -b --factory-startup --python tools/blender/items/eschaton_regalia.py -- [models] [icons] [knight|mage|ranger|shadowblade ...] [weapons] [armour]
"""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import item_kit as K  # noqa: E402
from item_kit import M, Rx, Ry, Rz  # noqa: E402
import ascendant_regalia as AR  # noqa: E402  (also registers the Ascendant collections in boss_regalia.SETS)
import boss_regalia as RG  # noqa: E402

ROOT = AR.ROOT
ITEMS_DIR = AR.ITEMS_DIR
CLASSES = ["knight", "mage", "ranger", "shadowblade"]
WEAPONS = {"knight": ["sword", "greatsword", "axe", "greataxe", "spear", "club", "javelin"],
           "mage": ["staff", "wand"],
           "ranger": ["bow", "crossbow", "javelin", "spear", "dagger"],
           "shadowblade": ["dagger", "claw", "knuckles", "sword"]}


def _e(cls, helm, torso, skirt, motif, cape, shield, jewel, plate, trim, cloth, leather, glow, gold_trim=False):
    """One collection's style. plate: the mirror chrome; trim: black chrome (or a gold chrome); glow: the prismatic light."""
    return dict(tier="eschaton", cls=cls, weapon=WEAPONS[cls][0], helm=helm, torso=torso, skirt=skirt, motif=motif, cape=cape,
                shield_shape=shield, jewel=jewel,
                plate=("BH_Chrome", plate, 1.0, 0.06), trim=("BH_Chrome" if gold_trim else "BH_BlackChrome", trim, 1.0, 0.1),
                cloth=("BH_Cloth_Primary", cloth, 0.0, 0.85), leather=("BH_Leather", leather, 0.0, 0.6),
                horn=("BH_BlackChrome", "101116", 1.0, 0.08), glow=glow)


# id: (class, helm, torso, skirt, motif, cape, shield, jewel, plate, trim, cloth, leather, glow[, gold trim])
COLLECTIONS = {
    # ---- knights: mirror plate, black-chrome trim, the last banners -------------------------------------------------
    "doomsday_paragon": _e("knight", "great", "plate", "tassets", "sun", "wings", "heater", "ring", "e6eaf2", "15161b", "0b0b12", "1a1a20", "f4f0ff"),
    "worldsend_bulwark": _e("knight", "great", "plate", "tassets", "shard", "tattered", "tower", "ring", "d8dde8", "c9a64a", "2a0a12", "201416", "ff3050", True),
    "endbringer_sovereign": _e("knight", "sallet", "plate", "tassets", "dragon", "long", "kite", "ring", "eef1f6", "191a20", "120a1e", "1c1820", "b070ff"),
    "last_crown_marshal": _e("knight", "great", "plate", "tassets", "star", "split", "heater", "ring", "dfe5ee", "e2c37a", "0f1a2e", "1a1e26", "7fd8ff", True),
    "ruinmarch_herald": _e("knight", "sallet", "plate", "tassets", "flame", "tattered", "tower", "ring", "cfd5df", "17181d", "2e0e0a", "221614", "ff6a20"),
    "oblivion_warden": _e("knight", "great", "plate", "tassets", "orbs", "fur", "kite", "ring", "e9edf3", "121318", "06060a", "141418", "9a9aff"),
    "final_dawn_executor": _e("knight", "great", "plate", "tassets", "feather", "wings", "heater", "ring", "f2f4f8", "d8b860", "3a3226", "2a2218", "fff0b0", True),
    "starless_throne": _e("knight", "sallet", "plate", "tassets", "crescent", "long", "tower", "ring", "d4d9e4", "101015", "0a0a16", "16161c", "c8d0ff"),
    "ashen_apocalypse": _e("knight", "great", "plate", "tassets", "bolt", "split", "kite", "ring", "dde2ea", "1a1b21", "1c1c22", "202024", "7affd8"),
    "unmaker_vanguard": _e("knight", "sallet", "plate", "tassets", "serpent", "tattered", "heater", "ring", "e4e8f0", "b8964a", "1e0a24", "1a141e", "ff60d0", True),
    # ---- mages: chrome mantles over void cloth ------------------------------------------------------------------
    "void_unwritten": _e("mage", "hood", "mantle", "robe", "crescent", "long", "round", "ring", "e2e6ee", "141519", "08080e", "16141a", "a890ff"),
    "last_word_archon": _e("mage", "mitre", "mantle", "robe", "sun", "wings", "round", "pendant", "f0f2f6", "dcc070", "1a1430", "201a24", "ffe8a8", True),
    "entropy_magus": _e("mage", "crown", "mantle", "robe", "shard", "tattered", "round", "ring", "d6dbe4", "121216", "200a26", "1a141e", "ff50c8"),
    "null_choir": _e("mage", "circlet", "mantle", "robe", "orbs", "long", "round", "pendant", "e8ecf2", "17181e", "0c1420", "141820", "80e8ff"),
    "unmade_sky_sage": _e("mage", "hood", "mantle", "robe", "star", "split", "round", "ring", "dde2ea", "c8a858", "101830", "1a1e28", "a8c8ff", True),
    "silent_star_conclave": _e("mage", "mitre", "mantle", "robe", "tear", "long", "round", "pendant", "eef1f5", "131418", "0e0e16", "18181e", "e0e4ff"),
    "ender_of_tomes": _e("mage", "crown", "mantle", "robe", "flame", "tattered", "round", "ring", "d2d8e2", "16171c", "2a0c0c", "221412", "ff7838"),
    "mirrorless_oracle": _e("mage", "circlet", "mantle", "robe", "snow", "fur", "round", "pendant", "f4f6f9", "1a1b20", "142028", "18202a", "9cfff0"),
    "final_equation": _e("mage", "hood", "mantle", "robe", "bolt", "long", "round", "ring", "e0e4ec", "b49048", "1c1a10", "22201a", "fff070", True),
    "eclipse_sovereign": _e("mage", "crown", "mantle", "robe", "antler", "wings", "round", "pendant", "dfe3eb", "101014", "120612", "181218", "d070ff"),
    # ---- rangers: chrome brigandine, ash and storm cloth -----------------------------------------------------------
    "endtime_stalker": _e("ranger", "sallet", "brigandine", "leather", "feather", "split", "round", "pendant", "dde2ea", "16171c", "1a1e18", "22261e", "a8ff8c"),
    "last_arrow": _e("ranger", "wrap", "brigandine", "scarves", "bolt", "scarf", "round", "brooch", "e8ecf2", "c4a050", "2a1a10", "2a2016", "ffd070", True),
    "horizon_breaker": _e("ranger", "circlet", "brigandine", "leaves", "leaf", "wings", "round", "pendant", "d8dde6", "131418", "0e1a20", "16202a", "70e0ff"),
    "doomwind_hunter": _e("ranger", "hood", "brigandine", "leather", "antler", "tattered", "round", "brooch", "e2e6ee", "17181d", "1e1a24", "201c26", "c890ff"),
    "extinction_volley": _e("ranger", "sallet", "brigandine", "scarves", "shard", "split", "round", "pendant", "eef1f5", "111216", "240c10", "241416", "ff4860"),
    "skys_end_warden": _e("ranger", "circlet", "brigandine", "leaves", "star", "long", "round", "brooch", "f0f2f6", "d0b060", "12203a", "1a2230", "a0d8ff", True),
    "ashfall_pathfinder": _e("ranger", "wrap", "brigandine", "leather", "flame", "scarf", "round", "pendant", "d4d9e2", "18191e", "201812", "2a2018", "ffa040"),
    "requiem_marksman": _e("ranger", "hood", "brigandine", "scarves", "tear", "tattered", "round", "brooch", "e6e9f0", "141519", "101018", "18181e", "e8e8ff"),
    "final_twilight": _e("ranger", "sallet", "brigandine", "leaves", "crescent", "wings", "round", "pendant", "dde1e9", "b89850", "1a1028", "201828", "ff90e0", True),
    "worldscar_tracker": _e("ranger", "wrap", "brigandine", "leather", "serpent", "split", "round", "brooch", "e4e8ef", "15161b", "0e1a14", "16201a", "60ffb0"),
    # ---- shadowblades: black chrome harness, chrome edges, the quiet end ------------------------------------------
    "nihil_fang": _e("shadowblade", "cobra", "harness", "leather", "serpent", "tattered", "round", "brooch", "d6dbe4", "0e0f12", "0a080e", "141018", "b060ff"),
    "last_breath": _e("shadowblade", "hood", "harness", "scarves", "tear", "scarf", "round", "brooch", "e8ecf2", "131418", "101418", "161a1e", "90f0ff"),
    "mirror_death": _e("shadowblade", "circlet", "harness", "leather", "shard", "split", "round", "brooch", "f2f4f8", "121316", "141416", "1a1a1e", "f0f4ff"),
    "void_silhouette": _e("shadowblade", "wrap", "harness", "scarves", "crescent", "tattered", "round", "brooch", "dde1e9", "0f1013", "06060a", "121216", "8080ff"),
    "ending_whisper": _e("shadowblade", "cobra", "harness", "leather", "feather", "scarf", "round", "brooch", "e2e6ee", "c0a058", "1a1414", "221a18", "ffc080", True),
    "hollow_eclipse": _e("shadowblade", "hood", "harness", "scarves", "orbs", "tattered", "round", "brooch", "d8dde6", "101114", "160a14", "1c1218", "ff40a0"),
    "severance": _e("shadowblade", "circlet", "harness", "leather", "bolt", "split", "round", "brooch", "e6e9f0", "141518", "1a0a0a", "201212", "ff3a3a"),
    "quietus": _e("shadowblade", "wrap", "harness", "scarves", "snow", "scarf", "round", "brooch", "eef1f5", "121317", "0e1418", "141c20", "a0ffe8"),
    "null_reaper": _e("shadowblade", "cobra", "harness", "leather", "dragon", "tattered", "round", "brooch", "d2d7e0", "b8984c", "120e0a", "1a1610", "ffe060", True),
    "shroud_of_last_night": _e("shadowblade", "hood", "harness", "scarves", "star", "split", "round", "brooch", "dfe3eb", "0d0e11", "08080c", "101014", "c0c8ff"),
}
ORDER = list(COLLECTIONS.keys())
ARMOUR = ["helm", "armor", "inner", "leggings", "gloves", "boots", "accessory"]
PIECE_SLOT = AR.PIECE_SLOT
JEWEL_SLOT = AR.JEWEL_SLOT

for _sid, _s in COLLECTIONS.items():
    RG.SETS[_sid] = _s
    RG.SHIELDED[_sid] = _s["shield_shape"]


def class_sids(cls):
    return [s for s in ORDER if COLLECTIONS[s]["cls"] == cls]


def pieces_of(sid):
    return ARMOUR + (["shield"] if COLLECTIONS[sid]["cls"] == "knight" else [])


def item_id(sid, piece):
    return "esc_%s_%s" % (sid, piece)


def weapon_id(cls, wt, i):
    return "esc_w_%s_%s_%d" % (cls, wt, i)


def palette(sid):
    """Chrome palette under esc_ keys (MaterialLibrary turns BH_Chrome / BH_BlackChrome into mirror metal)."""
    s = COLLECTIONS[sid]
    keys = {}
    for role in ("plate", "trim", "cloth", "leather", "horn"):
        base, hx, met, rough = s[role]
        k = "esc_%s_%s" % (sid, role)
        K.MAT[k] = (base, RG.srgb(hx), met, rough, None, 0)
        keys[role] = k
    k = "esc_%s_mail" % sid
    K.MAT[k] = ("BH_Chrome", RG.srgb("aab0bc"), 1.0, 0.18, None, 0)
    keys["mail"] = k
    k = "esc_%s_dark" % sid
    K.MAT[k] = ("BH_BlackChrome", RG.srgb("0c0c10"), 1.0, 0.12, None, 0)
    keys["dark"] = k
    g = RG.srgb(s["glow"])
    k = "esc_%s_glow" % sid
    K.MAT[k] = ("BH_Emissive", g, 0.0, 0.2, g, 3.0)
    keys["glow"] = k
    k = "esc_%s_gem" % sid
    K.MAT[k] = ("BH_Gem", tuple(c * 0.75 for c in g), 0.0, 0.04, g, 1.8)
    keys["gem"] = k
    return keys


# ------------------------------------------------------------------------------------------------- the eclipse
def emblem(size, m, depth=0.01):
    """The Eschaton mark, flat in the XZ plane facing -Y: a black-chrome eclipse in a chrome corona with eight blade
    rays of two lengths, a ring of light and a gem at its heart."""
    s = size
    P_, T, G = m["plate"], m["trim"], m["glow"]
    out = [K.lathe([(0.0, 0.0), (0.2 * s, 0.0), (0.21 * s, depth), (0.0, depth * 1.5)], T, 28).rot(Rx(90))]
    out.append(K.ring_tube((0, 0, 0), 0.26 * s, 0.022 * s, P_, axis="y", n=36))
    for i in range(8):
        L = 0.64 if i % 2 == 0 else 0.44
        ray = [(-0.034 * s, 0.27 * s), (0.034 * s, 0.27 * s), (0.008 * s, L * s)]
        out.append(RG.xform([RG.slab(ray, depth, P_)], Ry(-i * 45.0 - 9.0))[0])
    out.append(K.ring_tube((0, -depth * 0.8, 0), 0.215 * s, 0.009 * s, G, axis="y", n=36))
    out.append(K.gem((0, -depth * 1.9, 0), 0.07 * s, m["gem"], rot=(90, 0, 0)))
    return out


def mark(m, c, size=0.05, R=None):
    return RG.xform(emblem(size, m, 0.006), R, c)


def helm_ornaments(m):
    """A floating halo of chrome blades behind the head, a black-chrome ring with light inside it, the eclipse on the
    brow and two blades sweeping back from the temples."""
    G, T, P_ = m["glow"], m["trim"], m["plate"]
    c = (0.0, 0.17, 2.0)
    out = [K.ring_tube(c, 0.215, 0.013, T, axis="y", n=48), K.ring_tube((0, 0.175, 2.0), 0.175, 0.006, G, axis="y", n=48)]
    for i in range(11):
        a = math.radians(-20 + i * 22)
        L = 0.38 if i % 2 == 0 else 0.29
        out.append(K.cone_spike((0.215 * math.cos(a), 0.17, 2.0 + 0.215 * math.sin(a)),
                                (L * math.cos(a), 0.17, 2.0 + L * math.sin(a)), 0.015, P_))
    out += mark(m, (0, -0.18, 1.91), 0.12)
    for sx in (-1, 1):
        out.append(K.crystal((sx * 0.17, 0.05, 1.93), 0.24, 0.02, P_, rot=(0, sx * -58, 0)))
    return out


def armor_ornaments(m):
    G, P_, T = m["glow"], m["plate"], m["trim"]
    out = mark(m, (0, -0.215, 1.34), 0.17)
    for sx in (-1, 1):
        for j in range(3):
            b = (sx * (0.27 + j * 0.06), 0.03 - j * 0.03, 1.62)
            out.append(K.crystal((b[0] + sx * 0.04, b[1], b[2] + 0.12), 0.26 - j * 0.05, 0.022, P_, rot=(-12, sx * -24, 0)))
        out.append(K.ring_tube((sx * 0.31, -0.02, 1.56), 0.06, 0.006, G, axis="x", n=20))
    for sx in (-1, 1):     # light seams down the plate
        pts = [(sx * 0.06, -0.215, 1.48), (sx * 0.1, -0.212, 1.36), (sx * 0.09, -0.218, 1.24), (sx * 0.13, -0.205, 1.12)]
        out.append(K.tube(pts, [0.004, 0.005, 0.004, 0.003], G, n=5))
    return out


def ornaments(slot, m):
    if slot == "helm":
        return helm_ornaments(m)
    if slot == "armor":
        return armor_ornaments(m)
    if slot == "inner_garment":
        return mark(m, (0, -0.16, 1.02), 0.08)
    if slot == "leggings":
        return mark(m, (0.1, -0.12, 0.74), 0.05) + mark(m, (-0.1, -0.12, 0.74), 0.05)
    if slot.startswith("gloves"):
        return mark(m, (0.6, -0.07, 1.445), 0.045)
    if slot.startswith("boots"):
        return mark(m, (0.1, -0.09, 0.36), 0.05)
    if slot == "accessory_1":
        return [K.gem((0.785, -0.03, 1.47), 0.013, m["glow"], rot=(90, 0, 0))]
    if slot == "accessory_3":
        return mark(m, (0, -0.29, 1.255), 0.045)
    if slot == "accessory_4":
        return [K.ring_tube((-0.2, -0.25, 1.43), 0.07, 0.004, m["glow"], axis="y", n=24)] + mark(m, (-0.2, -0.255, 1.43), 0.03)
    if slot == "sub_weapon":
        return mark(m, (0, -0.2, -0.3), 0.13)
    return []


def piece_slot(sid, piece):
    if piece == "accessory":
        return JEWEL_SLOT[COLLECTIONS[sid]["jewel"]]
    return PIECE_SLOT[piece]


# ------------------------------------------------------------------------------------------------- weapons
def _metal(m):
    """On a weapon the cloth-free roles read as metal."""
    return m["plate"], m["trim"], m["glow"], m["leather"], m["gem"]


def weapon_parts(cls, wt, i):
    """Weapon i of a type for a class, in the hand-socket convention (grip at the origin, long axis +Z). Each of the ten
    has its own construction; it wears collection i of the class's palette and the shard ring."""
    import item_weapons as W
    import artisan_weapons as A
    sid = class_sids(cls)[i]
    m = palette(sid)
    B, T, G, L, GEM = _metal(m)
    if wt == "sword":
        if i % 2 == 0:
            parts = AR._remap(A.edged({"design": i, "family": "sword"}), m)
        else:
            parts = W.sword({"len": 0.9 + 0.02 * i, "w": (0.056, 0.03), "shape": ["waisted", "leaf", "falchion", "sabre", "straight"][(i // 2) % 5],
                             "blade": B, "guard": ["winged", "swept", "bar", "disc", "winged"][(i // 2) % 5], "guard_half": 0.15, "guard_mat": T,
                             "grip_mat": L, "pommel": "spike", "pommel_mat": T, "gem": GEM, "glow": G, "lugs": i % 3 == 0, "serrate": i == 7})
    elif wt == "greatsword":
        parts = W.sword({"len": 1.16 + 0.025 * i, "z0": 0.135, "w": (0.07 + 0.004 * (i % 3), 0.046), "thick": 0.009,
                         "shape": ["straight", "waisted", "leaf", "falchion", "straight", "waisted", "leaf", "straight", "waisted", "falchion"][i],
                         "blade": B, "guard": ["winged", "bar", "swept", "winged", "disc"][i % 5], "guard_half": 0.2 + 0.01 * (i % 3), "guard_mat": T,
                         "grip_len": 0.34, "grip_r": 0.018, "grip_mat": L, "pommel": ["disc", "spike", "round"][i % 3], "pommel_mat": T,
                         "gem": GEM, "glow": G, "lugs": i % 2 == 0, "serrate": i in (3, 8), "wave": 0.004 if i == 6 else 0.0})
    elif wt == "axe":
        parts = AR._remap(A.axe({"design": i}), m)
    elif wt == "greataxe":
        parts = W.axe({"two_handed": True, "head": ["moon", "broad", "crescent", "bearded", "cleaver", "tomahawk", "moon", "crescent", "broad", "cleaver"][i],
                       "double": i % 3 != 2, "head_mat": B, "band_mat": T, "haft_mat": T, "spike_mat": T,
                       "head_scale": 1.25 + 0.03 * (i % 4), "glow": G, "pommel": True, "wrap": L})
    elif wt == "spear":
        parts = W.spear({"head": ["leaf", "partisan", "glaive", "trident"][i % 4],
                         "head_len": 0.34 + 0.02 * (i % 4), "head_w": 0.07 + 0.006 * (i % 3), "head_mat": B, "shaft_mat": T,
                         "band_mat": T, "glow": G, "fins": T if i % 4 == 3 else None})
    elif wt == "javelin":
        parts = W.javelin({"head": ["leaf", "barbed", "pilum", "bolt", "sun"][i % 5], "head_len": 0.2 + 0.02 * (i % 3), "head_w": 0.04,
                           "head_mat": B, "shaft_mat": T, "band_mat": T, "glow": G, "fins": T if i >= 5 else None})
    elif wt == "club":
        parts = W.club({"kind": ["flanged", "morningstar", "flanged", "cudgel", "morningstar"][i % 5], "head_mat": B, "flanges": 6 + i % 4,
                        "glow": G, "grip_mat": L, "haft_mat": T, "spikes": True, "spike_mat": T, "wood": T})
    elif wt == "staff":
        parts = W.staff({"head": ["star", "orb", "prongs", "fork", "shards", "crook", "branch", "star", "orb", "shards"][i],
                         "gem": GEM, "wood": T, "metal": T, "band": B})
    elif wt == "wand":
        parts = W.wand({"wood": T, "head": ["claw", "sun", "skull", "orb", "crescent", "shell", "branch", "sun", "claw", "orb"][i],
                        "gem": GEM, "orn": B})
    elif wt == "bow":
        parts = AR._remap(A.bow({"design": i}), m)
    elif wt == "crossbow":
        parts = AR._remap(A.crossbow({"design": i}), m)
    elif wt == "dagger":
        if i % 2 == 0:
            parts = AR._remap(A.edged({"design": i, "family": "dagger"}), m)
        else:
            parts = W.dagger({"len": 0.3 + 0.01 * i, "shape": ["crescent", "kris", "kukri", "skinner", "wide"][(i // 2) % 5], "blade": B,
                              "guard_mat": T, "glow": G, "gem": GEM, "grip_mat": L})
    elif wt == "claw":
        parts = W.claw({"blades": 2 + i % 3, "len": 0.3 + 0.012 * i, "hook": 0.04 + 0.01 * (i % 4), "blade": B, "frame_mat": T, "glow": G,
                        "spikes": i % 2 == 0, "plate_mat": T})
    else:  # knuckles
        parts = W.knuckles({"kind": "cestus" if i % 3 == 1 else "bar", "mat": B, "plate": T, "spikes": 2 + i % 4, "spike_len": 0.03 + 0.004 * (i % 3),
                            "spike_mat": B, "glow": G, "wrap": L, "stud": T})
    # every weapon is chrome to the grip: wood from the artisan designs becomes the black (or gold) chrome trim
    for p in parts:
        src = K.MAT.get(p.mat)
        if src is not None and src[0] in ("BH_Wood",) and p.mat != L:
            p.mat = T
    return parts + weapon_ornaments(wt, parts, m, i)


def weapon_ornaments(wt, parts, m, i):
    """A floating ring of chrome shards (black-chrome hoop, light inside) and a core of light."""
    V = np.vstack([p.V for p in parts])
    lo, hi = V.min(0), V.max(0)
    G, P_, T = m["glow"], m["plate"], m["trim"]
    long_z = wt not in ("bow", "crossbow", "claw", "knuckles")
    if long_z:
        up = 0.86 if wt in ("staff", "wand", "spear", "javelin", "club", "axe", "greataxe") else 0.18
        c = (0.0, 0.0, lo[2] + (hi[2] - lo[2]) * up)
        r = max(0.06, min(0.13, (hi[0] - lo[0]) * 0.55))
    else:
        c = tuple((lo + hi) / 2)
        r = 0.1
    tilt = Rx(20 + 6 * (i % 3))
    out = [K.ring_tube(c, r, 0.006, T, axis="z", n=36).rot(tilt, c), K.ring_tube(c, r * 0.82, 0.004, G, axis="z", n=36).rot(tilt, c)]
    n = 6
    for k in range(n):
        a = math.radians(k * 360.0 / n + 15 * i)
        p = (tilt @ np.array((r * 1.12 * math.cos(a), r * 1.12 * math.sin(a), 0.0))) + np.array(c)
        out.append(K.crystal(tuple(p), 0.05, 0.009, P_, rot=(0, 0, math.degrees(a))))
    out.append(K.sphere(0.018, c, G, 10, 8))
    return out


# ------------------------------------------------------------------------------------------------- build
def build_piece(sid, piece, mirror=False):
    m = palette(sid)
    slot = piece_slot(sid, piece)
    if mirror:
        slot = slot[:-1] + "2"
    if piece in ("gloves", "boots"):
        base_slot = slot[:-1] + "1"
        parts = RG.piece_parts(sid, base_slot, m) + ornaments(base_slot, m)
        if mirror:
            parts = [p.mirrored(False) for p in parts]
            for p in parts:
                p.bone = RG.swap_bone(p.bone)
    else:
        parts = RG.piece_parts(sid, slot, m) + ornaments(slot, m)
    return RG.to_frame(parts, slot)


def todo(classes, what):
    """(kind, a, b, mirror): ("piece", sid, piece, mirror) and ("weapon", class, type, index)."""
    out = []
    for cls in classes:
        if "armour" in what:
            for sid in class_sids(cls):
                for piece in pieces_of(sid):
                    out.append(("piece", sid, piece, False))
                    if piece in ("gloves", "boots"):
                        out.append(("piece", sid, piece, True))
        if "weapons" in what:
            for wt in WEAPONS[cls]:
                for i in range(10):
                    out.append(("weapon", cls, wt, i))
    return out


def export_models(jobs, log=print):
    import json
    sys.path.insert(0, K.CHARS)
    from build import reset
    report = []
    for kind, a, b, x in jobs:
        reset()
        if kind == "piece":
            iid = item_id(a, b)
            parts = build_piece(a, b, x)
            path = os.path.join(ITEMS_DIR, iid + ("_R" if x else "") + ".glb")
        else:
            iid = weapon_id(a, b, x)
            parts = weapon_parts(a, b, x)
            path = os.path.join(ITEMS_DIR, iid + ".glb")
        obs = RG.objects_for(iid, parts)
        RG._export(path, obs)
        tris = sum(M.tri_count(o) for o in obs)
        report.append({"id": os.path.basename(path)[:-4], "tris": tris, "objects": [o.name for o in obs]})
        log("[eschaton] %-50s %6d tris" % (os.path.basename(path), tris))
    out = os.path.join(ROOT, "work", "lemondev", "bh-041", "evidence")
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "eschaton_models_%d.json" % len(report)), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1)
    return report


def _chrome_world():
    """A studio sky for the icons: a light floor, a dark horizon band and a bright top, so mirror chrome has something
    to reflect (in a flat grey world it renders as dull grey, in a dark one as black)."""
    import bpy
    w = bpy.context.scene.world
    nt = w.node_tree
    bg = nt.nodes.get("Background")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    rng = nt.nodes.new("ShaderNodeMapRange")          # direction z in -1..1 -> 0..1
    rng.inputs["From Min"].default_value = -1.0
    rng.inputs["From Max"].default_value = 1.0
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    nt.links.new(sep.outputs["Z"], rng.inputs["Value"])
    nt.links.new(rng.outputs["Result"], ramp.inputs["Fac"])
    els = ramp.color_ramp.elements
    els[0].position = 0.0
    els[0].color = (0.32, 0.33, 0.37, 1)
    els[1].position = 1.0
    els[1].color = (1.7, 1.72, 1.85, 1)
    for pos, col in ((0.46, (0.5, 0.51, 0.56, 1)), (0.5, (0.03, 0.03, 0.04, 1)), (0.53, (0.05, 0.05, 0.07, 1)), (0.58, (0.95, 0.97, 1.08, 1))):
        e = els.new(pos)
        e.color = col
    nt.links.new(ramp.outputs["Color"], bg.inputs[0])
    bg.inputs[1].default_value = 1.0


def render_icons(jobs, raw_dir, log=print):
    import bpy
    from mathutils import Vector
    sys.path.insert(0, K.CHARS)
    from build import reset
    import build_items as B
    os.makedirs(raw_dir, exist_ok=True)
    for kind, a, b, x in jobs:
        if x is True:
            continue        # the right glove / boot has no icon of its own
        reset()
        if kind == "piece":
            iid = item_id(a, b)
            slot = piece_slot(a, b)
            m = palette(a)
            parts = RG.piece_parts(a, slot, m) + ornaments(slot, m)
            if b == "armor":
                parts = [p for p in parts if p.name not in ("cape", "scarf")]
            for p in parts:
                p.bone = None
            pitch, yaw, R = AR.ICON_VIEW[slot]
            if R is not None:
                c = np.mean(np.vstack([p.V for p in parts]), 0)
                for p in parts:
                    p.rot(R, c)
        else:
            iid = weapon_id(a, b, x)
            parts = weapon_parts(a, b, x)
            for p in parts:
                p.bone = None
        obs = RG.objects_for(iid, parts, textured=True)
        cam = B._studio(256)
        _chrome_world()
        if kind == "weapon":
            pitch, yaw = B._pose_for({"category": "weapon", "weapon_type": b, "id": iid}, obs[0])
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
    classes = [a for a in argv if a in CLASSES] or CLASSES
    what = [a for a in argv if a in ("armour", "weapons")] or ["armour", "weapons"]
    limit = [a for a in argv if a.startswith("limit=")]
    jobs = todo(classes, what)
    if limit:
        jobs = jobs[:int(limit[0][6:])]
    raw = os.environ.get("BH_ESC_RAW", os.path.join(ROOT, "work", "lemondev", "bh-041", "scratch", "icons_raw"))
    if "models" in targets:
        export_models(jobs)
    if "icons" in targets:
        render_icons(jobs, raw)
    print("[eschaton] done", len(jobs), "jobs")


if __name__ == "__main__":
    main()
