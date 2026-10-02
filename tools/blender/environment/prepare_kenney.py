"""Map-design pass (2026-10-03): prepare the accepted Kenney CC0 sources as game kit pieces.

  blender -b --factory-startup -P tools/blender/environment/prepare_kenney.py -- [ids...]

Reads the immutable canonical packages listed in assets_src/map_design_20261003/manifest.json and writes, for every
accepted model, one runtime GLB game/assets/environment/kd_<name>.glb that follows the kit contract:

* ONE mesh with identity transform: every source part (multi-mesh models included) is joined with its node transform
  applied, so MapBuilder.library_mesh() batches the whole object, not just its first piece.
* Game metres, Y up, front +Z, origin at the bottom (trees keep their trunk base; other pieces are centred).
* Part materials renamed to the shared BH_* contract, so MaterialLibrary replaces them with the game's lit, textured
  materials (no KHR_materials_unlit, no plastic shine, no per-placement copies). Flat-colour models map by source
  material name; palette-textured models ("colormap") are split per face by the palette colour under the face's UV
  centre, so a barrel keeps its staves and hoops as separate parts instead of one blanket material.
* Animations, armatures and skins are dropped (a decorative chest is not a loot chest).
* Optional simple collision: a box "<name>-colonly" child for furniture/large rocks, a trunk box for trees.

Each run writes work/map-design/prepared/<name>.json receipts (source/derived SHA-256, scale, part->material table,
triangles, surfaces, bounds) and work/map-design/prepared/index.json. Sources are never written.
"""
import bpy, bmesh, json, sys, hashlib, colorsys
from pathlib import Path
from mathutils import Vector, Matrix

ROOT = Path(__file__).resolve().parents[3]
LIB = ROOT / "assets_src/map_design_20261003"
OUT = ROOT / "game/assets/environment"
REC = ROOT / "work/map-design/prepared"

# ---- flat-colour source material name -> game material (nature and furniture kits) --------------------------------
FLAT = {
    "leafsGreen": "BH_Foliage", "leafsDark": "BH_FoliageDark", "leafsFall": "BH_Produce", "plant": "BH_Foliage",
    "woodBark": "BH_Bark", "woodBarkDark": "BH_Bark", "woodInner": "BH_Wood", "wood": "BH_Wood", "woodDark": "BH_WoodDark",
    "grass": "BH_Foliage", "dirt": "BH_Rock", "stone": "BH_Stone", "_defaultMat": "BH_Bark",
    "colorTan": "BH_MushroomPale", "colorRed": "BH_FlowerWhite", "colorRedDark": "BH_Cloth", "colorYellow": "BH_FlowerYellow",
    "colorPurple": "BH_FlowerViolet", "carpet": "BH_ClothRed", "carpetDarker": "BH_ClothOchre", "carpetWhite": "BH_ClothCream",
    "metal": "BH_Iron",
}

# ---- palette (colormap) roles by colour, then role -> material per kit -----------------------------------------------
def role(rgb):
    r, g, b = rgb
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    if v < 0.34:
        return "dark"
    if g > r + 0.15 and g > b:
        return "teal"
    if (s < 0.3 and b >= g >= r - 0.02) or (b > r and b >= g and s < 0.45):
        return "grey_dark" if v < 0.56 else "grey"
    if s < 0.12:
        return "white"
    if h < 0.13 and s >= 0.3:
        if s < 0.5 and v > 0.83:
            return "cream"
        return "wood" if v >= 0.7 else "wood_dark"
    return "grey"

KIT_ROLES = {
    "pirate-kit": {"wood": "BH_Wood", "wood_dark": "BH_WoodDark", "cream": "BH_Rope", "grey": "BH_Iron", "grey_dark": "BH_Iron",
                   "teal": "BH_Bottle", "dark": "BH_Iron", "white": "BH_ClothCream"},
    "graveyard-kit": {"wood": "BH_Wood", "wood_dark": "BH_WoodDark", "cream": "BH_Candle", "grey": "BH_Stone",
                      "grey_dark": "BH_StoneDark", "teal": "BH_Iron", "dark": "BH_Iron", "white": "BH_Stone"},
    "modular-dungeon-kit": {"wood": "BH_Stone", "wood_dark": "BH_Stone", "cream": "BH_Stone", "grey": "BH_Stone",
                            "grey_dark": "BH_Iron", "teal": "BH_Iron", "dark": "BH_Iron", "white": "BH_Stone"},
}

