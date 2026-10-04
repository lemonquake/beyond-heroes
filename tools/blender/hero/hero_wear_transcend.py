"""Class Transcendence: the twelve class armours, worn (slot `armor`, ids = the item bases in
game/src/data/data_transcendence_gear.gd). Each class dresses its own way, in its own colours
(game/src/data/data_transcendence.gd themes), so the class reads from across a fight:

  Royal Guard      royal-blue cuirass, gold trim, a crown on the breast, a blue tabard, a short blue shoulder cape
  Dark General     blackened plate, crimson trim, spiked shard pauldrons, a tall gorget, crimson tassets, a long
                   tattered crimson cape
  Grand Paladin    white plate with gold trim, sun pauldrons, a sun on the breast, a white tabard bordered in gold, a
                   long gold cape
  Tracker          a moss-green jerkin, amber rivets, a bandolier of pouches, a fur-trimmed hood rolled on the shoulders
  Wildwarden       a deep-green jerkin, bark pauldrons with leaves, a collar of leaves, a split green cape
  Starstrider      a midnight-blue long coat scattered with silver stars, a star on the breast, a high collar
  Arcanist         a violet robe with silver trim, a rune-stitched stole down the front, an amethyst clasp
  Archmage         a sapphire robe, a white mantle set with ruby, sapphire and topaz, a long sapphire cape
  Void Sovereign   an indigo robe, a tall flared collar, a dark layered mantle, a tattered indigo cape
  Nightstalker     a plum leather harness with crossed straps, a cowl, one layered pauldron, a trailing scarf
  Phantom Reaper   a grey-violet layered mantle over a dark harness, a crescent clasp, a long pale tattered cape
  Blood Sovereign  a garnet long coat with tails, black trim, a crimson sash, a blood-moon clasp, a high collar

Built with the torso kit (hero_wear_torso: body-fitted cloth and plate, robes, tabards) and the boss-set pieces
(boss_regalia: pauldrons, emblems, mantles), in the hero's rest space. Capes hang from the shoulders behind the back:
the chest carries the top, the hips more of the hem (they swing less than the chest when the hero leans).
"""
import math

import numpy as np

import boss_regalia as R
import hero_wear_kit as WK
import hero_wear_torso as T
from hero_wear_kit import K, M, item, pal, attach
from bh_math import Rx, Ry, Rz  # noqa: F401


def hexc(h):
    return WK.srgb(h)


def cloth_m(key, hexcol, rough=0.85):
    return pal("tc_" + key, "BH_Cloth_Secondary", hexc(hexcol), 0.0, rough)


def leather_m(key, hexcol, rough=0.62):
    return pal("tc_" + key, "BH_Leather", hexc(hexcol), 0.0, rough)


def plate_m(key, hexcol, metallic=0.5, rough=0.34):
    """A worn plate: part metallic only (a mirror plate reads black under the game's night sky)."""
    return pal("tc_" + key, "BH_Steel", hexc(hexcol), metallic, rough)


def gold_m(key="gold", hexcol="d8b04e"):
    return pal("tc_" + key, "BH_Gold", hexc(hexcol), 0.55, 0.32)


def gem_m(key, hexcol, glow=0.6):
    c = hexc(hexcol)
    return pal("tc_" + key, "BH_Gem", c, 0.0, 0.1, c, glow)


def mats(plate, trim, cloth, leather=None, horn=None, glow=None, gem=None, dark=None):
    """The role -> palette key table boss_regalia's pieces read."""
    return {"plate": plate, "trim": trim, "cloth": cloth, "leather": leather or pal("darkleather"), "horn": horn or trim,
            "glow": glow or gem or trim, "gem": gem or trim, "dark": dark or pal("darkleather"), "mail": WK.mail()}


def _motif(tag, motif):
    """boss_regalia's pauldron reads its motif from SETS; register one for a class."""
    R.SETS.setdefault(tag, {"motif": motif})
    return tag


def regalia_pauldrons(m, motif="none", big=True, left_only=False):
    """boss_regalia's pauldron (an arched plate and lames, with the motif's crest), on both shoulders."""
    tag = _motif("tc_" + motif, motif)
    parts = R.pauldron(tag, m, big)
    left = T.rigid_mix(parts, [("upper_arm.L", 0.8), ("shoulder.L", 0.2)])
    return left if left_only else WK.both(left)


def chest_y(z=1.3, x=0.0, out=0.03):
    """y just in front of the breast at height z (outside a cuirass `out` metres off the body)."""
    return T.front_y(z, x, frame=T.TRUNK) - out


def emblem_on_chest(motif, size, m, z=1.3, out=0.034, depth=0.012):
    return attach(R.front_emblem(motif, size, m, (0.0, chest_y(z, 0.0, out), z), depth), bone="chest")


