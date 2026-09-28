"""Validate the dungeon floor plans in game/src/data/data_dungeons.gd (bh-012): row widths, stair feet/heads,
markers on walkable cells, everything reachable from the arrival portal. Prints one line per floor."""
import re
import sys
from collections import deque

SRC = open(r"A:\Python\beyond-heroes\game\src\data\data_dungeons.gd", encoding="utf-8").read()
DIRS = {"^": (0, -1), "v": (0, 1), "<": (-1, 0), ">": (1, 0)}

floors = re.findall(r'\{"name": "([^"]+)",(.*?)"plan": \[(.*?)\]\}', SRC, re.S)
bad = 0


def v2(s):
    return tuple(int(x) for x in re.findall(r"-?\d+", s))


for name, head, plan_s in floors:
    rows = re.findall(r'"([^"]*)"', plan_s)
    W = len(rows[0])
    errs = []
    if any(len(r) != W for r in rows):
        errs.append("row widths %s" % [len(r) for r in rows])
    H = len(rows)

    def ch(c, r):
        if 0 <= r < H and 0 <= c < len(rows[r]):
            return rows[r][c]
        return "."

    # heights: floors, bridges; stairs by walking back to the foot
    hgt = {}
    for r in range(H):
        for c in range(W):
            k = ch(c, r)
            if k in "012":
                hgt[(c, r)] = int(k) * 4.0
            elif k == "=":
                hgt[(c, r)] = 0.0
    stairs = {}
    for r in range(H):
        for c in range(W):
            k = ch(c, r)
            if k in DIRS:
                dx, dy = DIRS[k]
                n = 0
                cc, rr = c, r
                while ch(cc, rr) == k:
                    cc -= dx
                    rr -= dy
                    n += 1
                foot = (cc, rr)
                if ch(*foot) not in "012=":
                    errs.append("stair %s foot %s is '%s'" % ((c, r), foot, ch(*foot)))
                    continue
                base = hgt.get(foot, 0.0) + (n - 1) * 2.0
                stairs[(c, r)] = (k, base)
                # head check at the run's top
                if ch(c + dx, r + dy) != k:
                    head_c = (c + dx, r + dy)
                    top = base + 2.0
                    if ch(*head_c) not in "012" or abs(int(ch(*head_c)) * 4.0 - top) > 0.01:
                        errs.append("stair %s head %s '%s' expected height %.0f" % ((c, r), head_c, ch(*head_c), top))
    # connectivity from arrival
    m = re.search(r'"arrival": Vector2i\(([^)]*)\)', head)
    arrival = v2(m.group(1))

    def walkable(p):
        return ch(*p) in "012=" or ch(*p) in DIRS

    def neighbours(p):
        c, r = p
        k = ch(c, r)
        for d, (dx, dy) in (("n", (0, -1)), ("s", (0, 1)), ("w", (-1, 0)), ("e", (1, 0))):
            q = (c + dx, r + dy)
            if not walkable(q):
                continue
            a = ch(*q)
            # stair cells connect only along their direction
            if k in DIRS and (dx, dy) not in (DIRS[k], (-DIRS[k][0], -DIRS[k][1])):
                continue
            if a in DIRS and (dx, dy) not in (DIRS[a], (-DIRS[a][0], -DIRS[a][1])):
                continue
            h1 = hgt.get(p) if p in hgt else None
            h2 = hgt.get(q) if q in hgt else None
            if h1 is not None and h2 is not None and abs(h1 - h2) > 0.01:
                continue
            yield q

    seen = {arrival}
    dq = deque([arrival])
    while dq:
        p = dq.popleft()
        for q in neighbours(p):
            if q not in seen:
                seen.add(q)
                dq.append(q)
    allw = [(c, r) for r in range(H) for c in range(W) if walkable((c, r))]
    lost = [p for p in allw if p not in seen]
    if lost:
        errs.append("unreachable cells %s" % lost[:8])
    for key in ("arrival", "descent", "exit", "seal", "miniboss", "boss"):
        mm = re.search(r'"%s": Vector2i\(([^)]*)\)' % key, head)
        if mm:
            p = v2(mm.group(1))
            if ch(*p) not in "012":
                errs.append("%s %s on '%s'" % (key, p, ch(*p)))
    for mm in re.finditer(r'\[Vector2i\(([^)]*)\), (?:"[ab]"|\d)', head):
        p = v2(mm.group(1))
        if ch(*p) not in "012":
            errs.append("marker %s on '%s'" % (p, ch(*p)))
    levels = sorted({int(k) for r in rows for k in r if k in "012"})
    print("%-28s %2dx%-2d storeys %s  cells %3d  %s" % (name, W, H, levels, len(allw), "OK" if not errs else "; ".join(errs)))
    bad += bool(errs)
print("floors:", len(floors), "bad:", bad)
sys.exit(1 if bad else 0)