# ---- the accepted set ----------------------------------------------------------------------------------------------
# source id (without "kenney_") -> runtime name, scale rule ("h": height m | "s": uniform), collision, material overrides
# collision: "" none | "box" whole bounds | "trunk" a trunk-sized box | "low" box up to 0.9 m (low walls of a pile)
S = {}
def a(src, name, rule, col="", mats=None, keep_xz=False):
    S[src] = {"name": name, "rule": rule, "col": col, "mats": mats or {}, "keep_xz": keep_xz}

TREE = {"keep_xz": True}
a("nature_tree_oak", "kd_tree_oak", ("h", 6.5), "trunk", **TREE)
a("nature_tree_default", "kd_tree_broadleaf", ("h", 6.0), "trunk", **TREE)
a("nature_tree_detailed", "kd_tree_detailed", ("h", 6.8), "trunk", **TREE)
a("nature_tree_thin", "kd_tree_thin", ("h", 6.4), "trunk", **TREE)
a("nature_tree_small", "kd_tree_small", ("h", 3.6), "trunk", **TREE)
a("nature_tree_pinedefaulta", "kd_pine", ("h", 8.5), "trunk", **TREE)
a("nature_tree_pinerounda", "kd_pine_round", ("h", 7.2), "trunk", **TREE)
a("nature_tree_pinetalla", "kd_pine_tall", ("h", 11.0), "trunk", **TREE)
a("nature_tree_palm", "kd_palm", ("h", 7.5), "trunk", {"leafsGreen": "BH_JungleLeaf"}, keep_xz=True)
a("nature_tree_palmbend", "kd_palm_bend", ("h", 7.0), "trunk", {"leafsGreen": "BH_JungleLeaf"}, keep_xz=True)
a("nature_tree_palmshort", "kd_palm_short", ("h", 3.4), "", {"leafsGreen": "BH_JungleLeaf"}, keep_xz=True)
a("nature_tree_palmdetailedtall", "kd_palm_tall", ("h", 9.5), "trunk", {"leafsGreen": "BH_JungleLeaf"}, keep_xz=True)
a("nature_plant_bush", "kd_bush", ("h", 0.9))
a("nature_plant_bushlarge", "kd_bush_large", ("h", 1.2))
a("nature_plant_flattall", "kd_plant_leafy", ("h", 0.8), mats={"leafsGreen": "BH_JungleLeaf"})
a("nature_grass", "kd_grass", ("h", 0.35))
a("nature_grass_large", "kd_grass_large", ("h", 0.45))
a("nature_grass_leafs", "kd_ground_leaves", ("h", 0.3), mats={"grass": "BH_JungleLeaf"})
a("nature_flower_yellowa", "kd_flower_yellow", ("h", 0.45))
a("nature_flower_purplea", "kd_flower_purple", ("h", 0.5))
a("nature_mushroom_tangroup", "kd_mushrooms_pale", ("h", 0.35), mats={"_defaultMat": "BH_Fungus"})
a("nature_lily_large", "kd_lily", ("s", 3.0), mats={"leafsDark": "BH_FoliageDark"})
a("nature_hanging_moss", "kd_hanging_moss", ("h", 1.4), mats={"grass": "BH_Moss"})
a("nature_rock_largea", "kd_rock_a", ("s", 3.0), "box", {"grass": "BH_Moss"})
a("nature_rock_largeb", "kd_rock_b", ("s", 3.0), "box", {"grass": "BH_Moss", "_defaultMat": "BH_Rock"})
a("nature_rock_largec", "kd_rock_c", ("s", 3.0), "box", {"grass": "BH_Moss"})
a("nature_rock_smalla", "kd_rock_small_a", ("s", 2.0), "", {"grass": "BH_Moss"})
a("nature_rock_smallb", "kd_rock_small_b", ("s", 2.0), "", {"grass": "BH_Moss"})
a("nature_rock_smallflata", "kd_rock_flat", ("s", 2.4), "", {"grass": "BH_Moss"})
a("nature_rock_talla", "kd_rock_tall", ("h", 2.8), "box", {"grass": "BH_Moss", "_defaultMat": "BH_Rock"})
a("nature_stump_old", "kd_stump_old", ("h", 0.6), "box")
a("nature_stump_rounddetailed", "kd_stump_cut", ("h", 0.45), "box")
a("nature_log", "kd_log", ("s", 3.6), "box")
a("nature_log_stack", "kd_log_stack", ("s", 2.6), "box")
a("nature_fence_planks", "kd_fence", ("s", 2.6), "box", {"wood": "BH_WoodDark"})
a("nature_fence_gate", "kd_fence_gate", ("s", 2.6), "", {"wood": "BH_WoodDark", "woodDark": "BH_WoodDark", "stone": "BH_Stone"})
a("nature_pot_small", "kd_pot_small", ("h", 0.55), "", {"wood": "BH_Terracotta", "woodBarkDark": "BH_Terracotta", "_defaultMat": "BH_Dirt"})
a("nature_pot_large", "kd_planter", ("s", 2.2), "box", {"wood": "BH_Terracotta", "woodBarkDark": "BH_Dirt"})
a("nature_crop_carrot", "kd_carrots", ("h", 0.45))
a("nature_crop_pumpkin", "kd_pumpkin", ("h", 0.45))
a("nature_crops_wheatstageb", "kd_wheat", ("h", 1.0), "", {"woodInner": "BH_Thatch", "_defaultMat": "BH_Thatch"})
a("nature_crops_bamboostageb", "kd_bamboo", ("h", 3.2), "", {"grass": "BH_Foliage"})
a("nature_tent_smallopen", "kd_tent", ("h", 2.2), "box", {"colorRed": "BH_ClothCream", "colorRedDark": "BH_Cloth"})
a("nature_campfire_stones", "kd_fire_ring", ("s", 2.2))
a("nature_canoe", "kd_canoe", ("s", 3.0), "", {"leafsFall": "BH_WoodDark"})
FURN = 2.25
a("furniture_bench", "kd_bench", ("s", 2.1), "box")
a("furniture_chair", "kd_chair", ("s", FURN), "box")
a("furniture_chairrounded", "kd_chair_round", ("s", FURN), "box")
a("furniture_stoolbarsquare", "kd_stool_square", ("s", 2.0), "", {"carpet": "BH_Leather"})
a("furniture_table", "kd_table", ("s", FURN), "box")
a("furniture_tableround", "kd_table_round", ("s", FURN), "box")
a("furniture_tablecross", "kd_table_cross", ("s", FURN), "box")
a("furniture_tablecloth", "kd_table_cloth", ("s", FURN), "box", {"carpet": "BH_ClothCream"})
a("furniture_sidetable", "kd_side_table", ("s", FURN), "box", {"_defaultMat": "BH_WoodDark"})
a("furniture_sidetabledrawers", "kd_drawers", ("s", FURN), "box", {"_defaultMat": "BH_WoodDark"})
a("furniture_desk", "kd_desk", ("s", FURN), "box")
a("furniture_bookcaseopen", "kd_bookcase_open", ("s", FURN), "box")
a("furniture_bookcaseopenlow", "kd_bookcase_low", ("s", FURN), "box")
a("furniture_bookcaseclosed", "kd_bookcase_closed", ("s", FURN), "box", {"wood": "BH_WoodDark"})
a("furniture_bookcaseclosedwide", "kd_bookcase_wide", ("s", FURN), "box", {"wood": "BH_WoodDark"})
a("furniture_books", "kd_books", ("s", FURN), "", {"carpetDarker": "BH_Leather", "carpetWhite": "BH_Paper", "plant": "BH_ClothGreen", "metal": "BH_Brass"})
a("furniture_bedsingle", "kd_bed_single", ("s", 1.9), "box")
a("furniture_bedbunk", "kd_bed_bunk", ("s", 1.9), "box", {"carpet": "BH_Cloth"})
a("furniture_rugrectangle", "kd_rug_long", ("s", 2.0), "", {"carpet": "BH_ClothRed", "carpetDarker": "BH_ClothOchre"})
a("furniture_coatrackstanding", "kd_coat_rack", ("s", FURN), "box", {"wood": "BH_WoodDark"})
a("furniture_plantsmall1", "kd_plant_pot_a", ("s", 2.4), "", {"wood": "BH_Terracotta"})
a("furniture_plantsmall2", "kd_plant_pot_b", ("s", 2.4), "", {"wood": "BH_Terracotta"})
a("furniture_pottedplant", "kd_plant_tall", ("s", FURN), "", {"wood": "BH_Terracotta", "woodDark": "BH_Dirt"})
a("pirate_barrel", "kd_barrel", ("h", 0.95), "box")
a("pirate_crate", "kd_crate", ("s", 0.9), "box")
a("pirate_crate_bottles", "kd_crate_bottles", ("s", 0.9), "box", {"cream": "BH_Thatch"})
a("pirate_bottle", "kd_bottle", ("h", 0.3))
a("pirate_bottle_large", "kd_bottle_large", ("h", 0.45), "", {"wood": "BH_Terracotta", "wood_dark": "BH_Terracotta", "cream": "BH_Rope"})
a("pirate_chest", "kd_chest", ("h", 0.7), "box", {"grey": "BH_Iron", "grey_dark": "BH_Iron"})
a("pirate_tool_shovel", "kd_shovel", ("h", 1.3))
a("pirate_tool_paddle", "kd_paddle", ("h", 1.6))
a("pirate_boat_row_small", "kd_rowboat", ("s", 1.3))
a("pirate_ship_wreck", "kd_wreck", ("s", 1.15), "", {"teal": "BH_Kelp"})
a("pirate_rocks_a", "kd_shore_rocks_a", ("s", 1.2), "box", {"grey": "BH_Rock", "grey_dark": "BH_Rock"})
a("pirate_rocks_b", "kd_shore_rocks_b", ("s", 1.2), "box", {"grey": "BH_Rock", "grey_dark": "BH_Rock"})
a("pirate_rocks_c", "kd_shore_rocks_c", ("s", 1.2), "box", {"grey": "BH_Rock", "grey_dark": "BH_Rock"})
a("pirate_platform_planks", "kd_planks", ("s", 1.0))
a("pirate_structure_platform_dock_small", "kd_dock_small", ("s", 1.0), "", {"wood": "BH_WoodDark"})
a("pirate_structure_roof", "kd_canopy", ("s", 1.0), "", {"cream": "BH_ClothCream"})
G = 2.2
a("graveyard_altar_stone", "kd_altar_stone", ("s", 2.0), "box")
a("graveyard_altar_wood", "kd_altar_wood", ("s", 2.0), "box", {"grey": "BH_Iron", "grey_dark": "BH_Iron"})
a("graveyard_coffin_old", "kd_coffin_old", ("s", 2.3), "box", {"wood": "BH_WoodDark"})
a("graveyard_coffin", "kd_coffin", ("s", 2.3), "box", {"wood": "BH_WoodDark"})
a("graveyard_candle_multiple", "kd_candles", ("s", 1.6))
a("graveyard_lantern_candle", "kd_lantern_candle", ("s", 1.6), "", {"grey": "BH_Iron", "grey_dark": "BH_Iron"})
a("graveyard_fire_basket", "kd_fire_basket", ("s", 2.4), "box")
a("graveyard_urn_round", "kd_urn_round", ("s", 2.0), "box", {"grey": "BH_Terracotta", "grey_dark": "BH_StoneDark"})
a("graveyard_urn_square", "kd_urn_square", ("s", 2.0), "box")
a("graveyard_detail_chalice", "kd_chalice", ("s", 1.0), "", {"wood": "BH_Brass", "wood_dark": "BH_Brass", "cream": "BH_Brass"})
a("graveyard_detail_bowl", "kd_offering_bowl", ("s", 1.4), "", {"wood": "BH_Brass", "wood_dark": "BH_Brass", "cream": "BH_Brass"})
a("graveyard_debris", "kd_debris_stone", ("s", 2.0))
a("graveyard_debris_wood", "kd_debris_wood", ("s", 2.2), "", {"wood": "BH_WoodDark"})
a("graveyard_gravestone_broken", "kd_grave_broken", ("s", 2.0), "box")
a("graveyard_column_large", "kd_column", ("s", 2.6), "box", {"wood": "BH_Stone", "wood_dark": "BH_StoneDark"})
a("graveyard_pillar_obelisk", "kd_obelisk", ("s", 2.6), "box")
a("modular-dungeon_gate_metal_bars", "kd_bars_gate", ("s", 0.9), "box")
a("modular-dungeon_template_floor_layer_raised", "kd_dais", ("s", 0.75), "box")
a("modular-dungeon_template_floor_detail_a", "kd_floor_inlay", ("s", 0.75))