# ---- light parts (the class armours carry capes and tabards, so their own plates are kept lean) ----------------------
def cuirass(plate, trim, belt_m, under, sleeve_to=0.36):
    """hero_wear_torso._plate without its dome pauldrons (each class has its own) and with leaner trims: an arming
    coat below the cuirass and down the upper arm, breast and back plates, a ridge, three fauld lames, a gorget."""
    coat = T.cloth(T.region(trunk=(0.84, 0.975), arms=(0.19, sleeve_to)), T.hem_off(0.010, 0.84), under, "arming", relax=6)
    S0 = T.surf(coat)
    sel = T.region(trunk=(0.93, 1.515))
    cuir = T.cloth(sel, 0.021, plate, "cuirass", relax=14)
    raw = T.cloth(sel, 0.021, plate, "cuirass", relax=14, rim=False)
    S = T.surf(cuir)
    parts = [coat, cuir] + T.edge_cords(raw, trim, 0.0045, 22)
    ridge = T.vband(0.0, 0.96, 1.46, 0.012, trim, S, 0.0025, 6, frame=T.TRUNK)
    fauld = []
    top = S
    for i in range(3):
        z0 = 0.95 - i * 0.045
        lame = T.skirt(z0, z0 - 0.06, plate, top, (0.003 + 0.001 * i, 0.012 + 0.002 * i), n=18, steps=1, flare=0.004, thick=0.0,
                       name="fauld")
        top = T.surf(lame)
        fauld += [lame, T.hoop(z0 - 0.056, 0.008, trim, top, 0.0015, 18, T.HIPS)]
    parts += attach([ridge], bone="chest") + attach(fauld, weights=T.skw(z_top=0.96, z_knee=0.62, leg=0.6))
    parts += attach(T.belt(0.955, 0.99, belt_m, S0, 0.018, n=20, clasp=trim), bones=["hips", "spine"], k=8)
    parts += attach([T.collar(1.49, 1.555, plate, 0.018, n=14, lip=0.006)], k=8)
    return parts


def jerkin(face, rivet, trim, belt_m, clasp, skirt_to=None, rivet_rows=6):
    """hero_wear_torso._brigandine with leaner trims and fewer rivets: a sleeveless riveted coat, a belt."""
    sel = T.region(vest=(0.84, 1.53, 0.215), notch=(1.47, 0.045))
    coat = T.cloth(sel, T.hem_off(0.0135, 0.84, 0.003), face, "coat", relax=9)
    raw = T.cloth(sel, T.hem_off(0.0135, 0.84, 0.003), face, "coat", relax=9, rim=False)
    S = T.surf(coat)
    parts = [coat] + T.edge_cords(raw, trim, 0.0045, 26)
    pts = []
    for z in np.linspace(0.95, 1.38, rivet_rows):
        for x in (-0.13, -0.07, 0.07, 0.13):
            pts.append((x, T.front_y(z, x, S, frame=T.TRUNK) - 0.001, z))
    parts += attach([T.studs(pts, lambda q: (0.0, -0.02, q[2]), 0.0048, rivet)], k=6)
    parts += attach(T.belt(0.975, 1.03, belt_m, S, 0.004, n=20, clasp=clasp), bones=["hips", "spine"], k=8)
    if skirt_to:
        tail = T.skirt(0.99, skirt_to, face, S, (0.003, 0.02), n=20, steps=3, flare=0.02)
        parts += attach([tail, T.hoop(skirt_to + 0.012, 0.022, trim, T.surf(tail), 0.002, 20, T.HIPS)], weights=T.skw(z_top=0.6 + 0.4, z_knee=0.6, leg=0.9))
    return parts


def _arch(x0, x1, rows, mat, zc=1.455, arc=220.0, thick=0.01, n=12, name="pauldron"):
    """An arched plate over the upper arm (boss_regalia.arm_arch without the bevel)."""
    rings = []
    for t, r, lift in rows:
        x = x0 + (x1 - x0) * t
        rings.append(np.array([(x, -r * math.cos(a), zc + lift + r * math.sin(a))
                               for a in np.radians(np.linspace(90 - arc / 2, 90 + arc / 2, n))]))
    V, F = M.loft(rings, cap0=False, cap1=False, closed=False)
    p = M.Part(V, F, mat, name=name)
    M.recalc_normals(p)
    return M.solidify(p, thick, offset=1.0)


def _arc_trim(x, r, mat, zc=1.455, arc=220.0, lift=0.0, n=12, tube=0.005):
    pts = [(x, -r * math.cos(a), zc + lift + r * math.sin(a)) for a in np.radians(np.linspace(90 - arc / 2, 90 + arc / 2, n))]
    return K.tube(pts, [tube] * len(pts), mat, n=4, up=(1, 0, 0), name="trim")


def pauldrons(plate, trim, big=True, crest=None, left_only=False):
    """Layered pauldrons over both shoulders: a great arched plate, two lames below it, trim on every edge; `crest`
    returns extra parts for the left one (spikes, a sun, leaves ...)."""
    if big:
        parts = [_arch(0.17, 0.36, [(0.0, 0.13, 0.03), (0.3, 0.15, 0.03), (0.7, 0.152, 0.012), (1.0, 0.135, -0.01)], plate, arc=230, thick=0.012)]
        parts.append(_arc_trim(0.172, 0.135, trim, arc=230, lift=0.03))
        for i, x in enumerate((0.35, 0.395)):
            r = 0.122 - i * 0.012
            parts.append(_arch(x, x + 0.05, [(0.0, r, -0.012 - i * 0.004), (1.0, r - 0.006, -0.016 - i * 0.004)], plate, arc=200, thick=0.008,
                               n=10, name="lame"))
            parts.append(_arc_trim(x + 0.05, r - 0.004, trim, arc=200, lift=-0.016 - i * 0.004, n=10, tube=0.0045))
    else:
        parts = [_arch(0.19, 0.33, [(0.0, 0.11, 0.02), (0.4, 0.125, 0.015), (1.0, 0.11, 0.0)], plate, arc=200, thick=0.009, n=10, name="spaulder")]
        parts.append(_arc_trim(0.33, 0.108, trim, arc=200, n=10))
        parts.append(_arc_trim(0.19, 0.11, trim, arc=200, lift=0.02, n=10))
    if crest:
        parts += crest()
    left = T.rigid_mix(parts, [("upper_arm.L", 0.8), ("shoulder.L", 0.2)])
    return left if left_only else WK.both(left)


