"""bh-029: Aljay's Broken Link, the quest item Terax hands over in Agdao, exported with Blender's bundled Python.

    blender -b --factory-startup --python tools/blender/characters/zarael_quest_items.py
"""
from pathlib import Path
from math import pi, cos, sin
import bmesh
import bpy

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'game/assets/items'
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)


def material(name, color, metallic, rough=.5):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    node = mat.node_tree.nodes.get('Principled BSDF')
    node.inputs['Base Color'].default_value = (*color, 1)
    node.inputs['Metallic'].default_value = metallic
    node.inputs['Roughness'].default_value = rough
    return mat


iron = material('Forsaken link iron', (.07, .065, .075), .85, .42)
bright = material('Snapped edge', (.55, .52, .5), .9, .3)


def link(name, gap_from, gap_to, rx=.11, ry=.065, r=.026, seg=40, ring=10):
    """An oval chain link swept round its long axis, with the arc between gap_from and gap_to (radians) left out."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    rows = []
    span = 2 * pi - (gap_to - gap_from)
    for i in range(seg + 1):
        a = gap_to + span * i / seg
        cx, cy = rx * cos(a), ry * sin(a)
        tx, ty = -rx * sin(a), ry * cos(a)
        tl = (tx * tx + ty * ty) ** .5
        nx, ny = ty / tl, -tx / tl
        row = []
        for j in range(ring):
            b = 2 * pi * j / ring
            row.append(bm.verts.new((cx + nx * r * cos(b), cy + ny * r * cos(b), r * sin(b) * 1.15)))
        rows.append(row)
    for i in range(seg):
        for j in range(ring):
            bm.faces.new((rows[i][j], rows[i][(j + 1) % ring], rows[i + 1][(j + 1) % ring], rows[i + 1][j]))
    # bright snapped faces at both broken ends
    for row, flip in ((rows[0], True), (rows[-1], False)):
        f = bm.faces.new(row[::-1] if flip else row)
        f.material_index = 1
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    me.materials.append(iron)
    me.materials.append(bright)
    for p in me.polygons:
        p.use_smooth = p.material_index == 0
    return ob


# the snapped link, lying flat, and the half-link still hooked through it
a = link('broken_link', -.28, .28)
b = link('hooked_half', pi * .55, pi * 1.45, rx=.1, ry=.06, r=.024)
b.location = (-.17, 0, .0)
b.rotation_euler = (pi / 2, 0, 0)
a.rotation_euler = (0, 0, .2)
bpy.ops.export_scene.gltf(filepath=str(OUT / 'quest_broken_link.glb'), export_format='GLB')
