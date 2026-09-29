"""bh-021 look-dev renders for the legends: EEVEE, the real texture sets on the box-projected UVs, a dark studio.

  blender -b --factory-startup --python legend_preview.py -- <character|weapon:name> [--clip cs_aj_rise --frames 0,0.5,1]
          [--views 20,160,90] [--res 900] [--out <dir>] [--tag x] [--close] [--weapon dusk_piercer]

Writes <out>/<character>_<tag>_<view>[_<frame>].png (compose sheets with tools/blender/characters/legend_sheet.py).
"""
import argparse
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
TEX = os.path.join(ROOT, "game", "assets", "textures", "legend")

import bpy  # noqa: E402
from mathutils import Vector, Matrix  # noqa: E402

# material base name -> (texture set, metres per repeat)
LEGEND_TEX = {
    "BH_DragonPlate": ("dragon_scale", 0.3), "BH_HolyPlate": ("engraved_plate", 0.5),
    "BH_Crimson": ("engraved_plate", 0.3), "BH_Gold": ("engraved_plate", 0.3), "BH_DarkSteel": ("engraved_plate", 0.55),
    "BH_ForsakenIron": ("forsaken_iron", 0.6), "BH_Mail": ("chainmail", 0.22), "BH_Leather": ("leather_worn", 0.45),
    "BH_Cloth_Primary": ("storm_wool", 0.3), "BH_Cloth_Secondary": ("storm_wool", 0.3), "BH_Wool": ("storm_wool", 0.3),
    "BH_Horn": ("tyrant_bone", 0.3), "BH_Fang": ("tyrant_bone", 0.2), "BH_Bone": ("tyrant_bone", 0.3),
    "BH_Steel": ("engraved_plate", 0.5), "BH_Silver": ("engraved_plate", 0.4),
}


def args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("character")
    ap.add_argument("--clip", default="")
    ap.add_argument("--frames", default="0")
    ap.add_argument("--views", default="25,160,90,-35")
    ap.add_argument("--res", type=int, default=900)
    ap.add_argument("--out", default=os.path.join(ROOT, "work", "lemondev", "bh-021", "scratch", "preview"))
    ap.add_argument("--tag", default="rest")
    ap.add_argument("--close", action="store_true", help="head-and-shoulders framing")
    ap.add_argument("--face", action="store_true", help="portrait framing of the head")
    ap.add_argument("--weapon", default="", help="legend weapon to put in the right hand")
    ap.add_argument("--weapon_l", default="")
    ap.add_argument("--samples", type=int, default=32)
    return ap.parse_args(argv)