def sun(gold, gem, size, center, face=(0.0, -1.0, 0.0), rays=8):
    """A sun: a flattened gold disc with a gem and `rays` points (faces -Y by default)."""
    cx, cy, cz = center
    out = [K.sphere(0.32 * size, (0, 0, 0), gold, 8, 4, scale=(1, 0.3, 1))]
    for i in range(rays):
        a = math.radians(i * 360.0 / rays)
        L = 0.85 if i % 2 == 0 else 0.62
        out.append(K.cone_spike((0.28 * size * math.cos(a), 0.0, 0.28 * size * math.sin(a)),
                                (L * size * math.cos(a), 0.0, L * size * math.sin(a)), 0.07 * size, gold, n=4))
    if gem:
        out.append(K.gem((0.0, -0.1 * size, 0.0), 0.16 * size, gem, rot=(90, 0, 0)))
    if face[1] > 0:
        R.xform(out, Rz(180.0))
    return R.xform(out, None, (cx, cy, cz))


def flat(outline, depth, mat):
    """A flat cut shape (stars, leaves, crescents) without a bevel."""
    return K.slab(outline, depth, mat, axis="y")


# ---- capes -------------------------------------------------------------------------------------------------------------
def cape_weights(z_top=1.5, z_bot=0.4):
    """The chest holds the top of a cape; down the cape the hips take a growing share (half at the hem)."""
    ic, isp, ih = (WK.BONES.index(n) for n in ("chest", "spine", "hips"))

    def fn(V):
        W = np.zeros((len(V), len(WK.BONES)))
        t = np.clip((z_top - V[:, 2]) / max(z_top - z_bot, 1e-6), 0.0, 1.0)
        W[:, ic] = 1.0 - 0.75 * t
        W[:, isp] = 0.25 * t
        W[:, ih] = 0.5 * t
        return W / W.sum(1, keepdims=True)
    return fn


def cape(cloth, trim, length=1.05, width=0.2, flare=0.5, kind="long", z_top=1.5, y0=0.19, clasp=None, lining=None, back=None,
         sides=True):
    """A cloak hanging from the shoulders behind the back: kind "long" (straight hem), "tattered" (torn hem), "split"
    (two halves), "short" (a shoulder cape). A trim cord runs along the top between the clasps and down the sides;
    back=(motif, size, mats) sets an emblem on the cape's back."""
    parts = []
    halves = (-1, 1) if kind == "split" else (0,)
    nu, nv = 7, 10 if length > 0.6 else 6
    for h in halves:
        def fn(u, v, h=h):
            if kind == "split":
                x0, x1 = (-width, -0.012) if h < 0 else (0.012, width)
            else:
                x0, x1 = -width, width
            x = (x0 + (x1 - x0) * u) * (1.0 + flare * v)
            z = z_top - v * length
            y = y0 + 0.05 * v + 0.025 * math.sin(u * math.pi * 3 + v) * v - 0.035 * (1 - abs(2 * u - 1)) * (1 - v) ** 2
            if kind == "tattered" and v > 0.9:
                z += 0.055 * (abs(math.sin(u * 23.0 + h)) - 0.5)
            if kind == "short":
                z -= 0.04 * (1 - (2 * u - 1) ** 2) * v ** 2
            return (x, y, z)
        V, F = M.grid(fn, nu, nv)
        cl = M.Part(V, F, cloth, name="cape")
        M.recalc_normals(cl)
        parts.append(M.solidify(cl, 0.012, offset=0.0))
        if lining:
            V2, F2 = M.grid(lambda u, v, fn=fn: tuple(np.array(fn(u, v)) + np.array((0.0, -0.007, 0.0))), nu, nv)
            ln = M.Part(V2, F2, lining, name="lining")
            M.recalc_normals(ln)
            parts.append(ln)
    top = R.curve([(-width - 0.005, y0, z_top), (0.0, y0 - 0.03, z_top + 0.03), (width + 0.005, y0, z_top)], 4)
    parts.append(K.tube(top, [0.011] * len(top), trim, n=6, up=(0, 0, 1)))
    if clasp:
        for sx in (-1, 1):
            parts.append(K.sphere(0.022, (sx * (width + 0.005), y0 - 0.005, z_top), clasp, 10, 6, scale=(1, 0.6, 1)))
    if kind != "split":
        hem_v = 1.0
        hem = []
        for i in range(17):
            u = i / 16
            x = (-width + 2 * width * u) * (1.0 + flare * hem_v)
            z = z_top - length + (0.0 if kind != "short" else -0.04 * (1 - (2 * u - 1) ** 2))
            y = y0 + 0.05 + 0.025 * math.sin(u * math.pi * 3 + 1)
            if kind == "tattered":
                continue
            hem.append((x, y, z + 0.006))
        if hem:
            parts.append(K.tube(hem[::2], [0.0065] * len(hem[::2]), trim, n=4, up=(0, 0, 1), name="cape_hem"))
    if sides and kind != "split":
        for u in (0.0, 1.0):
            edge = []
            for j in range(13):
                v = j / 12
                x = (-width + 2 * width * u) * (1.0 + flare * v)
                y = y0 + 0.05 * v + 0.025 * math.sin(u * math.pi * 3 + v) * v
                z = z_top - v * length
                if kind == "tattered" and v > 0.9:
                    break
                edge.append((x, y + 0.002, z))
            parts.append(K.tube(edge[::2] + ([edge[-1]] if len(edge) % 2 == 0 else []), [0.0065] * (len(edge[::2]) + (1 if len(edge) % 2 == 0 else 0)),
                                trim, n=4, up=(0, 1, 0), name="cape_side"))
    if back:
        zc = z_top - min(0.36, length * 0.4)
        v = (z_top - zc) / length
        yc = y0 + 0.05 * v + 0.025 * math.sin(0.5 * math.pi * 3 + v) * v + 0.013
        parts += back((0.0, yc, zc))
    return attach(parts, weights=cape_weights(z_top, z_top - length))


