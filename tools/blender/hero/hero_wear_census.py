"""Triangles and materials of worn pieces, part by part (no export):

  blender -b --factory-startup --python tools/blender/hero/hero_wear_census.py -- <ids>
"""
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import hero_wear  # noqa: E402,F401  (registers every module)
import hero_wear_kit as WK  # noqa: E402


def tris(p):
    return sum(len(f) - 2 for f in p.F)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    for i in argv:
        parts = WK.REGISTRY[i]["fn"]()
        if isinstance(parts, dict):
            parts = [p for ps in parts.values() for p in ps]
        by = defaultdict(int)
        mats = defaultdict(int)
        for p in parts:
            by[p.name] += tris(p)
            mats[p.mat] += tris(p)
        total = sum(by.values())
        print("[census] %s %d tris, %d materials" % (i, total, len(mats)))
        for k, v in sorted(by.items(), key=lambda kv: -kv[1])[:12]:
            print("   %-16s %6d" % (k, v))
        print("   mats:", dict(mats))


main()
