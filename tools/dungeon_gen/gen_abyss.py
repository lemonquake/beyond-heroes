"""Beyond Heroes (bh-042): floor plans of the five Abyss dungeons (DataDungeonsAbyss), 22 floors each.

Same grammar as DataDungeons, plus:
    3   a fourth storey (y = 12 m)
    #   a cracked wall: floor at the height of the cells beside it, closed by a SecretWall until the hero breaks it.
        Every secret room is reached only through its wall (validated).
Floors 1-10 and 12-20: Seal Keepers guard the way down; floors 5, 10, 15 and 20 also hold a warden (a named
champion, DataDungeonsAbyss.WARDENS); floor 11: the gatekeeper's hall (a boss; its fall breaks the seal); floor 21:
the champion; floor 22: the lord's sanctum.

    python tools/dungeon_gen/gen_abyss.py           # regenerate game/src/data/data_dungeon_plans_abyss.gd and validate
    python tools/dungeon_gen/gen_abyss.py --show hollow_crown 3
"""
import random
import sys
from collections import deque
from pathlib import Path

import gen_plans as G

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "game" / "src" / "data" / "data_dungeon_plans_abyss.gd"
DIRS = G.DIRS
FLOORS = 22
GATEKEEPER_FLOOR = 11
WARDEN_FLOORS = (5, 10, 15, 20)

NAMES = {
    "hollow_crown": ["The Sunken Stair", "Halls of the Unburied", "The Candle Vault", "The Ossuary Galleries", "The Weeping Niches",
                     "The Choir of Bones", "The Lightless Nave", "The Hanging Crypts", "The Gilded Charnel", "The King's Tithe",
                     "The Archivist's Index", "The Stacks of Names", "The Marrow Stair", "The Crypt of Heralds", "The Mourning Court",
                     "The Bone Orchard", "The Sealed Reliquary", "The Ash Chapel", "The Court Below", "The Ossuary Gate",
                     "The Antechamber of Crowns", "The Hollow Throne-Crypt"],
    "sunless_cistern": ["The Black Sluice", "The Drowned Stair", "The Overflow Halls", "The Silt Galleries", "The Weir of Bones",
                        "The Pumping Crypt", "The Echoing Tanks", "The Rusted Aqueduct", "The Undertow Vaults", "The Still Reservoir",
                        "The Faceless Gallery", "The Keepers' Locks", "The Barnacle Halls", "The Flooded Chapel", "The Drain of Sorrows",
                        "The Pale Cisterns", "The Deep Weir", "The Choking Stair", "The Reef Vaults", "The Sunless Gate",
                        "The Tide Antechamber", "The Colossus Basin"],
    "ashgrave_foundry": ["The Cold Furnaces", "The Slag Steps", "The Bellows Halls", "The Ash Galleries", "The Cinder Works",
                         "The Crucible Vaults", "The Iron Chapel", "The Quench Pits", "The Smelter's Stair", "The Anvil Court",
                         "The Glutton's Pit", "The Ore Bridges", "The Chain Foundry", "The Ember Crypts", "The Mould Halls",
                         "The Clinker Vaults", "The Pourer's Gallery", "The Burning Stair", "The Hammer Halls", "The Ashgrave Gate",
                         "The Forge Antechamber", "The Tyrant's Crucible"],
    "weeping_bastion": ["The Frozen Postern", "The Widows' Walk", "The Rime Barracks", "The Icebound Armoury", "The Tear Galleries",
                        "The Glacier Stair", "The Hall of Banners", "The Frostbitten Keep", "The Silent Ramparts", "The Lament Cells",
                        "The Shroud's Belfry", "The Hoarfrost Chapel", "The Snowblind Halls", "The Gaol of Winters", "The White Stair",
                        "The Frozen Choir", "The Cold Barbican", "The Last Watch", "The Chain Halls", "The Bastion Gate",
                        "The Winter Antechamber", "The Cell of the Last Winter"],
    "throne_beneath": ["The Nameless Stair", "The Obsidian Galleries", "The Hall of Kneeling", "The Void Cloisters", "The Ash Thrones",
                       "The Starless Nave", "The Unlit Court", "The Crawling Dark", "The Halls of Fealty", "The Black Mirror Vault",
                       "The Fallen Company", "The Oathbreaker's Stair", "The Hollow Regalia", "The Abyssal Choir", "The Last Light",
                       "The Throne Roads", "The Bones of Kings", "The Edge of Names", "The Ember Crypt", "The Throne Gate",
                       "The Wyrm's Antechamber", "The Throne Beneath"],
}
# (W, H) min/max, basin chance, storey-3 chance
SIZES = {"hollow_crown": (22, 18, 26, 22), "sunless_cistern": (22, 18, 26, 22), "ashgrave_foundry": (23, 18, 27, 22),
         "weeping_bastion": (23, 19, 27, 22), "throne_beneath": (24, 19, 28, 23)}