# ---- tabards and tassets -------------------------------------------------------------------------------------------
def tabard(face, border, z_top=1.0, z_bot=0.5, half=0.11, back=True, grow=0.046, grow1=0.075, hem="point"):
    """A cloth panel hanging over the fauld, front (and back), with a border of another cloth or metal behind it."""
    parts = []
    for bk in ((False, True) if back else (False,)):
        parts.append(T.panel(-half, half, z_top, z_bot, face, None, grow, nu=5, nv=7, flare=0.18, hem=hem, back=bk, thick=0.004,
                             grow1=grow1, name="tabard"))
        parts.append(T.panel(-half - 0.012, half + 0.012, z_top + 0.005, z_bot - 0.016, border, None, grow - 0.003, nu=5, nv=7,
                             flare=0.18, hem=hem, back=bk, thick=0.003, grow1=grow1 - 0.003, name="tabard_border"))
    return attach(parts, weights=T.skw(z_top=1.0, z_knee=0.51, z_bot=z_bot, centre=0.09, leg=0.75))


def tassets(face, trim, count=4, z_top=0.97, z_bot=0.56, grow=0.04, grow1=0.07, back=True):
    """Cloth strips hanging round the hips (front, sides and back), each with a trim strip down its middle."""
    parts = []
    xs = np.linspace(-0.13, 0.13, count)
    for bk in ((False, True) if back else (False,)):
        for x in xs:
            parts.append(T.panel(x - 0.034, x + 0.034, z_top, z_bot - 0.03 * abs(x) / 0.13, face, None, grow, nu=2, nv=6, flare=0.1,
                                 hem="point", back=bk, thick=0.003, grow1=grow1, name="tasset"))
            parts.append(T.panel(x - 0.006, x + 0.006, z_top - 0.01, z_bot + 0.02, trim, None, grow + 0.004, nu=2, nv=6, back=bk, thick=0.0,
                                 grow1=grow1 + 0.004, name="tasset_trim"))
    return attach(parts, weights=T.skw(z_top=1.0, z_knee=0.51, z_bot=z_bot, centre=0.09, leg=0.8))


def crown(gold, gem, z=1.31, out=0.036, w=0.06):
    """A small crown standing on the breastplate: a band, five points, three gems (Royal Guard)."""
    y = chest_y(z, 0.0, out)
    parts = [K.box(w * 2, 0.012, 0.026, (0.0, y, z), gold, 0.003)]
    for i, x in enumerate(np.linspace(-w * 0.9, w * 0.9, 5)):
        h = 0.05 if i % 2 == 0 else 0.034
        parts.append(K.cone_spike((x, y, z + 0.012), (x, y - 0.002, z + 0.012 + h), 0.011, gold))
        if i % 2 == 0:
            parts.append(K.sphere(0.008, (x, y - 0.003, z + 0.016 + h), gold, 8, 5))
    for x in (-w * 0.5, 0.0, w * 0.5):
        parts.append(K.gem((x, y - 0.008, z), 0.009, gem, rot=(90, 0, 0)))
    return attach(parts, bone="chest")


def spikes_on_pauldrons(mat, count=3, top=1.6):
    """Short upswept spikes along the crest of both pauldrons (Dark General)."""
    parts = []
    for i in range(count):
        x = 0.22 + i * 0.055
        parts.append(K.cone_spike((x, 0.0, top - 0.02 - i * 0.015), (x + 0.05, 0.015, top + 0.085 - i * 0.025), 0.02, mat))
    return WK.both(T.rigid_mix(parts, [("upper_arm.L", 0.8), ("shoulder.L", 0.2)]))


def gorget(plate, trim, z0=1.5, z1=1.62, flare=0.03):
    """A tall plate collar standing round the neck."""
    rows = [(z0, 0.16, 0.165, 0.15), (z0 + (z1 - z0) * 0.5, 0.12 + flare * 0.3, 0.13 + flare * 0.3, 0.125 + flare * 0.3),
            (z1, 0.115 + flare, 0.125 + flare, 0.12 + flare)]
    parts = [R.shell(rows, plate, n=20, p=2.2, thick=0.009, bevel=0.0, name="gorget"),
             R.band_trim(z1, 0.115 + flare, 0.125 + flare, 0.12 + flare, trim, 0.006, n=20, p=2.2)]
    return attach(parts, k=8)


