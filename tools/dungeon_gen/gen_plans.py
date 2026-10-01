"""Beyond Heroes (bh-013): deterministic floor-plan generator for the dungeons in DataDungeonsX.

Writes game/src/data/data_dungeon_plans.gd — one entry per dungeon: a list of floors, each with the plan (rows of
cells, the same grammar as DataDungeons: . void, 0/1/2 storeys, ~ basin, = bridge, ^ < > stairs) and its markers
(arrival, descent/exit, seal/miniboss/boss, camps, chests). Every floor is validated with the bh-012 plan rules
(stairs have a foot and a head at the right heights, every walkable cell is reachable from the arrival portal,
markers stand on floor cells). Same seed -> same plans.

    python tools/dungeon_gen/gen_plans.py            # regenerate and validate
    python tools/dungeon_gen/gen_plans.py --show cellars
"""
import random
import sys
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "game" / "src" / "data" / "data_dungeon_plans.gd"
DIRS = {"^": (0, -1), "v": (0, 1), "<": (-1, 0), ">": (1, 0)}

# id: (tier, floor names, size range (W, H) min/max, basin chance, storey-2 chance)
SPECS = {
    "cellars": (1, ["The Wine Cellars", "Coinwhisper's Counting Room"], (16, 14, 18, 15), 0.3, 0.0),
    "burrows": (1, ["The Muddy Tunnels", "The Gnawing Pits", "Gnashgut's Throne-Heap"], (16, 14, 19, 16), 0.5, 0.1),
    "ossuary": (2, ["Hall of Stacked Bones", "The Candle Crypts", "The Ossuarch's Reliquary"], (16, 14, 19, 17), 0.5, 0.25),
    "warcamp": (2, ["The Palisade Tunnels", "The Blood Pits", "Ironjaw's War Hall"], (17, 14, 20, 17), 0.6, 0.25),
    "hive": (2, ["The Honeyed Galleries", "The Brood Combs", "The Queen's Chamber"], (16, 15, 20, 17), 0.8, 0.35),
    "sump": (3, ["The Overflow", "The Rotting Cisterns", "The Drowned Drains", "The Tyrant's Wallow"], (17, 15, 20, 18), 0.95, 0.3),
    "briar": (3, ["The Thorn Gate", "Gardens of Red Sap", "The Weeping Arbor", "Heart of the Briar"], (17, 15, 20, 18), 0.7, 0.4),
    "dunemourn": (3, ["The Sand-choked Stair", "The Hall of Mirrors", "The Sealed Treasury", "The Sovereign's Tomb"], (17, 15, 21, 18), 0.7, 0.45),
    "thunderwell": (3, ["The Conduit Halls", "The Storm Cisterns", "The Lightning Loft", "The Eye of the Storm"], (17, 15, 21, 18), 0.8, 0.55),
    "undercroft": (4, ["The Lightless Stair", "Crypts of Whispering Shadow", "The Riftworks", "The Hollow Dark"], (18, 15, 21, 18), 0.8, 0.5),
    "geode": (4, ["The Glimmering Hollows", "The Prism Fields", "The Lens of the Deep", "The Colossus Chamber"], (18, 15, 21, 18), 0.8, 0.5),
    "vault": (4, ["The Counting Halls", "The Coin Rivers", "The Warden's Strongroom", "The Hoard"], (18, 15, 21, 18), 0.85, 0.55),
    "reliquary": (5, ["The Twin Stairs", "The Hall of Oaths", "The Silent Choir", "The Soul Forge", "The Regents' Crypt"], (18, 16, 21, 18), 0.75, 0.6),
    "wyrmcoil": (5, ["The Coil Tunnels", "The Shed Skins", "The Gnawed Deep", "The Wyrm's Gullet", "The Coiled Throne"], (18, 16, 22, 18), 0.8, 0.55),
    "maw": (5, ["The Edge of Nothing", "The Flesh Stair", "The Bleeding Vaults", "The Unmade Halls", "The Maw"], (18, 16, 22, 18), 0.9, 0.65),
}

