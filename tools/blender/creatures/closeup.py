"""Workbench close-up of a humanoid character module (rest pose) for detail checks.

  python3 closeup.py <character> --z 0.95 --dist 1.2 --views 0,40,90,180 [--pitch 8] [--out DIR] [--clip NAME --t 0.5]
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CHAR = os.path.join(HERE, "..", "characters")
sys.path.insert(0, CHAR)

import bpy  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("character")
    ap.add_argument("--z", type=float, default=1.0)
    ap.add_argument("--dist", type=float, default=1.5)
    ap.add_argument("--views", default="0,40,90,180")
    ap.add_argument("--pitch", type=float, default=8)
    ap.add_argument("--res", type=int, default=360)
    ap.add_argument("--clip", default="")
    ap.add_argument("--t", type=float, default=0.0)
    ap.add_argument("--out", default="/tmp/claude-0/prevC")
    a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:])
    import build_chars as BC
    import preview_enemy as PE
    bpy.ops.wm.read_factory_settings(use_empty=True)
    res = BC.build_character(a.character, with_actions=bool(a.clip), only={a.clip} if a.clip else None)
    PE.material_colors()
    cam = PE.setup(a.res)
    if a.clip:
        arm = res["armature"]
        act = res["actions"][a.clip]
        ad = arm.animation_data or arm.animation_data_create()
        ad.action = act
        try:
            if ad.action_slot is None and len(act.slots):
                ad.action_slot = act.slots[0]
        except Exception:
            pass
        bpy.context.scene.frame_set(int(round(a.t * act.frame_range[1])))
    tiles = []
    os.makedirs(a.out, exist_ok=True)
    for v in [float(x) for x in a.views.split(",")]:
        PE.place(cam, (0, 0, a.z), a.dist, v, a.pitch)
        p = os.path.join(a.out, f"_cu_{int(v)}.png")
        bpy.context.scene.render.filepath = p
        bpy.ops.render.render(write_still=True)
        tiles.append(p)
    from PIL import Image
    sheet = Image.new("RGB", (len(tiles) * a.res, a.res))
    for i, p in enumerate(tiles):
        sheet.paste(Image.open(p).convert("RGB"), (i * a.res, 0))
    out = os.path.join(a.out, f"{a.character}_closeup{('_' + a.clip) if a.clip else ''}.png")
    sheet.save(out)
    print("CLOSEUP", out)


if __name__ == "__main__":
    main()