def rolled_hood(cloth, trim, fur=None):
    """A hood worn down: a thick roll of cloth round the back of the neck and over the shoulders, a fur edge."""
    pts = R.curve([(-0.17, -0.02, 1.5), (-0.12, 0.09, 1.56), (0.0, 0.13, 1.58), (0.12, 0.09, 1.56), (0.17, -0.02, 1.5)], 5)
    parts = [K.tube(pts, [0.045, 0.05] + [0.055] * (len(pts) - 4) + [0.05, 0.045], cloth, n=10, up=(0, 0, 1), name="hood_roll")]
    if fur:
        for i, p in enumerate(pts[::3]):
            parts.append(K.sphere(0.03, (p[0], p[1] - 0.02, p[2] + 0.03), fur, 8, 5, scale=(1.3, 1.0, 0.8)))
    parts.append(K.tube(R.curve([(-0.17, -0.06, 1.48), (0.0, -0.17, 1.42), (0.17, -0.06, 1.48)], 4), [0.006] * 9, trim, n=5, up=(0, -1, 0)))
    return attach(parts, bones=["chest", "neck"], k=8)


def bandolier(strap, pouch, buckle, sx=1.0):
    """A strap from one shoulder across the chest to the other hip, three pouches on it."""
    pts = [(sx * 0.19, chest_y(1.47, sx * 0.19, 0.012), 1.47), (sx * 0.06, chest_y(1.3, sx * 0.06, 0.03), 1.3),
           (-sx * 0.08, chest_y(1.13, -sx * 0.08, 0.03), 1.13), (-sx * 0.2, chest_y(1.0, -sx * 0.2, 0.02), 1.0)]
    c = R.curve(pts, 4)
    parts = [K.tube(c, [(0.02, 0.005)] * len(c), strap, n=6, up=(0, -1, 0), name="bandolier")]
    for t in (0.3, 0.5, 0.7):
        p = c[int(t * (len(c) - 1))]
        parts.append(K.box(0.04, 0.022, 0.034, (p[0], p[1] - 0.014, p[2]), pouch, 0.004))
        parts.append(K.box(0.012, 0.006, 0.012, (p[0], p[1] - 0.027, p[2] + 0.006), buckle))
    return attach(parts, k=6)


def leaf_collar(leaf, n=11, z=1.47, r=0.2, L=0.13):
    """A ring of leaves lying on the shoulders and breast (Wildwarden)."""
    parts = []
    for i in range(n):
        a = math.radians(-180.0 + i * 360.0 / n)
        c, s = math.cos(a), math.sin(a)
        org = (r * c * 0.95, r * 0.8 * s - 0.01, z)
        lf = flat(R.leaf_outline(L, 0.04, n=7), 0.004, leaf)
        parts += R.xform([lf], Rz(math.degrees(a) + 90.0) @ Rx(-62.0), org)
    return attach(parts, bones=["chest", "shoulder.L", "shoulder.R"], k=8)


def stole(face, trim, rune, x=0.065, z0=1.47, z1=0.62):
    """Two bands of cloth over the shoulders and down the front of a robe, runes stitched on them (Arcanist)."""
    parts = []
    for sx in (-1, 1):
        parts.append(T.panel(sx * x - 0.025, sx * x + 0.025, 1.0, z1, face, None, 0.03, nu=2, nv=7, flare=0.05, hem="point", thick=0.003,
                             grow1=0.05, name="stole_lo"))
        for i in range(4):
            zz = 0.95 - i * 0.08
            parts.append(K.box(0.014, 0.004, 0.026, (sx * x, T.front_y(zz, sx * x) - 0.038 - 0.02 * (i / 3), zz), rune))
    up = []
    for sx in (-1, 1):
        up.append(T.vband(sx * x, 1.0, z0, 0.05, face, None, 0.026, 6, frame=T.TRUNK))
        for i in range(3):
            zz = 1.12 + i * 0.1
            up.append(K.box(0.014, 0.004, 0.026, (sx * x, T.front_y(zz, sx * x, frame=T.TRUNK) - 0.03, zz), rune))
    return attach(parts, weights=T.skw(z_top=1.0, z_knee=0.51, z_bot=z1, centre=0.09, leg=0.6)) + attach(up, bone="chest")


def tall_collar(face, trim, z0=1.48, z1=1.72, w=0.17):
    """A tall stiff collar flaring up behind the head, open at the front (Void Sovereign)."""
    rows = [(z0, w - 0.02, 0.16, 0.15), (z0 + 0.08, w + 0.01, 0.17, 0.17), (z1, w + 0.06, 0.2, 0.22)]
    parts = [R.shell(rows, face, n=28, p=2.0, a0=-40.0, a1=220.0, thick=0.008, name="collar_tall"),
             R.band_trim(z1, w + 0.06, 0.2, 0.22, trim, 0.0055, n=28, p=2.0, a0=-40.0, a1=220.0)]
    return attach(parts, bones=["chest", "neck"], k=8)


def mantle(cloth, trim, w=0.3, z_top=1.57, drop=0.08):
    """boss_regalia's soft shoulder mantle with its trimmed hem."""
    parts = R.mantle_shell({"cloth": cloth, "trim": trim}, w, z_top, drop, n=28, nv=5)
    if not isinstance(parts, list):
        parts = [parts]
    return attach(parts, bones=["chest", "shoulder.L", "shoulder.R", "upper_arm.L", "upper_arm.R"], k=8)