# bh-028: the five special dungeons behind Kethrax (DataDungeonsSpecial), 10-15 floors each, bigger floors with more
# storeys. `python tools/dungeon_gen/gen_plans.py --special` writes game/src/data/data_dungeon_plans_special.gd.
OUT_SPECIAL = ROOT / "game" / "src" / "data" / "data_dungeon_plans_special.gd"
SPECIAL_SPECS = {
    "prismheart": (6, ["The Glass Gate", "The Shimmering Galleries", "The Refraction Halls", "Gardens of Quartz", "The Singing Geodes",
                       "The Lattice of Light", "The Shardfall Cascade", "The Mirror Deeps", "The Heart Facet", "The Prismheart"],
                   (19, 16, 23, 19), 0.85, 0.6),
    "underworld": (6, ["The Weeping Stair", "Banks of the Grey Run", "The Ferryman's Wharf", "Fields of Ash", "The Bone Orchard",
                       "Halls of the Unjudged", "The Soulfire Forges", "The Chained Gallery", "The River of Lament", "The Black Gates",
                       "The Court of the Drowned King", "The Throne Below"],
                   (19, 16, 23, 19), 0.95, 0.55),
    "aetherreach": (6, ["The Torn Threshold", "The Skybridge Ruins", "The Drifting Isles", "Halls of Still Wind", "The Lantern Spires",
                        "The Unmoored Library", "The Cloud Cisterns", "The Starwell", "Gardens of Breath", "The Hanging Bastion",
                        "The Tempest Loom", "The Warden's Zenith", "The Aether Heart"],
                    (20, 16, 24, 19), 0.95, 0.7),
    "eclipse": (6, ["The Dimming Door", "The Moonlit Cloisters", "The Silver Stair", "Halls of Half-Light", "The Umbra Pools",
                    "The Orrery of Tides", "The Gallery of Phases", "The Shadow Observatory", "The Sleeping Choir", "The Penumbral Bridge",
                    "The Night Garden", "The Totality Chamber", "The Crescent Throne", "The Eclipse Heart"],
                (20, 16, 24, 20), 0.9, 0.65),
    "solarium": (6, ["The Sunken Atrium", "The Gilded Aqueducts", "The Amber Baths", "Halls of Noon", "The Sunglass Terraces",
                     "The Burning Fountains", "The Lens Gardens", "The Solar Foundry", "The Dawn Chapel", "The Halo Galleries",
                     "The Golden Cistern", "The Mirror of Midday", "The Pyre Colonnade", "The Sunwarden's Rest", "The Drowned Sun"],
                 (20, 16, 24, 20), 0.95, 0.7),
}

# bh-029: the three Vaults of Zarael (DataDungeonsZarael), 7 floors each, big floors with high galleries.
# `python tools/dungeon_gen/gen_plans.py --zarael` writes game/src/data/data_dungeon_plans_zarael.gd.
OUT_ZARAEL = ROOT / "game" / "src" / "data" / "data_dungeon_plans_zarael.gd"
ZARAEL_SPECS = {
    "jade_sepulchre": (6, ["The Serpent Stair", "Halls of the Wrapped Dead", "The Jade Cisterns", "Gallery of Green Fire",
                           "The Feathered Crypts", "The Sleeping Court", "The Jade Throne"],
                       (19, 16, 23, 19), 0.85, 0.6),
    "obsidian_engine": (6, ["The Glass Furnaces", "The Copper Sluices", "The Piston Halls", "The Slag Galleries",
                            "The Black Mirror Works", "The Turbine Crypt", "The Engine Heart"],
                        (20, 16, 24, 19), 0.9, 0.65),
    "veinworks": (6, ["The Wound in the Stone", "The Marrow Tunnels", "The Pulse Galleries", "The Sinew Bridges",
                      "The Chained Arteries", "The Hollow of the Ribs", "The Giant's Heart"],
                  (20, 16, 24, 20), 0.95, 0.7),
}

# ------------------------------------------------------------------------------------------------ validation

def heights(rows):
    H, W = len(rows), len(rows[0])
    hgt = {}
    for r in range(H):
        for c in range(W):
            k = rows[r][c]
            if k in "012":
                hgt[(c, r)] = int(k) * 4.0
            elif k == "=":
                hgt[(c, r)] = 0.0
    return hgt