BASIN = {"hollow_crown": 0.45, "sunless_cistern": 0.95, "ashgrave_foundry": 0.75, "weeping_bastion": 0.55, "throne_beneath": 0.7}
STOREY3 = {"hollow_crown": 0.55, "sunless_cistern": 0.5, "ashgrave_foundry": 0.6, "weeping_bastion": 0.7, "throne_beneath": 0.75}

FLOOR = "0123"


# ------------------------------------------------------------------------------------------------ validation (0-3, #)

def ch(rows, c, r):
    return G.ch(rows, c, r)


def secret_height(rows, c, r):
    hs = [int(ch(rows, c + dx, r + dy)) for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)) if ch(rows, c + dx, r + dy) in FLOOR]
    return max(hs) if hs else 0


def heights(rows, walls_open=True):
    hgt = {}
    for r in range(len(rows)):
        for c in range(len(rows[r])):
            k = rows[r][c]
            if k in FLOOR:
                hgt[(c, r)] = int(k) * 4.0
            elif k == "=":
                hgt[(c, r)] = 0.0
            elif k == "#" and walls_open:
                hgt[(c, r)] = secret_height(rows, c, r) * 4.0
    return hgt


def reach(rows, start, walls_open=True):
    hgt = heights(rows, walls_open)

    def walk(p):
        k = ch(rows, *p)
        return k in FLOOR or k == "=" or k in DIRS or (k == "#" and walls_open)

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
    dist = {start: 0}
    dq = deque([start])
    while dq:
        p = dq.popleft()
        for q in nbrs(p):
            if q not in dist:
                dist[q] = dist[p] + 1
                dq.append(q)
    allw = [(c, r) for r in range(len(rows)) for c in range(len(rows[0])) if walk((c, r))]
    return dist, allw


def validate(rows, m):
    errs = []
    W = len(rows[0])
    if any(len(r) != W for r in rows):
        return ["row widths"], 0
    hgt = heights(rows)
    for r in range(len(rows)):
        for c in range(W):
            k = rows[r][c]
            if k not in DIRS:
                continue
            dx, dy = DIRS[k]
            n, cc, rr = 0, c, r
            while ch(rows, cc, rr) == k:
                cc -= dx
                rr -= dy
                n += 1
            foot = (cc, rr)
            if ch(rows, *foot) not in FLOOR + "=":
                errs.append("stair foot %s" % (foot,))
                continue
            base = hgt.get(foot, 0.0) + (n - 1) * 2.0
            if ch(rows, c + dx, r + dy) != k:
                head = (c + dx, r + dy)
                hk = ch(rows, *head)
                if hk not in FLOOR or abs(int(hk) * 4.0 - (base + 2.0)) > 0.01:
                    errs.append("stair head %s" % (head,))
    dist, allw = reach(rows, m["arrival"])
    lost = [p for p in allw if p not in dist]
    if lost:
        errs.append("unreachable %s" % lost[:6])
    shut, _ = reach(rows, m["arrival"], walls_open=False)
    for s in m.get("secrets", []):
        if s["room"][0] in shut:
            errs.append("secret room %s reachable without its wall" % (s["room"][0],))
        if s["wall"] not in dist:
            errs.append("secret wall unreachable")
    keys = ("arrival", "descent", "exit", "seal", "miniboss", "boss", "gatekeeper", "warden")
    for key in keys:
        if key in m and ch(rows, *m[key]) not in FLOOR:
            errs.append("%s on '%s'" % (key, ch(rows, *m[key])))
    cells = [m[k] for k in keys if k in m] + [cp[0] for cp in m.get("camps", [])] + [cp[0] for cp in m.get("chests", [])]
    if len(cells) != len(set(cells)):
        errs.append("markers share a cell")
    goal = m.get("descent", m.get("exit"))
    if goal and goal not in shut:
        errs.append("the way on needs a secret wall")
    return errs, len(allw)


# ------------------------------------------------------------------------------------------------ generation