def scarf(cloth, L=(0.7, 0.55)):
    """A long scarf: a loop round the neck, two tails trailing behind (Nightstalker)."""
    parts = [K.ring_tube((0, 0.0, 1.52), 1.0, 0.028, cloth, axis="z", n=26).scale((0.15, 0.16, 1), (0, 0, 1.52))]
    for sx, l in ((-1, L[0]), (1, L[1])):
        pts = [(sx * 0.07, 0.15, 1.5), (sx * 0.1, 0.21, 1.3), (sx * 0.12, 0.26, 1.08), (sx * 0.14, 0.29, 1.5 - l)]
        c = R.curve(pts, 4)
        parts.append(K.tube(c, [(0.05, 0.007)] * len(c), cloth, n=8, up=(0, 1, 0), name="scarf"))
    return attach(parts, weights=cape_weights(1.5, 0.8))


def cross_straps(strap, buckle, z_hi=1.47, z_lo=1.04):
    parts = []
    for sx in (1.0, -1.0):
        pts = [(sx * 0.19, chest_y(z_hi, sx * 0.19, 0.014), z_hi), (sx * 0.05, chest_y(1.3, sx * 0.05, 0.03), 1.3),
               (-sx * 0.1, chest_y(1.14, -sx * 0.1, 0.03), 1.14), (-sx * 0.19, chest_y(z_lo, -sx * 0.19, 0.02), z_lo)]
        c = R.curve(pts, 4)
        parts.append(K.tube(c, [(0.017, 0.005)] * len(c), strap, n=6, up=(0, -1, 0)))
    parts.append(K.box(0.034, 0.012, 0.034, (0.0, chest_y(1.27, 0.0, 0.04), 1.27), buckle, 0.004))
    return attach(parts, k=6)


def cowl(cloth, trim):
    rows = [(1.47, 0.2, 0.19, 0.18), (1.53, 0.17, 0.17, 0.16), (1.6, 0.13, 0.135, 0.135)]
    return attach([R.shell(rows, cloth, n=30, p=2.1, thick=0.012, name="cowl"), R.band_trim(1.6, 0.13, 0.135, 0.135, trim, 0.005, p=2.1)],
                  bones=["chest", "neck"], k=8)


def sash(face, z=1.0, tail=0.6, x=0.1):
    """A sash knotted at the left hip, its ends hanging (Blood Sovereign)."""
    parts = T.belt(z - 0.035, z + 0.035, face, None, 0.03, clasp=None)
    knot = K.sphere(0.03, (x, T.front_y(z, x) - 0.04, z), face, 10, 6, scale=(1.2, 0.8, 1.0))
    ends = [T.panel(x - 0.03 + d, x + 0.0 + d, z - 0.01, tail - d * 2, face, None, 0.035, nu=2, nv=6, flare=0.15, hem="point", thick=0.003,
                    grow1=0.05, name="sash_end") for d in (0.0, 0.035)]
    return attach(parts + [knot], bones=["hips", "spine"], k=8) + attach(ends, weights=T.skw(z_top=1.0, z_knee=0.51, z_bot=tail, leg=0.7))


# ====================================================================================================================
# Knight family
# ====================================================================================================================
PLATE_HIDE = {"z": [0.865, 1.49], "sleeve": [0.23, 0.29]}


@item("tc_royal_guard_cuirass", hide=PLATE_HIDE, skirt=0.80)
def royal_guard_cuirass():
    blue = plate_m("rg_blue", "3d63c2", 0.45, 0.3)
    gold = gold_m("rg_gold", "d8b46a")
    cloth = cloth_m("rg_cloth", "2c4c9e")
    gem = gem_m("rg_gem", "4a78e8", 0.5)
    parts = cuirass(blue, gold, pal("darkleather"), cloth, sleeve_to=0.31)
    parts += pauldrons(blue, gold, big=True)
    parts += crown(gold, gem)
    parts += tabard(cloth, gold, z_top=1.0, z_bot=0.55, half=0.1, hem="point", back=False)
    parts += cape(cloth, gold, length=0.55, width=0.21, flare=0.35, kind="short", clasp=gold)
    return parts


@item("tc_black_dominion_plate", hide=PLATE_HIDE, skirt=0.80)
def black_dominion_plate():
    black = plate_m("dg_black", "2b2b33", 0.45, 0.42)
    crimson = pal("tc_dg_crimson_trim", "BH_Steel", hexc("9e2a3e"), 0.4, 0.36)
    cloth = cloth_m("dg_cloth", "7d1e30")
    m = mats(black, crimson, cloth, horn=pal("tc_dg_horn", "BH_DarkSteel", hexc("1a1a1f"), 0.5, 0.45), gem=gem_m("dg_gem", "c9566c", 0.4))
    parts = cuirass(black, crimson, pal("darkleather"), cloth, sleeve_to=0.31)

    def shards():
        out = []
        for i, h in enumerate((0.15, 0.21, 0.13)):
            x = 0.2 + i * 0.05
            sh = [(-0.02, 0), (0.024, 0), (0.012, h * 0.7), (0.0, h), (-0.012, h * 0.5)]
            out += R.xform([flat(sh, 0.014, m["horn"])], Ry(-20 - i * 8), (x, 0.0, 1.6))
        return out
    parts += pauldrons(black, crimson, big=True, crest=shards)
    parts += gorget(black, crimson, 1.5, 1.63, 0.03)
    parts += attach([K.tube(R.curve([(0, chest_y(1.08, 0, 0.028), 1.08), (0, chest_y(1.3, 0, 0.04), 1.3), (0, chest_y(1.46, 0, 0.03), 1.46)], 4),
                            [0.009] * 9, crimson, n=6, up=(1, 0, 0))], bone="chest")
    parts += tassets(cloth, crimson, count=3, z_top=0.95, z_bot=0.56, back=False)
    parts += cape(cloth, crimson, length=1.1, width=0.22, flare=0.55, kind="tattered", clasp=crimson)
    return parts


