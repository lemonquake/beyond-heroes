"""bh-033: convert a Quaternius glTF creature into a game-ready GLB (Blender 5.x, run headless).
  blender -b -P convert_creature.py -- <spec.json>
spec: {"src": gltf path, "out": glb path, "height": target height (m), "clips": {"game_clip": "SourceAction", ...},
       "tint": [r, g, b] multiply on the base colour, "value": 0.0-1.0 extra darkening, "rough": 0.85}
The source file is never written. Every game clip is its own action (copied when two game clips share a source), so
the game's clip names resolve directly in the model's AnimationPlayer."""
import bpy, json, sys, mathutils

spec = json.load(open(sys.argv[sys.argv.index("--") + 1]))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=spec["src"])

arm = next((o for o in bpy.context.scene.objects if o.type == "ARMATURE"), None)
meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
src_actions = {a.name: a for a in bpy.data.actions}
print("SOURCE ACTIONS", sorted(src_actions))

# ---- clips: one action per game clip name ---------------------------------------------------------------------------
made = []
for game, source in spec["clips"].items():
    a = src_actions.get(source)
    if a is None:
        # glTF importer may suffix actions with the armature name
        a = next((x for n, x in src_actions.items() if n.split("_")[0] == source or n.startswith(source)), None)
    if a is None:
        print("MISSING", source, "for", game)
        continue
    c = a.copy()
    c.name = game
    c.use_fake_user = True
    made.append(c)
for a in list(src_actions.values()):
    bpy.data.actions.remove(a)
if arm:
    arm.animation_data_create()
    # NLA: one muted track per clip so the exporter writes them all as separate animations
    for c in made:
        tr = arm.animation_data.nla_tracks.new()
        tr.name = c.name
        st = tr.strips.new(c.name, int(c.frame_range[0]), c)
        tr.mute = True
    arm.animation_data.action = None

# ---- scale to the target height (rest pose bounds) ------------------------------------------------------------------
lo = mathutils.Vector((1e9, 1e9, 1e9)); hi = mathutils.Vector((-1e9, -1e9, -1e9))
for m in meshes:
    for v in m.bound_box:
        w = m.matrix_world @ mathutils.Vector(v)
        lo = mathutils.Vector(map(min, lo, w)); hi = mathutils.Vector(map(max, hi, w))
height = hi.z - lo.z
s = spec["height"] / height if height > 0 else 1.0
roots = [o for o in bpy.context.scene.objects if o.parent is None]
for r in roots:
    r.scale = r.scale * s
    r.location = r.location * s
print("HEIGHT", round(height, 3), "->", spec["height"], "scale", round(s, 4))

# ---- palette: darken and desaturate the toy colours toward the game's look ------------------------------------------
tint = spec.get("tint", [1, 1, 1])
for mat in bpy.data.materials:
    if not mat.use_nodes:
        continue
    bsdf = next((n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if bsdf is None:
        continue
    nt = mat.node_tree
    link = next((l for l in nt.links if l.to_socket == bsdf.inputs["Base Color"]), None)
    if link:
        hsv = nt.nodes.new("ShaderNodeHueSaturation")
        hsv.inputs["Saturation"].default_value = spec.get("saturation", 0.7)
        hsv.inputs["Value"].default_value = 1.0 - spec.get("value", 0.25)
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.blend_type = "MULTIPLY"
        mix.inputs["Factor"].default_value = 1.0
        mix.inputs[7].default_value = (tint[0], tint[1], tint[2], 1.0)
        nt.links.new(link.from_socket, hsv.inputs["Color"])
        nt.links.new(hsv.outputs["Color"], mix.inputs[6])
        nt.links.new(mix.outputs[2], bsdf.inputs["Base Color"])
    else:
        c = bsdf.inputs["Base Color"].default_value
        bsdf.inputs["Base Color"].default_value = (c[0] * tint[0], c[1] * tint[1], c[2] * tint[2], 1.0)
    bsdf.inputs["Roughness"].default_value = spec.get("rough", 0.85)

# Mix/HSV nodes are not glTF-exportable: bake them into a new atlas image so the GLB carries the adapted colours.
img_src = next((i for i in bpy.data.images if i.size[0] > 0), None)
if img_src is not None:
    import colorsys
    px = list(img_src.pixels)
    out = bpy.data.images.new(img_src.name + "_bh", img_src.size[0], img_src.size[1], alpha=True)
    sat = spec.get("saturation", 0.7); val = 1.0 - spec.get("value", 0.25)
    res = [0.0] * len(px)
    for i in range(0, len(px), 4):
        h, l_s, v = colorsys.rgb_to_hsv(px[i], px[i + 1], px[i + 2])
        r, g, b = colorsys.hsv_to_rgb(h, l_s * sat, v * val)
        res[i] = r * tint[0]; res[i + 1] = g * tint[1]; res[i + 2] = b * tint[2]; res[i + 3] = px[i + 3]
    out.pixels = res
    out.file_format = "PNG"
    for mat in bpy.data.materials:
        if not mat.use_nodes:
            continue
        nt = mat.node_tree
        for n in list(nt.nodes):
            if n.type in ("HUE_SAT", "MIX"):
                nt.nodes.remove(n)
        bsdf = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
        tex = next((n for n in nt.nodes if n.type == "TEX_IMAGE"), None)
        if tex and bsdf:
            tex.image = out
            nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])

bpy.ops.export_scene.gltf(filepath=spec["out"], export_format="GLB", export_animations=True, export_animation_mode="NLA_TRACKS",
    export_force_sampling=True, export_apply=False, export_image_format="AUTO")
print("EXPORTED", spec["out"], "clips", [c.name for c in made])