# Considered and NOT prepared (decision and reason; ASSET_CREDITS_MAP_DESIGN.md mirrors this list)
DEFERRED = {
    "nature_stone_largea": "rejected: recolour of rock_largeA (same geometry); not a distinct source model",
    "nature_stone_smallflata": "rejected: recolour of rock_smallFlatA (same geometry)",
    "furniture_beddouble": "deferred: the existing bed_double already fits every room that needs one",
    "furniture_pillow": "deferred: the prepared beds include pillows; a loose modern pillow adds nothing",
    "furniture_ruground": "deferred: the existing rug_round fills this role",
    "pirate_boat_row_large": "deferred: kd_rowboat and the existing boat_rowing cover every mooring",
    "pirate_structure_fence": "deferred: repeated railing spans are what the brief warns against on long bridges",
    "pirate_flag_pennant": "rejected: flags and pennants were rejected by the user (medieval, in-theme art only)",
    "pirate_mast_ropes": "deferred: no harbour scene needs a free-standing rigged mast; the wreck carries one",
    "nature_plant_bushsmall": "rejected after in-game review: its 8 triangles read as a flat dark star from the gameplay "
                              "camera; the kit's own bushes take its places",
    "modular-dungeon_template_wall_half": "deferred: the existing 4 m wall kit and low cutaway walls already do this",
}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def get_mat(name):
    m = bpy.data.materials.get(name)
    if m is None:
        m = bpy.data.materials.new(name)
    return m