def ch(rows, c, r):
    if 0 <= r < len(rows) and 0 <= c < len(rows[r]):
        return rows[r][c]
    return "."


def validate(rows, markers):
    """bh-012 rules. Returns (errors, walkable cell count, reachable dict cell -> BFS distance)."""
    errs = []
    H, W = len(rows), len(rows[0])
    if any(len(r) != W for r in rows):
        return ["row widths"], 0, {}
    hgt = heights(rows)
    for r in range(H):
        for c in range(W):
            k = ch(rows, c, r)
            if k not in DIRS:
                continue
            dx, dy = DIRS[k]
            n, cc, rr = 0, c, r
            while ch(rows, cc, rr) == k:
                cc -= dx
                rr -= dy
                n += 1
            foot = (cc, rr)
            if ch(rows, *foot) not in "012=":
                errs.append("stair %s foot %s" % ((c, r), foot))
                continue
            base = hgt.get(foot, 0.0) + (n - 1) * 2.0
            if ch(rows, c + dx, r + dy) != k:
                head = (c + dx, r + dy)
                top = base + 2.0
                hk = ch(rows, *head)
                if hk not in "012" or abs(int(hk) * 4.0 - top) > 0.01:
                    errs.append("stair %s head %s" % ((c, r), head))

    def walk(p):
        return ch(rows, *p) in "012=" or ch(rows, *p) in DIRS

    def nbrs(p):
        c, r = p
        k = ch(rows, c, r)
        for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
            q = (c + dx, r + dy)
            if not walk(q):
                continue
            a = ch(rows, *q)
            if k in DIRS and (dx, dy) not in (DIRS[k], (-DIRS[k][0], -DIRS[k][1])):
                continue
            if a in DIRS and (dx, dy) not in (DIRS[a], (-DIRS[a][0], -DIRS[a][1])):
                continue
            h1, h2 = hgt.get(p), hgt.get(q)
            if h1 is not None and h2 is not None and abs(h1 - h2) > 0.01:
                continue
            yield q

    arrival = markers["arrival"]
    dist = {arrival: 0}
    dq = deque([arrival])
    while dq:
        p = dq.popleft()
        for q in nbrs(p):
            if q not in dist:
                dist[q] = dist[p] + 1
                dq.append(q)
    allw = [(c, r) for r in range(H) for c in range(W) if walk((c, r))]
    lost = [p for p in allw if p not in dist]
    if lost:
        errs.append("unreachable %s" % lost[:6])
    for key in ("arrival", "descent", "exit", "seal", "miniboss", "boss"):
        if key in markers and ch(rows, *markers[key]) not in "012":
            errs.append("%s on '%s'" % (key, ch(rows, *markers[key])))
    for cp in markers.get("camps", []):
        if ch(rows, *cp[0]) not in "012":
            errs.append("camp on '%s'" % ch(rows, *cp[0]))
    for cp in markers.get("chests", []):
        if ch(rows, *cp[0]) not in "012":
            errs.append("chest on '%s'" % ch(rows, *cp[0]))
    cells = [m for k, m in markers.items() if k in ("arrival", "descent", "exit", "seal", "miniboss", "boss")]
    cells += [cp[0] for cp in markers.get("camps", [])] + [cp[0] for cp in markers.get("chests", [])]
    if len(cells) != len(set(cells)):
        errs.append("markers share a cell")
    return errs, len(allw), dist


# ------------------------------------------------------------------------------------------------ generation