@item("tc_sanctified_plate", hide=PLATE_HIDE, skirt=0.80)
def sanctified_plate():
    white = plate_m("gp_white", "ece6d6", 0.3, 0.32)
    gold = gold_m("gp_gold", "e5bd64")
    white_cloth = cloth_m("gp_white_cloth", "f1ece0", 0.8)
    gold_cloth = pal("tc_gp_gold_cloth", "BH_Cloth_Secondary", hexc("f2c64a"), 0.35, 0.42)
    holy = gem_m("gp_gem", "ffd27a", 0.6)
    m = mats(white, gold, white_cloth, horn=gold, glow=holy, gem=holy)
    parts = cuirass(white, gold, gold, white_cloth, sleeve_to=0.31)
    parts += pauldrons(white, gold, big=True, crest=lambda: sun(gold, None, 0.07, (0.27, -0.16, 1.47)))
    parts += attach(sun(gold, holy, 0.085, (0.0, chest_y(1.3, 0.0, 0.036), 1.3)), bone="chest")
    parts += tabard(white_cloth, gold, z_top=1.0, z_bot=0.5, half=0.115, hem="point", back=False)
    parts += cape(gold_cloth, white_cloth, length=1.18, width=0.22, flare=0.5, kind="long", clasp=gold, lining=white_cloth,
                  back=lambda c: sun(white_cloth, None, 0.15, c, face=(0.0, 1.0, 0.0), rays=12))
    return parts


# ====================================================================================================================
# Hunter family
# ====================================================================================================================
VEST_HIDE = {"z": [0.865, 1.46]}


@item("tc_trackers_leathers", hide=VEST_HIDE)
def trackers_leathers():
    moss = leather_m("tr_moss", "5a7a45")
    amber = gold_m("tr_amber", "d5b86a")
    tan = leather_m("tr_tan", "8a6a44")
    parts = jerkin(moss, amber, tan, pal("darkleather"), amber)
    parts += bandolier(pal("darkleather"), tan, amber)
    hood = cloth_m("tr_hood", "4d6a3c")
    parts += rolled_hood(hood, amber, fur=tan)
    parts += cape(hood, amber, length=0.62, width=0.2, flare=0.4, kind="short", clasp=amber)
    return parts


@item("tc_livingwood_leathers", hide=VEST_HIDE, skirt=0.62)
def livingwood_leathers():
    green = leather_m("ww_green", "2f6b52")
    jade = pal("tc_ww_jade", "BH_Cloth_Secondary", hexc("8cc28a"), 0.0, 0.7)
    bark = pal("tc_ww_bark", "BH_Wood", hexc("5a4630"), 0.0, 0.75)
    cloth = cloth_m("ww_cloth", "2e5e48")
    m = mats(bark, jade, cloth, horn=bark)
    parts = jerkin(green, bark, jade, bark, bark, skirt_to=0.62)

    def leaves():
        out = []
        for i in range(3):
            out += R.xform([flat(R.leaf_outline(0.15 - i * 0.015, 0.04, n=7), 0.005, jade)], Ry(-60 - i * 14) @ Rx(-10), (0.22 + i * 0.035, 0.02, 1.53))
        return out
    parts += pauldrons(bark, jade, big=False, crest=leaves)
    parts += leaf_collar(jade)
    parts += cape(cloth, jade, length=1.0, width=0.2, flare=0.45, kind="split")
    return parts


@item("tc_constellation_leathers", hide={"z": [0.885, 1.49], "sleeve": [0.23, 0.70]}, skirt=0.42)
def constellation_leathers():
    night = cloth_m("ss_night", "26305e")
    silver = pal("tc_ss_silver", "BH_Steel", hexc("c9d4e6"), 0.5, 0.25)
    star = gem_m("ss_star", "cfeaff", 0.5)
    m = mats(night, silver, night, glow=star, gem=star)
    parts = T._robe(night, silver, pal("darkleather"), 0.42, bell_to=0.0, open_front=True, belt_clasp=silver, stars=star)
    parts += attach(R.xform([flat(R.star_outline(0.05, 0.02), 0.008, silver)], None, (0.0, chest_y(1.32, 0.0, 0.026), 1.32)), bone="chest")
    parts += pauldrons(night, silver, big=False, left_only=True,
                       crest=lambda: R.xform([flat(R.star_outline(0.04, 0.016), 0.008, silver)], None, (0.26, -0.13, 1.47)))
    parts += attach([T.collar(1.5, 1.6, night, 0.016, lip=0.006)], k=8)
    return parts


# ====================================================================================================================
# Mage family
# ====================================================================================================================
ROBE_HIDE = {"z": [0.885, 1.49], "sleeve": [0.23, 0.70]}


@item("tc_arcanist_vestments", hide=ROBE_HIDE, skirt=0.24)
def arcanist_vestments():
    violet = cloth_m("ar_violet", "6e4aa8")
    silver = pal("tc_ar_silver", "BH_Steel", hexc("c7d0e6"), 0.5, 0.25)
    pale = cloth_m("ar_pale", "c9c2e0")
    gem = gem_m("ar_gem", "a07ae6", 0.6)
    parts = T._robe(violet, silver, pale, 0.24, belt_clasp=silver)
    parts += stole(pale, silver, silver)
    parts += attach([K.gem((0.0, chest_y(1.36, 0.0, 0.02), 1.36), 0.016, gem, rot=(90, 0, 0)),
                     K.ring_tube((0.0, chest_y(1.36, 0.0, 0.014), 1.36), 0.026, 0.0035, silver, axis="y", n=20)], bone="chest")
    return parts