def texture_materials():
    imgs = {}

    def img(name, cs):
        key = (name, cs)
        if key not in imgs:
            im = bpy.data.images.load(os.path.join(TEX, name + ".png"))
            im.colorspace_settings.name = cs
            imgs[key] = im
        return imgs[key]
    for m in bpy.data.materials:
        base = m.name.split("__")[0].split(".")[0]
        if base not in LEGEND_TEX or not m.use_nodes:
            continue
        tset, tile = LEGEND_TEX[base]
        nt = m.node_tree
        bsdf = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if bsdf is None:
            continue
        col = tuple(bsdf.inputs["Base Color"].default_value)
        uv = nt.nodes.new("ShaderNodeTexCoord")
        mp = nt.nodes.new("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = (1.0 / tile, 1.0 / tile, 1.0)
        nt.links.new(uv.outputs["UV"], mp.inputs["Vector"])
        ta = nt.nodes.new("ShaderNodeTexImage")
        ta.image = img(tset + "_albedo", "sRGB")
        nt.links.new(mp.outputs["Vector"], ta.inputs["Vector"])
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.blend_type = "MULTIPLY"
        mix.inputs["Factor"].default_value = 1.0
        mix.inputs[6].default_value = col
        nt.links.new(ta.outputs["Color"], mix.inputs[7])
        # keep the baked vertex AO too
        vc = nt.nodes.new("ShaderNodeVertexColor")
        vc.layer_name = "Col"
        mix2 = nt.nodes.new("ShaderNodeMix")
        mix2.data_type = "RGBA"
        mix2.blend_type = "MULTIPLY"
        mix2.inputs["Factor"].default_value = 1.0
        nt.links.new(mix.outputs[2], mix2.inputs[6])
        nt.links.new(vc.outputs["Color"], mix2.inputs[7])
        nt.links.new(mix2.outputs[2], bsdf.inputs["Base Color"])
        tn = nt.nodes.new("ShaderNodeTexImage")
        tn.image = img(tset + "_normal", "Non-Color")
        nt.links.new(mp.outputs["Vector"], tn.inputs["Vector"])
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nm.inputs["Strength"].default_value = 1.0
        nt.links.new(tn.outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
        tr = nt.nodes.new("ShaderNodeTexImage")
        tr.image = img(tset + "_rough", "Non-Color")
        nt.links.new(mp.outputs["Vector"], tr.inputs["Vector"])
        rm = nt.nodes.new("ShaderNodeMath")
        rm.operation = "MULTIPLY"
        rm.inputs[1].default_value = bsdf.inputs["Roughness"].default_value / 0.45
        nt.links.new(tr.outputs["Color"], rm.inputs[0])
        nt.links.new(rm.outputs[0], bsdf.inputs["Roughness"])


def studio(res, samples):
    import bh_render as R
    cam = R.setup_scene(res, samples, bg=(0.02, 0.018, 0.024))
    sc = bpy.context.scene
    sc.render.resolution_x = res
    sc.render.resolution_y = int(res * 1.25)
    sc.view_settings.exposure = -1.8
    # a crimson under-glow and a cold rim for drama
    for name, loc, energy, color, size in (("Under", (0.0, -1.6, 0.2), 35, (1.0, 0.3, 0.2), 1.0),
                                          ("Top", (0.0, 0.5, 4.5), 500, (0.85, 0.85, 1.0), 2.5)):
        ld = bpy.data.lights.new(name, "AREA")
        ld.energy = energy
        ld.color = color
        ld.size = size
        lo = bpy.data.objects.new(name, ld)
        sc.collection.objects.link(lo)
        lo.location = loc
        R.look_at(lo, Vector((0, 0, 1.0)))
    g = bpy.data.objects.get("Ground")
    if g and g.data.materials:
        b = g.data.materials[0].node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = (0.012, 0.012, 0.014, 1)
    return cam


def attach_weapon(arm, name, bone):
    import legend_weapons as LW
    import bh_materials as MT
    ob = LW.build(name)
    pb = arm.pose.bones[bone]
    ob.parent = arm
    ob.parent_type = "BONE"
    ob.parent_bone = bone
    # bone-parented objects sit at the bone TAIL; weapon GLBs are authored with the grip at the origin, +Z blade,
    # socket +Y = blade: rotate +Z onto the bone's +Y and move back to the head
    L = (pb.bone.tail_local - pb.bone.head_local).length
    ob.matrix_parent_inverse = Matrix.Identity(4)
    ob.matrix_basis = Matrix.Translation((0, -L, 0)) @ Matrix.Rotation(-math.pi / 2, 4, "X")
    return ob


def main():
    a = args()
    os.makedirs(a.out, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    import build_chars as BC
    clips = [c for c in a.clip.split(",") if c]
    res = BC.build_character(a.character, with_actions=bool(clips), only=set(clips) if clips else None)
    arm = res["armature"]
    if a.weapon:
        attach_weapon(arm, a.weapon, "weapon.R")
    if a.weapon_l:
        attach_weapon(arm, a.weapon_l, "weapon.L")
    texture_materials()
    cam = studio(a.res, a.samples)
    import bh_render as R
    h = getattr(res["module"], "PREVIEW_HEIGHT", 1.95)
    views = [float(v) for v in a.views.split(",")]
    frames = [float(f) for f in a.frames.split(",")]
    todo = [(None, 0)]
    if clips:
        todo = [(c, fr) for c in clips for fr in frames]
    for clip, fr in todo:
        if clip:
            act = res["actions"].get(clip)
            if act is None:
                print("missing clip", clip)
                continue
            ad = arm.animation_data or arm.animation_data_create()
            ad.action = act
            try:
                if ad.action_slot is None and len(act.slots):
                    ad.action_slot = act.slots[0]
            except Exception:
                pass
            f = int(round(fr * act.frame_range[1]))
            bpy.context.scene.frame_set(f)
        for v in views:
            if a.face:
                R.place_camera(cam, (0, 0, 1.69), 0.62, v, 3, lens=70)
            elif a.close:
                R.place_camera(cam, (0, 0, h * 0.8), 1.35, v, 6, lens=60)
            else:
                R.place_camera(cam, (0, 0, h * 0.5), h * 2.3, v, 8, lens=55)
            tag = f"{a.character}_{a.tag}_{int(v)}" + (f"_{clip}_{int(fr * 100)}" if clip else "")
            R.render(os.path.join(a.out, tag + ".png"))
            print("RENDERED", tag)


if __name__ == "__main__":
    main()