def place_rooms(fl, rng, want, s3_chance):
    for _ in range(80):
        w = rng.randint(7, min(10, fl.W - 4))
        h = rng.randint(5, 7)
        x = rng.randint(1, fl.W - w - 1)
        y = rng.randint(int(fl.H * 0.55), fl.H - h - 2)
        if y + h <= fl.H - 1:
            fl.put_room(G.Room(x, y, w, h, 0))
            break
    tries = 0
    while len(fl.rooms) < want and tries < 600:
        tries += 1
        w = rng.randint(3, 7)
        h = rng.randint(3, 5)
        x = rng.randint(1, fl.W - w - 1)
        y = rng.randint(1, fl.H - h - 1)
        cy = (y + h / 2) / fl.H
        s = 2 if cy < 0.34 else (1 if cy < 0.62 else 0)
        room = G.Room(x, y, w, h, s)
        if any(room.overlaps(o, 2) for o in fl.rooms):
            continue
        fl.put_room(room)
    # the fourth storey: a high room in the far north climbs once more
    if rng.random() < s3_chance:
        highs = [r for r in fl.rooms if r.s == 2 and r.y <= 3]
        if len(highs) >= 2:
            r3 = min(highs, key=lambda r: r.w * r.h)
            r3.s = 3
            for c, r in r3.cells():
                fl.g[r][c] = "3"


def add_secrets(fl, rng, used, want):
    """Small rooms behind cracked walls, north, east or west of an existing room (never south: the camera looks
    through the low south walls). The link cell becomes '#'."""
    out = []
    rooms = [r for r in fl.rooms if r.s >= 0]
    rng.shuffle(rooms)
    for host in rooms:
        if len(out) >= want:
            break
        for side in rng.sample(["north", "east", "west"], 3):
            w = rng.randint(3, 4)
            h = 3
            if side == "north":
                lx = rng.randint(host.x, host.x + host.w - 1)
                link = (lx, host.y - 1)
                sx, sy = lx - rng.randint(0, w - 1), host.y - 1 - h
            elif side == "east":
                ly = rng.randint(host.y, host.y + host.h - 1)
                link = (host.x + host.w, ly)
                sx, sy = host.x + host.w + 1, ly - rng.randint(0, h - 1)
            else:
                ly = rng.randint(host.y, host.y + host.h - 1)
                link = (host.x - 1, ly)
                sx, sy = host.x - 1 - w, ly - rng.randint(0, h - 1)
            if fl.get(*link) != "." or fl.get(*{"north": (link[0], link[1] + 1), "east": (link[0] - 1, link[1]),
                                                  "west": (link[0] + 1, link[1])}[side]) != str(host.s):
                continue
            room = G.Room(sx, sy, w, h, host.s)
            cells = room.cells()
            if not all(G.inside(fl, *p) for p in cells):
                continue
            # the room and a one-cell margin round it must be empty, except the link
            ok = True
            for c, r in cells:
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        q = (c + dx, r + dy)
                        if q == link:
                            continue
                        if fl.get(*q) not in (".", "#"):
                            ok = False
            # the link's own other sides must be void
            for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
                q = (link[0] + dx, link[1] + dy)
                if q not in cells and fl.get(*q) not in (".", str(host.s)):
                    ok = False
            if not ok:
                continue
            for c, r in cells:
                fl.g[r][c] = str(host.s)
            fl.g[link[1]][link[0]] = "#"
            # the treasure at the far end of the room, never in the doorway behind the wall
            free = [p for p in cells if p not in used and abs(p[0] - link[0]) + abs(p[1] - link[1]) >= 2]
            rng.shuffle(free)
            free.sort(key=lambda p: -(abs(p[0] - link[0]) + abs(p[1] - link[1])))
            if not free:
                continue
            chest = free[0]
            used.add(chest)
            guard = None
            if rng.random() < 0.55 and len(free) > 2:
                guard = free[1]
                used.add(guard)
            out.append({"wall": link, "room": cells, "chest": chest, "guard": guard, "side": side})
            break
    return out


def gen_floor(rng, did, fi):
    W = rng.randint(SIZES[did][0], SIZES[did][2])
    H = rng.randint(SIZES[did][1], SIZES[did][3])
    fl = G.Floor(W, H)
    place_rooms(fl, rng, rng.randint(9, 13), STOREY3[did] if fi >= 2 else STOREY3[did] * 0.4)
    if len(fl.rooms) < 7 or not any(r.s >= 2 for r in fl.rooms) or not any(r.s == 0 for r in fl.rooms):
        return None
    for i, j in G.mst_edges(fl.rooms):
        if not G.connect(fl, fl.rooms[i], fl.rooms[j], rng):
            return None
    for _ in range(rng.randint(1, 3)):
        i, j = rng.sample(range(len(fl.rooms)), 2)
        G.connect(fl, fl.rooms[i], fl.rooms[j], rng)
    if rng.random() < BASIN[did]:
        G.add_basin(fl, rng)
    markers = markers_for(fl, rng, fi)
    if markers is None:
        return None
    return fl, markers


