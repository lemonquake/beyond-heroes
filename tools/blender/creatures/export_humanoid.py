"""Export Builder C's humanoid enemies through build_chars.export_character with the ACTIONS-mode exporter
(glb_export.py explains the bpy 4.4 NLA_TRACKS bug), then check every clip length against the library.

  python3 export_humanoid.py goblin_skulker orc_reaver ogre_crusher
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "characters"))

import build as BLD  # noqa: E402  (characters/build.py: reset(), CHAR_DIR)
import glb_export as GX  # noqa: E402


def main():
    import build_chars as BC
    import bh_library as L
    lib = {a.name: a.length / 30.0 for a in L.library()}
    for name in sys.argv[1:]:
        BLD.reset()
        res = BC.export_character(name, BLD.CHAR_DIR, GX.export_glb)
        path = os.path.join(BLD.CHAR_DIR, name + ".glb")
        bad, got = GX.check_lengths(path, {n: lib[n] for n in res["actions"]})
        print(f"[{name}] {len(got)} animations in the GLB; length mismatches: {bad}")


if __name__ == "__main__":
    main()
