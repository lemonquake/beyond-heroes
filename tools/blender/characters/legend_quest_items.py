"""Export the story's two inventory models with Blender's bundled Python."""
from pathlib import Path
import shutil
import bpy
from math import pi

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'game/assets/items'
shutil.copyfile(ROOT / 'game/assets/weapons/legend/dusk_piercer_tip.glb', OUT / 'quest_lance_shard.glb')
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

def material(name, color, metallic):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    node = mat.node_tree.nodes.get('Principled BSDF')
    node.inputs['Base Color'].default_value = (*color, 1)
    node.inputs['Metallic'].default_value = metallic
    node.inputs['Roughness'].default_value = .46
    return mat

iron = material('Chain seal iron', (.12, .10, .14), .8)
silver = material('Worn seal engraving', (.43, .38, .46), .7)
bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=.18, depth=.055)
bpy.context.object.data.materials.append(iron)
for x in [-.07, 0, .07]:
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, 0, .035))
    bpy.context.object.scale = (.017, .22 if x == 0 else .13, .012)
    bpy.context.object.data.materials.append(silver)
for i in range(3):
    bpy.ops.mesh.primitive_torus_add(major_segments=16, minor_segments=6, major_radius=.055, minor_radius=.012,
                                  location=(0, .20 + i * .075, 0), rotation=(pi/2 if i % 2 else 0, 0, 0))
    bpy.context.object.scale.y = 1.4
    bpy.context.object.data.materials.append(iron)
bpy.ops.export_scene.gltf(filepath=str(OUT / 'quest_chain_seal.glb'), export_format='GLB')