def markers_for(fl, rng, fi):
    n = fi + 1
    rows = fl.rows()
    ground = [r for r in fl.rooms if r.s == 0]
    arr_room = max(ground, key=lambda r: (r.y + r.h, -abs(r.center()[0] - fl.W // 2)))
    cand = [p for p in G.floor_cells(arr_room, fl) if G.free_neighbour(fl, p)]
    cand.sort(key=lambda p: abs(p[0] - arr_room.center()[0]) + abs(p[1] - arr_room.center()[1]))
    arrival = cand[0]
    dist, _ = reach(rows, arrival)
    used = {arrival}

    def room_dist(rm):
        ds = [dist[p] for p in G.floor_cells(rm, fl) if p in dist]
        return min(ds) if ds else -1
    others = [r for r in fl.rooms if r is not arr_room and G.floor_cells(r, fl)]
    goal_room = max(others, key=lambda r: room_dist(r) + r.s * 6)
    gc = [p for p in G.floor_cells(goal_room, fl) if G.free_neighbour(fl, p)]
    gc.sort(key=lambda p: (p[1], abs(p[0] - goal_room.center()[0])))
    goal = gc[0]
    used.add(goal)
    m = {"arrival": arrival, "descent": goal}
    keeper = [p for p in G.floor_cells(goal_room, fl) if p not in used and abs(p[0] - goal[0]) + abs(p[1] - goal[1]) >= 2]
    if not keeper:
        return None
    keeper.sort(key=lambda p: abs(abs(p[0] - goal[0]) + abs(p[1] - goal[1]) - 3))
    m["miniboss" if n == FLOORS - 1 else "seal"] = keeper[0]
    used.add(keeper[0])
    camp_rooms = [r for r in others if r is not goal_room]
    rng.shuffle(camp_rooms)
    camp_rooms.sort(key=lambda r: -len(G.floor_cells(r, fl)))
    depth = fi / (FLOORS - 2)
    camps = []
    for rm in camp_rooms[:min(len(camp_rooms), 6)]:
        cells = [p for p in G.floor_cells(rm, fl) if p not in used and dist.get(p, 0) >= 4]
        if not cells:
            continue
        cells.sort(key=lambda p: abs(p[0] - rm.center()[0]) + abs(p[1] - rm.center()[1]))
        p = cells[0]
        used.add(p)
        pool = "b" if rng.random() < 0.45 + 0.35 * depth else "a"
        camps.append([p, pool, rng.randint(4, 5), round(min(0.7, 0.3 + 0.3 * depth + rng.uniform(0, 0.08)), 2)])
    if len(camps) < 4:
        return None
    m["camps"] = camps
    if n in WARDEN_FLOORS:
        wroom = max(camp_rooms, key=lambda r: len(G.floor_cells(r, fl)))
        wc = [p for p in G.floor_cells(wroom, fl) if p not in used]
        if not wc:
            return None
        m["warden"] = wc[len(wc) // 2]
        used.add(m["warden"])
    pool = [p for rm in others for p in G.floor_cells(rm, fl) if p not in used and G.free_neighbour(fl, p)]
    pool.sort(key=lambda p: -(dist.get(p, 0) + int(fl.get(*p)) * 8))
    chests = []
    for p in pool:
        if len(chests) >= 2:
            break
        if any(abs(p[0] - q[0]) + abs(p[1] - q[1]) < 5 for q, _ in chests):
            continue
        chests.append((p, 1 if int(fl.get(*p)) >= 1 or not chests else 0))
        used.add(p)
    m["chests"] = [list(c) for c in chests]
    secrets = add_secrets(fl, rng, used, rng.randint(1, 3))
    if not secrets:
        return None
    for s in secrets:
        m["chests"].append([s["chest"], 2])
        if s["guard"]:
            m["camps"].append([s["guard"], "b", 3, 0.85])
    m["secrets"] = secrets
    return m


def gen_hall(rng, did, last):
    """Floor 11 (the gatekeeper's hall) and floor 22 (the lord's sanctum): the bh-012 sanctum layout, larger, with a
    side vault behind a cracked wall."""
    W = rng.randint(SIZES[did][0] - 2, SIZES[did][2] - 4)
    H = rng.randint(17, 19)
    fl, m = G.gen_boss_floor(rng, W, H, 6, BASIN[did])
    rows = fl.rows()
    if not last:
        m["descent"] = m.pop("exit")
        m["gatekeeper"] = m.pop("boss")
    used = {m["arrival"], m.get("descent", m.get("exit")), m.get("boss", m.get("gatekeeper"))} | {tuple(c[0]) for c in m["chests"]}
    secrets = add_secrets(fl, rng, used, 1)
    if not secrets:
        return None
    for s in secrets:
        m["chests"].append([s["chest"], 2])
    m["secrets"] = secrets
    return fl, m


def gen_dungeon(did):
    rng = random.Random("bh042-" + did)
    floors = []
    for fi in range(FLOORS):
        n = fi + 1
        for attempt in range(6000):
            if n == GATEKEEPER_FLOOR or n == FLOORS:
                res = gen_hall(rng, did, n == FLOORS)
            else:
                res = gen_floor(rng, did, fi)
            if res is None:
                continue
            fl, m = res
            rows = fl.rows()
            errs, cells = validate(rows, m)
            if errs:
                continue
            if n not in (GATEKEEPER_FLOOR, FLOORS) and not (170 <= cells <= 360):
                continue
            if n not in (GATEKEEPER_FLOOR, FLOORS) and not any(k in "23" for row in rows for k in row):
                continue
            floors.append((NAMES[did][fi], rows, m))
            break
        else:
            raise SystemExit("could not generate %s floor %d" % (did, n))
    return floors


# ------------------------------------------------------------------------------------------------ output

def v(p):
    return "Vector2i(%d, %d)" % (p[0], p[1])


def emit(all_floors):
    out = ['class_name DataDungeonPlansAbyss',
           '## GENERATED by tools/dungeon_gen/gen_abyss.py (bh-042) — do not edit by hand; change the generator and rerun.',
           '## Floor plans of the five Abyss dungeons (DataDungeonsAbyss): DataDungeons grammar plus storey 3 and # (a cracked',
           '## wall hiding a secret room). Markers as DataDungeons, plus "gatekeeper" (floor 11), "warden" (floors 5/10/15/20)',
           '## and "secrets": [{"wall": cell, "side": the room is north/east/west of the wall}].',
           '', 'const PLANS := {']
    for did, floors in all_floors.items():
        out.append('\t&"%s": [' % did)
        for name, rows, m in floors:
            head = '"name": "%s", "arrival": %s' % (name, v(m["arrival"]))
            for k in ("descent", "exit", "seal", "miniboss", "boss", "gatekeeper", "warden"):
                if k in m:
                    head += ', "%s": %s' % (k, v(m[k]))
            camps = ", ".join('[%s, "%s", %d, %s]' % (v(c[0]), c[1], c[2], c[3]) for c in m["camps"])
            chests = ", ".join('[%s, %d]' % (v(c[0]), c[1]) for c in m["chests"])
            secrets = ", ".join('{"wall": %s, "side": "%s"}' % (v(s["wall"]), s["side"]) for s in m.get("secrets", []))
            out.append('\t\t{%s,' % head)
            out.append('\t\t\t"camps": [%s],' % camps)
            out.append('\t\t\t"chests": [%s],' % chests)
            out.append('\t\t\t"secrets": [%s],' % secrets)
            out.append('\t\t\t"plan": [')
            for r in rows:
                out.append('\t\t\t\t"%s",' % r)
            out.append('\t\t\t]},')
        out.append('\t],')
    out.append('}')
    OUT.write_text("\n".join(out) + "\n", encoding="utf-8")


def main():
    show = sys.argv[sys.argv.index("--show") + 1:] if "--show" in sys.argv else None
    all_floors = {}
    total = 0
    for did in NAMES:
        floors = gen_dungeon(did)
        all_floors[did] = floors
        for i, (name, rows, m) in enumerate(floors):
            errs, cells = validate(rows, m)
            st = sorted({int(k) for r in rows for k in r if k in FLOOR})
            print("%-17s F%-2d %-30s %2dx%-2d storeys %s cells %3d camps %d secrets %d %s" % (
                did, i + 1, name, len(rows[0]), len(rows), st, cells, len(m["camps"]), len(m.get("secrets", [])), "OK" if not errs else errs))
            total += 1
            if show and show[0] == did and (len(show) < 2 or int(show[1]) == i + 1):
                for r in rows:
                    print("    " + r)
                print("    ", {k: m[k] for k in m if k != "secrets"}, [s["wall"] for s in m["secrets"]])
    emit(all_floors)
    print("floors:", total, "->", OUT)


if __name__ == "__main__":
    main()