def palette_image(mat):
    if mat and mat.use_nodes:
        for n in mat.node_tree.nodes:
            if n.type == "TEX_IMAGE" and n.image:
                return n.image
    return None


def prepare(entry, spec):
    clear()
    src = LIB / entry["model"]
    bpy.ops.import_scene.gltf(filepath=str(src))
    kit = entry["kit"]
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    bm = bmesh.new()
    parts = {}           # BH material -> face count
    srcmap = {}          # source key -> BH material
    order = []
    for o in meshes:
        me = o.data
        uv = me.uv_layers.active
        tmp = bmesh.new()
        tmp.from_mesh(me)
        tmp.transform(o.matrix_world)          # applies every parent/child transform (multi-mesh models)
        uvl = tmp.loops.layers.uv.active
        imgs = [palette_image(m) for m in me.materials]
        mats_here = []
        for f in tmp.faces:
            m = me.materials[f.material_index] if me.materials else None
            mname = m.name.split(".")[0] if m else "_defaultMat"
            img = imgs[f.material_index] if me.materials else None
            if img is not None and uvl is not None:
                u = sum((l[uvl].uv for l in f.loops), Vector((0, 0))) / len(f.loops)
                w, h = img.size
                x = min(w - 1, max(0, int((u.x % 1.0) * w)))
                y = min(h - 1, max(0, int((u.y % 1.0) * h)))
                i = (y * w + x) * 4
                key = role(tuple(img.pixels[i:i + 3]))
                bh = spec["mats"].get(key, KIT_ROLES[kit][key])
            else:
                key = mname
                bh = spec["mats"].get(key, FLAT.get(key, "BH_Wood"))
            srcmap[key] = bh
            if bh not in order:
                order.append(bh)
            f.material_index = order.index(bh)
            parts[bh] = parts.get(bh, 0) + 1
        # merge into the single output mesh (material indices already refer to `order`)
        tmp_me = bpy.data.meshes.new("tmp")
        tmp.to_mesh(tmp_me)
        tmp.free()
        bm.from_mesh(tmp_me)
        bpy.data.meshes.remove(tmp_me)
    # scale to game metres and seat on the ground
    xs = [v.co.x for v in bm.verts]; ys = [v.co.y for v in bm.verts]; zs = [v.co.z for v in bm.verts]
    size = Vector((max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)))
    rule, val = spec["rule"]
    s = val / size.z if rule == "h" else val
    cx = 0.0 if spec["keep_xz"] else (min(xs) + max(xs)) / 2
    cy = 0.0 if spec["keep_xz"] else (min(ys) + max(ys)) / 2
    bmesh.ops.transform(bm, matrix=Matrix.Scale(s, 4) @ Matrix.Translation((-cx, -cy, -min(zs))), verts=bm.verts)
    # no vertex merge: the sources' split vertices carry their flat shading and double-sided leaves
    bm.normal_update()
    tris = sum(len(f.verts) - 2 for f in bm.faces)
    xs = [v.co.x for v in bm.verts]; ys = [v.co.y for v in bm.verts]; zs = [v.co.z for v in bm.verts]
    lo = Vector((min(xs), min(ys), min(zs))); hi = Vector((max(xs), max(ys), max(zs)))
    # drop everything the source brought (armatures, empties, animations)
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for ac in list(bpy.data.actions):
        bpy.data.actions.remove(ac)
    me = bpy.data.meshes.new(spec["name"])
    bm.to_mesh(me)
    bm.free()
    for m in order:
        me.materials.append(get_mat(m))
    ob = bpy.data.objects.new(spec["name"], me)
    bpy.context.scene.collection.objects.link(ob)
    col = spec["col"]
    if col:
        if col == "trunk":
            r = max(0.18, min(0.45, (hi.z - lo.z) * 0.045))
            clo, chi = Vector((-r, -r, 0)), Vector((r, r, min(2.6, hi.z)))
        else:
            clo, chi = lo.copy(), hi.copy()
        cb = bmesh.new()
        bmesh.ops.create_cube(cb, size=1.0)
        bmesh.ops.transform(cb, matrix=Matrix.Translation((clo + chi) / 2) @ Matrix.Diagonal((*(chi - clo), 1.0)), verts=cb.verts)
        cme = bpy.data.meshes.new(spec["name"] + "-colonly")
        cb.to_mesh(cme)
        cb.free()
        co = bpy.data.objects.new(spec["name"] + "-colonly", cme)
        bpy.context.scene.collection.objects.link(co)
        co.parent = ob
    out = OUT / (spec["name"] + ".glb")
    bpy.ops.object.select_all(action="SELECT")
    bpy.context.view_layer.objects.active = ob
    bpy.ops.export_scene.gltf(filepath=str(out), export_format="GLB", use_selection=True, export_yup=True, export_apply=True,
        export_materials="EXPORT", export_image_format="NONE", export_normals=True, export_texcoords=True,
        export_extras=False, export_cameras=False, export_lights=False, export_animations=False, export_skins=False,
        export_morph=False)
    # Blender Z-up -> glTF Y-up: x stays, Blender y -> -z, z -> y
    rec = {
        "source_id": entry["id"], "kit": kit, "runtime": "res://assets/environment/%s.glb" % spec["name"],
        "package": entry["package"], "source_sha256": entry["package_model_sha256"], "derived_sha256": sha(out),
        "scale": round(s, 4), "scale_rule": [rule, val], "origin": "trunk base" if spec["keep_xz"] else "bottom centre",
        "collision": col or "none", "materials": order, "part_faces": parts, "source_to_material": srcmap,
        "triangles": tris, "surfaces": len(order), "source_triangles": entry["triangles"], "source_meshes": entry["meshes"],
        "bounds_m": [round(hi.x - lo.x, 3), round(hi.z - lo.z, 3), round(hi.y - lo.y, 3)],
        "dropped": "animations, armatures, skins, palette texture (parts mapped to shared materials)",
    }
    (REC / (spec["name"] + ".json")).write_text(json.dumps(rec, indent=1))
    print("PREPARED", spec["name"], "tris", tris, "surfaces", len(order), "size", rec["bounds_m"], order)
    return rec


def main():
    want = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    REC.mkdir(parents=True, exist_ok=True)
    manifest = json.load(open(LIB / "manifest.json"))
    index = {"accepted": {}, "deferred": DEFERRED}
    for e in manifest["assets"]:
        sid = e["id"].replace("kenney_", "")
        if sid not in S:
            if sid not in DEFERRED:
                print("UNDECIDED", sid)
            continue
        spec = S[sid]
        if want and spec["name"] not in want and sid not in want:
            prev = REC / (spec["name"] + ".json")
            if prev.exists():
                index["accepted"][sid] = json.loads(prev.read_text())
            continue
        index["accepted"][sid] = prepare(e, spec)
    (REC / "index.json").write_text(json.dumps(index, indent=1))
    print("DONE accepted", len(index["accepted"]), "deferred", len(DEFERRED))


main()