@item("tc_archmage_robes", hide=ROBE_HIDE, skirt=0.2)
def archmage_robes():
    sapphire = cloth_m("am_sapphire", "2f5fae")
    white = cloth_m("am_white", "e6ebf4", 0.8)
    gold = gold_m("am_gold", "d8b04e")
    parts = T._robe(sapphire, gold, white, 0.2, belt_clasp=gold)
    parts += mantle(white, gold, 0.31, 1.575, 0.09)
    for x, g in ((-0.07, gem_m("am_ruby", "d8402e", 0.5)), (0.0, white), (0.07, gem_m("am_topaz", "f0c040", 0.5))):
        parts += attach([K.gem((x, chest_y(1.42, x, 0.06), 1.42), 0.013, g, rot=(90, 0, 0)),
                         K.ring_tube((x, chest_y(1.42, x, 0.054), 1.42), 0.02, 0.003, gold, axis="y", n=10)], bone="chest")
    parts += cape(sapphire, gold, length=1.22, width=0.21, flare=0.5, kind="long", clasp=gold, lining=white)
    return parts


@item("tc_riftwoven_robes", hide=ROBE_HIDE, skirt=0.22)
def riftwoven_robes():
    indigo = cloth_m("vs_indigo", "2a2458")
    pale = pal("tc_vs_pale", "BH_Steel", hexc("b292ea"), 0.4, 0.3)
    dark = cloth_m("vs_dark", "15122b")
    gem = gem_m("vs_gem", "8a62e0", 0.6)
    parts = T._robe(indigo, pale, dark, 0.22, belt_clasp=pale, glow=gem)
    parts += tall_collar(dark, pale)
    parts += mantle(dark, pale, 0.3, 1.57, 0.12)
    parts += cape(indigo, pale, length=1.2, width=0.21, flare=0.55, kind="tattered", lining=dark)
    return parts


# ====================================================================================================================
# Shadowblade family
# ====================================================================================================================
@item("tc_nightstalker_leathers", hide=VEST_HIDE)
def nightstalker_leathers():
    plum = leather_m("ns_plum", "4e2f63")
    steel = pal("tc_ns_steel", "BH_Steel", hexc("adb3c6"), 0.5, 0.3)
    dark = leather_m("ns_dark", "1e1626")
    m = mats(plum, steel, dark)
    parts = jerkin(plum, steel, dark, dark, steel)
    parts += cross_straps(dark, steel)
    parts += cowl(cloth_m("ns_cowl", "3a2550"), steel)
    parts += pauldrons(plum, steel, big=False, left_only=True)
    parts += scarf(cloth_m("ns_scarf", "5a3678"))
    return parts


@item("tc_afterimage_mantle", hide=VEST_HIDE)
def afterimage_mantle():
    grey = cloth_m("pr_grey", "6c6a8e")
    pale = cloth_m("pr_pale", "bedceb", 0.8)
    silver = pal("tc_pr_silver", "BH_Steel", hexc("d0dcea"), 0.5, 0.25)
    dark = leather_m("pr_dark", "2a2838")
    gem = gem_m("pr_gem", "bedceb", 0.4)
    m = mats(grey, silver, grey, glow=gem, gem=gem, dark=dark)
    parts = jerkin(dark, silver, silver, dark, silver)
    parts += mantle(grey, silver, 0.285, 1.57, 0.07)
    parts += attach(R.xform([flat(R.crescent_outline(0.045), 0.008, silver)], None, (0.0, chest_y(1.38, 0.0, 0.07), 1.38)), bone="chest")
    parts += cape(pale, silver, length=1.15, width=0.21, flare=0.6, kind="tattered", lining=grey)
    return parts


@item("tc_sanguine_leathers", hide={"z": [0.885, 1.49], "sleeve": [0.23, 0.70]}, skirt=0.32)
def sanguine_leathers():
    garnet = leather_m("bs_garnet", "7e2638")
    black = leather_m("bs_black", "1a0e12")
    rose = gold_m("bs_rose", "df9c9c")
    crimson = cloth_m("bs_crimson", "9e1f30")
    ruby = gem_m("bs_ruby", "c0283c", 0.6)
    parts = T._robe(garnet, black, black, 0.32, bell_to=0.0, open_front=True, belt_clasp=rose)
    parts += sash(crimson, 1.0, 0.62, 0.1)
    parts += attach([T.collar(1.5, 1.62, garnet, 0.017, flare=0.012, lip=0.006)], k=8)
    parts += attach([K.ring_tube((0.0, chest_y(1.36, 0.0, 0.022), 1.36), 0.03, 0.005, rose, axis="y", n=22),
                     K.sphere(0.024, (0.0, chest_y(1.36, 0.0, 0.026), 1.36), ruby, 14, 8, scale=(1, 0.45, 1))], bone="chest")
    return parts


# ====================================================================================================================
# Class accessories (rings on the fist, pendants on the breastbone, charms at the hip), made like the other jewellery
# (hero_wear_ends) from item specs in each class's metals and stones
# ====================================================================================================================
import hero_wear_ends as E  # noqa: E402
import item_gear as G  # noqa: E402

from transcend_items import JEWELS  # noqa: E402  (shared with the item models)
for _id, _spec in JEWELS.items():
    G.GEAR[_id] = _spec
    E._jewel_item(_id)