class Room:
    def __init__(self, x, y, w, h, s):
        self.x, self.y, self.w, self.h, self.s = x, y, w, h, s

    def cells(self):
        return [(c, r) for r in range(self.y, self.y + self.h) for c in range(self.x, self.x + self.w)]

    def center(self):
        return (self.x + self.w // 2, self.y + self.h // 2)

    def overlaps(self, o, gap=1):
        return not (self.x + self.w + gap <= o.x or o.x + o.w + gap <= self.x or
                    self.y + self.h + gap <= o.y or o.y + o.h + gap <= self.y)


class Floor:
    def __init__(self, W, H):
        self.W, self.H = W, H
        self.g = [["."] * W for _ in range(H)]
        self.rooms = []

    def get(self, c, r):
        if 0 <= r < self.H and 0 <= c < self.W:
            return self.g[r][c]
        return "#"

    def put_room(self, room):
        for c, r in room.cells():
            self.g[r][c] = str(room.s)
        self.rooms.append(room)

    def rows(self):
        return ["".join(r) for r in self.g]


def inside(fl, c, r):
    return 1 <= c < fl.W - 1 and 1 <= r < fl.H - 1


def carve(fl, cells, s, stairs=None):
    """Carve corridor cells at storey s (and stair cells); False (nothing changed) when it would cut through
    something of another storey or leave the grid."""
    stairs = stairs or {}
    want = {}
    for p in cells:
        if not inside(fl, *p):
            return False
        want[p] = str(s)
    for p, k in stairs.items():
        if not inside(fl, *p):
            return False
        want[p] = k
    for (c, r), k in want.items():
        cur = fl.get(c, r)
        if cur == ".":
            continue
        if cur != k:
            return False
    # a new stair cell must not touch other walkable cells sideways at its own run height... (allowed by rules);
    # a corridor must not open sideways onto a stair flight of another run
    for (c, r), k in want.items():
        if k in "012":
            for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
                nk = fl.get(c + dx, r + dy)
                if nk in DIRS and (c + dx, r + dy) not in want:
                    return False
    for (c, r), k in want.items():
        fl.g[r][c] = k
    return True


def seg(a, b):
    """Cells from a to b inclusive along one axis."""
    (x0, y0), (x1, y1) = a, b
    out = []
    if x0 == x1:
        step = 1 if y1 >= y0 else -1
        for y in range(y0, y1 + step, step):
            out.append((x0, y))
    else:
        step = 1 if x1 >= x0 else -1
        for x in range(x0, x1 + step, step):
            out.append((x, y0))
    return out


def widen(cells, horizontal):
    out = []
    for c, r in cells:
        out.append((c, r))
        out.append((c, r + 1) if horizontal else (c + 1, r))
    return out


def connect(fl, a, b, rng):
    """Join rooms a and b with a 2-wide corridor. Equal storeys: an L of floor. b one storey above a: the corridor
    runs at a's storey and climbs into b through a 2-cell flight on b's south (^), west (>) or east (<) side."""
    if abs(a.s - b.s) > 1:
        return False
    if b.s < a.s:
        a, b = b, a
    if a.s == b.s:
        ax, ay = a.center()
        bx, by = b.center()
        for first_h in ([True, False] if rng.random() < 0.5 else [False, True]):
            snap = [row[:] for row in fl.g]
            if first_h:
                cells = widen(seg((ax, ay), (bx, ay)), True) + widen(seg((bx, ay), (bx, by)), False)
            else:
                cells = widen(seg((ax, ay), (ax, by)), False) + widen(seg((ax, by), (bx, by)), True)
            if carve(fl, cells, a.s):
                return True
            fl.g = snap
        return False
    # climbing into b: try the south face first (flights rise toward north, the camera's favourite)
    options = []
    if a.y > b.y + b.h + 2:
        options.append("south")
    if a.x + a.w <= b.x - 3 or a.x >= b.x + b.w + 3 or True:
        options += ["west", "east"]
    rng.shuffle(options)
    if "south" in options:
        options.remove("south")
        options.insert(0, "south")
    for side in options:
        snap = [row[:] for row in fl.g]
        ax, ay = a.center()
        if side == "south":
            if b.w < 2:
                continue
            x = rng.randint(b.x, b.x + b.w - 2)
            head_r = b.y + b.h            # first row south of b
            st = {(x, head_r): "^", (x + 1, head_r): "^", (x, head_r + 1): "^", (x + 1, head_r + 1): "^"}
            foot_r = head_r + 2
            cells = widen(seg((x, foot_r), (x, ay)), False) + widen(seg((ax, ay), (x, ay)), True)
        elif side == "west":
            if b.h < 2:
                continue
            y = rng.randint(b.y, b.y + b.h - 2)
            head_c = b.x - 1
            st = {(head_c, y): ">", (head_c, y + 1): ">", (head_c - 1, y): ">", (head_c - 1, y + 1): ">"}
            foot_c = head_c - 2
            cells = widen(seg((foot_c, y), (ax, y)), True) + widen(seg((ax, y), (ax, ay)), False)
        else:
            if b.h < 2:
                continue
            y = rng.randint(b.y, b.y + b.h - 2)
            head_c = b.x + b.w
            st = {(head_c, y): "<", (head_c, y + 1): "<", (head_c + 1, y): "<", (head_c + 1, y + 1): "<"}
            foot_c = head_c + 2
            cells = widen(seg((foot_c, y), (ax, y)), True) + widen(seg((ax, y), (ax, ay)), False)
        if carve(fl, cells, a.s, st):
            return True
        fl.g = snap
    return False


def place_rooms(fl, rng, want, s2_chance):
    # the great hall first: a wide ground-storey room in the middle band that can hold the basin
    for _ in range(60):
        w = rng.randint(6, min(9, fl.W - 4))
        h = rng.randint(5, 6)
        x = rng.randint(1, fl.W - w - 1)
        y = rng.randint(int(fl.H * 0.4), fl.H - h - 3)
        if y + h <= fl.H - 1:
            fl.put_room(Room(x, y, w, h, 0))
            break
    tries = 0
    while len(fl.rooms) < want and tries < 400:
        tries += 1
        w = rng.randint(3, 7)
        h = rng.randint(3, 5)
        x = rng.randint(1, fl.W - w - 1)
        y = rng.randint(1, fl.H - h - 1)
        cy = y + h / 2
        s = 1 if cy < fl.H * 0.4 else 0
        room = Room(x, y, w, h, s)
        if any(room.overlaps(o, 2) for o in fl.rooms):
            continue
        fl.put_room(room)
    # a third storey: the smallest high room in the far north may climb once more
    if rng.random() < s2_chance:
        highs = [r for r in fl.rooms if r.s == 1 and r.y <= 2]
        if len(highs) >= 2:
            r2 = min(highs, key=lambda r: r.w * r.h)
            r2.s = 2
            for c, r in r2.cells():
                fl.g[r][c] = "2"


def mst_edges(rooms):
    n = len(rooms)
    inn = {0}
    edges = []
    def cost(i, j):
        a, b = rooms[i], rooms[j]
        d = abs(a.center()[0] - b.center()[0]) + abs(a.center()[1] - b.center()[1])
        return d + (999 if abs(a.s - b.s) > 1 else 0)
    while len(inn) < n:
        best = None
        for i in inn:
            for j in range(n):
                if j in inn:
                    continue
                c = cost(i, j)
                if best is None or c < best[0]:
                    best = (c, i, j)
        inn.add(best[2])
        edges.append((best[1], best[2]))
    return edges


def add_basin(fl, rng):
    cands = [r for r in fl.rooms if r.s == 0 and r.w >= 5 and r.h >= 5]
    if not cands:
        # grow the biggest ground room southward/eastward into void to make a hall that can hold a basin
        return False
    room = max(cands, key=lambda r: r.w * r.h)
    inner = [(c, r) for c, r in room.cells() if room.x < c < room.x + room.w - 1 and room.y < r < room.y + room.h - 1]
    for c, r in inner:
        fl.g[r][c] = "~"
    # a bridge across the middle, carried on arches
    if rng.random() < 0.5 and room.w >= 5:
        mid = room.x + room.w // 2
        for r in range(room.y + 1, room.y + room.h - 1):
            fl.g[r][mid] = "="
    else:
        mid = room.y + room.h // 2
        for c in range(room.x + 1, room.x + room.w - 1):
            fl.g[mid][c] = "="
    room.basin = True
    return True


def room_of(fl, p):
    for rm in fl.rooms:
        if rm.x <= p[0] < rm.x + rm.w and rm.y <= p[1] < rm.y + rm.h:
            return rm
    return None


def floor_cells(rm, fl):
    return [p for p in rm.cells() if fl.get(*p) in "012"]


def free_neighbour(fl, p):
    k = fl.get(*p)
    for dx, dy in ((0, 1), (-1, 0), (1, 0), (0, -1)):
        q = (p[0] + dx, p[1] + dy)
        if fl.get(*q) == k:
            return True
    return False


def gen_floor(rng, spec, fi, n_floors):
    tier, names, size, basin_ch, s2_ch = spec
    W = rng.randint(size[0], size[2])
    H = rng.randint(size[1], size[3])
    boss = fi == n_floors - 1
    if boss:
        return gen_boss_floor(rng, W, H, tier, basin_ch)
    fl = Floor(W, H)
    place_rooms(fl, rng, rng.randint(7, 10), s2_ch if fi >= 1 else s2_ch * 0.5)
    if len(fl.rooms) < 5 or not any(r.s >= 1 for r in fl.rooms) or not any(r.s == 0 for r in fl.rooms):
        return None
    ok_all = True
    for i, j in mst_edges(fl.rooms):
        if not connect(fl, fl.rooms[i], fl.rooms[j], rng):
            ok_all = False
            break
    if not ok_all:
        return None
    # a loop or two
    for _ in range(rng.randint(0, 2)):
        i, j = rng.sample(range(len(fl.rooms)), 2)
        connect(fl, fl.rooms[i], fl.rooms[j], rng)
    if rng.random() < basin_ch:
        add_basin(fl, rng)
    return fl, place_markers(fl, rng, tier, fi, n_floors)


def place_markers(fl, rng, tier, fi, n_floors):
    """Arrival in the southernmost ground room; the goal in the room walked farthest from it (preferring height);
    seal/champion beside the goal; camps across the other rooms; chests in far and high rooms."""
    rows = fl.rows()
    ground = [r for r in fl.rooms if r.s == 0]
    arr_room = max(ground, key=lambda r: (r.y + r.h, -abs(r.center()[0] - fl.W // 2)))
    cand = [p for p in floor_cells(arr_room, fl) if free_neighbour(fl, p)]
    cand.sort(key=lambda p: (abs(p[0] - arr_room.center()[0]) + abs(p[1] - arr_room.center()[1])))
    arrival = cand[0]
    _, _, dist = validate(rows, {"arrival": arrival})
    used = {arrival}
    def room_dist(rm):
        ds = [dist[p] for p in floor_cells(rm, fl) if p in dist]
        return min(ds) if ds else -1
    others = [r for r in fl.rooms if r is not arr_room and floor_cells(r, fl)]
    goal_room = max(others, key=lambda r: room_dist(r) + r.s * 6)
    gc = [p for p in floor_cells(goal_room, fl) if free_neighbour(fl, p)]
    gc.sort(key=lambda p: (p[1], abs(p[0] - goal_room.center()[0])))   # north side of the room
    goal = gc[0]
    used.add(goal)
    markers = {"arrival": arrival}
    last = fi == n_floors - 1
    markers["descent" if not last else "exit"] = goal
    keeper = [p for p in floor_cells(goal_room, fl) if p not in used and abs(p[0] - goal[0]) + abs(p[1] - goal[1]) >= 2]
    if not keeper:
        return None
    keeper.sort(key=lambda p: abs(abs(p[0] - goal[0]) + abs(p[1] - goal[1]) - 3))
    kp = keeper[0]
    used.add(kp)
    if fi == n_floors - 2:
        markers["miniboss"] = kp
    else:
        markers["seal"] = kp
    # camps
    camp_rooms = [r for r in others if r is not goal_room]
    rng.shuffle(camp_rooms)
    camp_rooms.sort(key=lambda r: -len(floor_cells(r, fl)))
    n_camps = min(len(camp_rooms), 4 + (1 if fi >= 1 else 0) + (1 if tier >= 4 else 0))
    camps = []
    depth = fi / max(1, n_floors - 2)
    for rm in camp_rooms[:n_camps]:
        cells = [p for p in floor_cells(rm, fl) if p not in used and dist.get(p, 0) >= 4]
        if not cells:
            continue
        cells.sort(key=lambda p: abs(p[0] - rm.center()[0]) + abs(p[1] - rm.center()[1]))
        p = cells[0]
        used.add(p)
        pool = "b" if rng.random() < 0.35 + 0.35 * depth else "a"
        count = rng.randint(3, 4) + (1 if tier >= 3 and rng.random() < 0.5 else 0)
        elite = round(min(0.55, 0.1 + 0.15 * depth + 0.05 * (tier - 1) + rng.uniform(0, 0.05)), 2)
        camps.append([p, pool, count, elite])
    # a ground camp between the arrival and the rest, in the corridor room if one is free
    markers["camps"] = camps
    # chests: the farthest free high cells, one ordinary, one better
    pool = [p for rm in others for p in floor_cells(rm, fl) if p not in used and free_neighbour(fl, p)]
    pool.sort(key=lambda p: -(dist.get(p, 0) + int(fl.get(*p)) * 8))
    chests = []
    for p in pool:
        if len(chests) >= 2:
            break
        if any(abs(p[0] - q[0]) + abs(p[1] - q[1]) < 5 for q, _ in chests):
            continue
        chests.append((p, 1 if int(fl.get(*p)) >= 1 or not chests else 0))
        used.add(p)
    markers["chests"] = [list(c) for c in chests]
    return markers


def gen_boss_floor(rng, W, H, tier, basin_ch):
    """The sanctum: an arrival room in the south, a short passage, the great hall (storey 0, basins in its corners
    or along its flanks), and the dais of the way home on a gallery (storey 1) along the north side, reached by two
    flights rising out of the hall (the reference sanctum layout of bh-012)."""
    H = max(H, 16)
    fl = Floor(W, H)
    cx = W // 2
    ar = Room(cx - 3, H - 4, 6, 3, 0)
    fl.put_room(ar)
    for r in range(H - 6, H - 4):
        for c in (cx - 1, cx):
            fl.g[r][c] = "0"
    hw = W - rng.randint(3, 5)
    hx = (W - hw) // 2
    hy, hh = 3, H - 9
    hall = Room(hx, hy, hw, hh, 0)
    fl.put_room(hall)
    gw = hw - rng.randint(2, 4)
    gx = hx + (hw - gw) // 2
    gal = Room(gx, 1, gw, 2, 1)
    fl.put_room(gal)
    for c in (gx + 1, gx + gw - 2):
        for r in (3, 4):
            fl.g[r][c] = "^"
    if rng.random() < basin_ch:
        if rng.random() < 0.5:
            for (c0, r0) in ((hx, hy + hh - 2), (hx + hw - 2, hy + hh - 2), (hx, hy + 2), (hx + hw - 2, hy + 2)):
                for c in (c0, c0 + 1):
                    for r in (r0, r0 + 1):
                        if fl.g[r][c] == "0" and fl.get(c, r - 1) not in DIRS and fl.get(c, r + 1) not in DIRS                                 and fl.get(c - 1, r) not in DIRS and fl.get(c + 1, r) not in DIRS:
                            fl.g[r][c] = "~"
        else:
            for r in range(hy + 3, hy + hh - 1):
                for c in (hx, hx + hw - 1):
                    fl.g[r][c] = "~"
    arrival = (cx, H - 3)
    exit_ = (cx, 1)
    boss = (cx, hy + hh // 2 + 1)
    chest = (gx + gw - 1, 1)
    if chest == exit_:
        chest = (gx, 1)
    markers = {"arrival": arrival, "exit": exit_, "boss": boss, "camps": [], "chests": [[chest, 2]]}
    return fl, markers


def gen_dungeon(did, specs=None, cell_range=(95, 200)):
    spec = (specs or SPECS)[did]
    names = spec[1]
    n = len(names)
    rng = random.Random("bh013-" + did)
    floors = []
    for fi in range(n):
        for attempt in range(4000):
            res = gen_floor(rng, spec, fi, n)
            if res is None:
                continue
            fl, markers = res
            if markers is None:
                continue
            rows = fl.rows()
            errs, cells, _ = validate(rows, markers)
            if errs:
                continue
            if cells < cell_range[0] or cells > cell_range[1]:
                continue
            if fi < n - 1 and len(markers["camps"]) < (3 if spec[0] == 1 and fi == 0 else 4):
                continue
            if fi < n - 1 and not any(k in "12" for row in rows for k in row):
                continue
            floors.append((names[fi], rows, markers))
            break
        else:
            raise SystemExit("could not generate %s floor %d" % (did, fi + 1))
    return floors


# ------------------------------------------------------------------------------------------------ output

def v(p):
    return "Vector2i(%d, %d)" % (p[0], p[1])


def emit(all_floors, special=False, zarael=False):
    if zarael:
        out = ['class_name DataDungeonPlansZarael',
               '## GENERATED by tools/dungeon_gen/gen_plans.py --zarael (bh-029) — do not edit by hand; change the generator and rerun.',
               '## Floor plans of the three Vaults of Zarael in DataDungeonsZarael (same grammar and markers as DataDungeons).',
               '', 'const PLANS := {']
    elif special:
        out = ['class_name DataDungeonPlansSpecial',
               '## GENERATED by tools/dungeon_gen/gen_plans.py --special (bh-028) — do not edit by hand; change the generator and rerun.',
               '## Floor plans of the five special dungeons in DataDungeonsSpecial (same grammar and markers as DataDungeons).',
               '', 'const PLANS := {']
    else:
        out = ['class_name DataDungeonPlans',
               '## GENERATED by tools/dungeon_gen/gen_plans.py (bh-013) — do not edit by hand; change the generator and rerun.',
               '## Floor plans of the fifteen dungeons in DataDungeonsX (same grammar and markers as DataDungeons).',
               '', 'const PLANS := {']
    for did, floors in all_floors.items():
        out.append('\t&"%s": [' % did)
        for name, rows, m in floors:
            head = '"name": "%s", "arrival": %s' % (name, v(m["arrival"]))
            if "descent" in m:
                head += ', "descent": %s' % v(m["descent"])
            if "exit" in m:
                head += ', "exit": %s' % v(m["exit"])
            for k in ("seal", "miniboss", "boss"):
                if k in m:
                    head += ', "%s": %s' % (k, v(m[k]))
            camps = ", ".join('[%s, "%s", %d, %s]' % (v(c[0]), c[1], c[2], c[3]) for c in m["camps"])
            chests = ", ".join('[%s, %d]' % (v(c[0]), c[1]) for c in m["chests"])
            out.append('\t\t{%s,' % head)
            out.append('\t\t\t"camps": [%s],' % camps)
            out.append('\t\t\t"chests": [%s],' % chests)
            out.append('\t\t\t"plan": [')
            for r in rows:
                out.append('\t\t\t\t"%s",' % r)
            out.append('\t\t\t]},')
        out.append('\t],')
    out.append('}')
    (OUT_ZARAEL if zarael else OUT_SPECIAL if special else OUT).write_text("\n".join(out) + "\n", encoding="utf-8")


def main():
    show = sys.argv[sys.argv.index("--show") + 1] if "--show" in sys.argv else None
    special = "--special" in sys.argv
    zarael = "--zarael" in sys.argv
    specs = ZARAEL_SPECS if zarael else SPECIAL_SPECS if special else SPECS
    all_floors = {}
    total = 0
    for did in specs:
        floors = gen_dungeon(did, specs, (120, 260) if (special or zarael) else (95, 200))
        all_floors[did] = floors
        for i, (name, rows, m) in enumerate(floors):
            errs, cells, _ = validate(rows, m)
            levels = sorted({int(k) for r in rows for k in r if k in "012"})
            print("%-11s F%d %-30s %2dx%-2d storeys %s cells %3d camps %d %s" % (did, i + 1, name, len(rows[0]), len(rows), levels, cells,
                  len(m["camps"]), "OK" if not errs else errs))
            total += 1
            if show == did:
                for r in rows:
                    print("    " + r)
                print("    ", m)
    emit(all_floors, special, zarael)
    print("floors:", total, "->", OUT_ZARAEL if zarael else OUT_SPECIAL if special else OUT)


if __name__ == "__main__":
    main()
