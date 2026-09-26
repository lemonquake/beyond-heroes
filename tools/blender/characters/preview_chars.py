"""Preview / evidence rendering of characters, poses and animation frames (EEVEE), plus sheet composition.

Used by render_previews.py (evidence) and during development:
  blender -b --factory-startup --python preview_chars.py -- --char knight --anims idle_1h,sword_1 --frames hit
          [--res 384] [--out DIR] [--cam 34|front|side|back|iso] [--name sheet] [--cols 6]
--frames: 'hit' (middle of each hit window / release / key), 'even:N' (N evenly spaced), or explicit '0,5,10'
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import bh_anim as A  # noqa: E402
import bh_materials as MT  # noqa: E402
import bh_mesh as M  # noqa: E402
import bh_render as RR  # noqa: E402
import bh_weapons as W  # noqa: E402

CAMS = {  # yaw, pitch, dist, lens, target z
    "front": (0, 6, 5.6, 85, 0.95),
    "34": (35, 10, 5.6, 85, 0.95),
    "side": (90, 6, 5.6, 85, 0.95),
    "back": (180, 8, 5.6, 85, 0.95),
    "iso": (40, 42, 7.5, 60, 0.9),
    "wide": (35, 14, 7.8, 70, 0.8),
    "top": (0, 88, 6.0, 60, 0.9),
}


def weapon_objects(mats, names):
    obs = {}
    for n in names:
        if n and n not in obs:
            ob = M.build_static("W_" + n, W.WEAPONS[n](), mats)
            MT.bake_vertex_ao(ob, rays=12, dist=0.1, strength=0.5)
            obs[n] = ob
    return obs


def attach(arm, ob, bone):
    ob.parent = arm
    ob.parent_type = "BONE"
    ob.parent_bone = bone
    L = arm.data.bones[bone].length
    ob.matrix_parent_inverse = Matrix.Identity(4)
    ob.location = (0, -L, 0)
    ob.rotation_mode = "XYZ"
    ob.rotation_euler = (-math.pi / 2, 0, 0)


class Stage:
    """A built character in a lit scene with weapon props."""

    def __init__(self, char, res=512, samples=16, weapons=None, ground=True):
        import build_chars as BC
        bpy.ops.wm.read_factory_settings(use_empty=True)
        self.res = BC.build_character(char, with_actions=False, preview=True)
        self.char = char
        self.arm = self.res["armature"]
        self.rig = self.res["rig"]
        self.cam = RR.setup_scene(res=res, samples=samples)
        if not ground:
            bpy.data.objects["Ground"].hide_render = True
        mats = MT.make_materials(getattr(self.res["module"], "PALETTE", char), vertex_color=False)
        names = weapons or list(W.WEAPONS)
        self.wobs = weapon_objects(mats, names)
        for ob in self.wobs.values():
            ob.hide_render = True
            ob.hide_viewport = True
        self.acts = {}

    def set_props(self, right=None, left=None):
        for n, ob in self.wobs.items():
            ob.hide_render = True
            ob.parent = None
        # a second sword for dual wield
        for side, n in (("R", right), ("L", left)):
            if not n:
                continue
            key = n
            if side == "L" and n == right:
                key = n + "#L"
                if key not in self.wobs:
                    cp = self.wobs[n].copy()
                    bpy.context.scene.collection.objects.link(cp)
                    self.wobs[key] = cp
            ob = self.wobs[key]
            attach(self.arm, ob, "weapon." + side)
            ob.hide_render = False

    def play(self, anim, frame):
        if anim.name not in self.acts:
            self.acts[anim.name] = A.bake_action(self.arm, self.rig, anim, extra=getattr(self.res["module"], "secondary", None))
        A.assign_action(self.arm, self.acts[anim.name])
        bpy.context.scene.frame_set(int(frame))
        bpy.context.view_layer.update()

    def camera(self, view="34", yaw_add=0.0, target=None, dist=None, lens=None):
        yaw, pitch, d, ln, tz = CAMS[view]
        RR.place_camera(self.cam, target or (0, 0, tz), dist or d, yaw + yaw_add, pitch, lens=lens or ln)

    def render(self, path):
        RR.render(path)
        return path


def compose(paths, labels, out, cols=6, title=None, cell=None):
    """Compose frames into a labeled sheet with system-independent PIL (Blender ships numpy but not PIL), so
    this writes a small json job and runs compose_sheets.py with the system Python if available."""
    import json
    import subprocess
    job = dict(paths=paths, labels=labels, out=out, cols=cols, title=title or "", cell=cell)
    jp = out + ".job.json"
    with open(jp, "w") as f:
        json.dump(job, f)
    py = os.environ.get("BH_PYTHON", "python3")
    try:
        subprocess.run([py, os.path.join(HERE, "compose_sheets.py"), jp], check=True)
        os.remove(jp)
    except Exception as e:  # pragma: no cover
        print("[compose] failed:", e)


def pick_frames(anim, mode):
    m = anim.meta
    if mode == "hit":
        fr = []
        for (a, b) in m.get("hits", []):
            fr.append(int(round((a + b) / 2)))
        if "release" in m:
            fr.append(int(round(m["release"])))
        if not fr:
            fr = [int(round(m.get("key", anim.length / 2)))]
        return fr
    if mode.startswith("even:"):
        n = int(mode.split(":")[1])
        L = anim.length if not anim.loop else anim.length - 1
        return [int(round(L * i / max(n - 1, 1))) for i in range(n)]
    return [int(x) for x in mode.split(",")]


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []

    def opt(name, default=None):
        if name in argv:
            return argv[argv.index(name) + 1]
        return default
    import bh_library as L
    char = opt("--char", "knight")
    names = opt("--anims", "idle").split(",")
    mode = opt("--frames", "hit")
    res = int(opt("--res", "384"))
    out = opt("--out", os.path.join(os.environ.get("TEMP", "."), "bh_preview"))
    views = opt("--cam", "34").split(",")
    sheet = opt("--name", "sheet")
    cols = int(opt("--cols", "6"))
    os.makedirs(out, exist_ok=True)
    lib = {a.name: a for a in L.library(partial=True)}
    st = Stage(char, res=res, samples=8)
    paths, labels = [], []
    for n in names:
        an = lib[n]
        r, l = an.meta.get("props", (None, None))
        st.set_props(r, l)
        for f in pick_frames(an, mode):
            st.play(an, f)
            for view in views:
                st.camera(view)
                p = st.render(os.path.join(out, f"{n}_{f:03d}_{view}.png"))
                paths.append(p)
                labels.append(f"{n} f{f} ({f / 30:.2f}s) {view}")
    compose(paths, labels, os.path.join(out, sheet + ".png"), cols=cols)


if __name__ == "__main__":
    main()
