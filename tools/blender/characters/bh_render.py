"""EEVEE preview rendering helpers (lighting rig + cameras)."""
import math
import bpy
from mathutils import Vector


def setup_scene(res=1024, samples=24, bg=(0.035, 0.035, 0.05)):
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE"
    sc.render.resolution_x = res
    sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = False
    sc.render.fps = 30
    try:
        sc.eevee.taa_render_samples = samples
    except Exception:
        pass
    sc.view_settings.view_transform = "AgX"
    try:
        sc.view_settings.look = "AgX - Medium High Contrast"
    except Exception:
        pass
    w = sc.world or bpy.data.worlds.new("World")
    sc.world = w
    w.use_nodes = True
    bgn = w.node_tree.nodes.get("Background")
    bgn.inputs[0].default_value = (*bg, 1)
    bgn.inputs[1].default_value = 1.0
    # lights: warm key, cool rim, soft fill
    for name, loc, energy, color, size in (
            ("Key", (-3.0, -4.0, 5.0), 900, (1.0, 0.82, 0.62), 2.0),
            ("Rim", (3.5, 3.5, 4.0), 1100, (0.45, 0.65, 1.0), 1.5),
            ("Fill", (4.0, -3.5, 1.5), 260, (0.7, 0.75, 0.9), 3.0)):
        ld = bpy.data.lights.new(name, "AREA")
        ld.energy = energy
        ld.color = color
        ld.size = size
        lo = bpy.data.objects.new(name, ld)
        sc.collection.objects.link(lo)
        lo.location = loc
        look_at(lo, Vector((0, 0, 1.0)))
    # ground disc
    me = bpy.data.meshes.new("Ground")
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_circle(bm, cap_ends=True, radius=3.0, segments=48)
    bm.to_mesh(me)
    bm.free()
    g = bpy.data.objects.new("Ground", me)
    sc.collection.objects.link(g)
    gm = bpy.data.materials.new("GroundMat")
    gm.use_nodes = True
    b = gm.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.05, 0.05, 0.06, 1)
    b.inputs["Roughness"].default_value = 0.9
    me.materials.append(gm)
    cam_d = bpy.data.cameras.new("Cam")
    cam = bpy.data.objects.new("Cam", cam_d)
    sc.collection.objects.link(cam)
    sc.camera = cam
    return cam


def look_at(ob, target):
    d = Vector(target) - ob.location
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def place_camera(cam, target, dist, yaw_deg, pitch_deg, lens=50.0, ortho=None):
    """yaw 0 = camera in front of the character (at -Y looking +Y); positive yaw orbits toward the
    character's left (+X). pitch = elevation angle above horizontal."""
    y = math.radians(yaw_deg)
    p = math.radians(pitch_deg)
    t = Vector(target)
    off = Vector((math.sin(y) * math.cos(p), -math.cos(y) * math.cos(p), math.sin(p))) * dist
    cam.location = t + off
    look_at(cam, t)
    if ortho:
        cam.data.type = "ORTHO"
        cam.data.ortho_scale = ortho
    else:
        cam.data.type = "PERSP"
        cam.data.lens = lens
    cam.data.clip_end = 200


def render(path):
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
