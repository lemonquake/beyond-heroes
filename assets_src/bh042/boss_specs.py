"""bh-042: the rigging specs of the downloaded bosses (rig_to_hero.py) and their in-game conversion specs
(game/tests/tools/convert_creature.tscn). python boss_specs.py writes specs/rig_<id>.json and specs/conv_<id>.json."""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")
OGA = HERE + "/oga"
OUT = HERE + "/out"


def lr(fn):
    out = {}
    for s, h in (("L", "L"), ("R", "R")):
        out.update(fn(s, h))
    return out


M = "mixamorig"
MIXAMO = {M + "Hips": "hips", M + "Spine": "spine", M + "Spine1": "chest", M + "Spine2": "chest", M + "Neck": "neck", M + "Head": "head"}
for s, h in (("Left", "L"), ("Right", "R")):
    MIXAMO.update({M + s + "Shoulder": "shoulder." + h, M + s + "Arm": "upper_arm." + h, M + s + "ForeArm": "forearm." + h,
                   M + s + "Hand": "hand." + h, M + s + "UpLeg": "thigh." + h, M + s + "Leg": "shin." + h,
                   M + s + "Foot": "foot." + h, M + s + "ToeBase": "toe." + h})

GOLEM = {"hips": "hips", "spine": "spine", "ribs": "chest", "spine1": "chest", "neck": "neck", "head": "head"}
for sd in ("L", "R"):
    GOLEM.update({"shoulder." + sd: "shoulder." + sd, "upper_arm." + sd: "upper_arm." + sd, "forearm." + sd: "forearm." + sd,
                  "hand." + sd: "hand." + sd, "IKhand." + sd: "hand." + sd, "elbow." + sd: "forearm." + sd,
                  "thigh." + sd: "thigh." + sd, "shin." + sd: "shin." + sd, "knee." + sd: "shin." + sd,
                  "heel." + sd: "foot." + sd, "foot." + sd: "foot." + sd, "IKheel." + sd: "foot." + sd, "toe." + sd: "toe." + sd})

GLUTTON = {"core": "hips", "core.001": "spine", "core.002": "chest", "head": "neck", "head.001": "head"}
for sd in ("L", "R"):
    GLUTTON.update({"Bone.002_%s" % sd: "shoulder." + sd, "Bone.002_%s.001" % sd: "upper_arm." + sd,
                    "Bone.002_%s.002" % sd: "forearm." + sd, "leg_%s.001" % sd: "thigh." + sd, "leg_%s.002" % sd: "shin." + sd})

HORROR = {"joint1": "hips", "joint2": "spine", "joint3": "chest", "joint4": "neck", "joint15": "head",
          "Clav_L": "shoulder.L", "joint14": "upper_arm.L", "joint11": "forearm.L", "joint12": "hand.L",
          "Clav_R": "shoulder.R", "joint14.001": "upper_arm.R", "joint11.001": "forearm.R", "joint12.001": "hand.R",
          "joint5": "thigh.L", "joint6": "shin.L", "joint7": "foot.L", "joint8": "toe.L",
          "joint64": "thigh.R", "joint6.001": "shin.R", "joint7.001": "foot.R", "joint8.001": "toe.R"}

# Darsh faces +Y in its file: it is turned round (yaw 180), so its -X limbs become the hero's left
DARSH = {"Bone": "hips", "Bone.001": "spine", "Bone.002": "chest", "Bone.003": "head",
         "Bone.004": "shoulder.L", "Bone.005": "upper_arm.L", "Bone.006": "forearm.L", "Bone.007": "hand.L",
         "Bone.008": "shoulder.R", "Bone.009": "upper_arm.R", "Bone.010": "forearm.R", "Bone.011": "hand.R",
         "Bone.013": "thigh.R", "Bone.014": "shin.R", "Bone.016": "thigh.L", "Bone.017": "shin.L"}

FOREST = {"Hips": "hips", "Spine1": "spine", "Spine2": "chest", "Spine3": "chest", "Neck": "neck", "Head": "head"}
for sd in ("L", "R"):
    FOREST.update({"Shoulder_" + sd: "shoulder." + sd, "Arm_" + sd: "upper_arm." + sd, "Forearm_" + sd: "forearm." + sd,
                   "Hand_" + sd: "hand." + sd, "Thigh_" + sd: "thigh." + sd, "Leg_" + sd: "shin." + sd, "Foot_" + sd: "foot." + sd,
                   "IK-Foot_" + sd: "foot." + sd})

# The faceless stalker stands in an A-pose with no rig: its joints read off measure.py's calibrated views
# (feet on z = 0, 1.8 m tall, facing -Y)
STALKER_LM = {"hips": [0.0, 0.04, 0.9], "spine": [0.0, 0.04, 1.02], "chest": [0.0, 0.02, 1.2], "neck": [0.0, 0.02, 1.47],
              "head": [0.0, 0.0, 1.58], "head:tip": [0.0, -0.02, 1.78],
              "thigh.L": [0.1, 0.04, 0.86], "shin.L": [0.13, -0.04, 0.5], "foot.L": [0.13, 0.06, 0.09], "toe.L": [0.13, -0.08, 0.02],
              "toe.L:tip": [0.13, -0.18, 0.01],
              "shoulder.L": [0.07, 0.02, 1.4], "upper_arm.L": [0.25, 0.04, 1.36], "forearm.L": [0.42, 0.12, 1.12],
              "hand.L": [0.57, 0.0, 0.94], "hand.L:tip": [0.67, -0.04, 0.81]}
for k in list(STALKER_LM):
    if ".L" in k:
        v = STALKER_LM[k]
        STALKER_LM[k.replace(".L", ".R")] = [-v[0], v[1], v[2]]

RIGS = {
    "rimehorn": {"src": OGA + "/giant-mutant/Giant Mutant.glb", "map": MIXAMO, "objects": ["Giant_Mesh"]},
    "kharzul": {"src": OGA + "/golem_clean.blend", "map": GOLEM, "objects": ["golem"]},
    "gorehelm": {"src": OGA + "/glutton-demon/glutton_final_0.blend", "map": GLUTTON, "objects": ["glutton.lopoly"],
                 "keep": ["head", "head.001"]},
    "flayed_archivist": {"src": OGA + "/3d-horror-game-monster/Poses/Idle.fbx", "map": HORROR, "objects": ["Creature1"],
                         "material": {"albedo": OGA + "/3d-horror-game-monster/Colors/Black/test_StingrayPBS1SG_AlbedoTransparency.png",
                                      "normal": OGA + "/3d-horror-game-monster/Colors/Black/test_StingrayPBS1SG_Normal.png",
                                      "rough": 0.45}},
    "morvhaal": {"src": OGA + "/darsh-undead-creature/Darsh.glb", "map": DARSH, "objects": ["Undead"], "yaw": 180.0},
    "thalassor": {"src": OGA + "/forest-monster/forest-monster-final.blend", "map": FOREST, "objects": ["Monster"],
                  "keep": ["Neck", "Head"],
                  "material": {"albedo": OGA + "/forest-monster/texture/forest-monster-skin.png",
                               "normal": OGA + "/forest-monster/texture/forest-monster-norm.png", "rough": 0.75}},
    "ysolde": {"src": OGA + "/low-poly-werewolf/LOBISOMEM/LOBO_HIGH_POLY.fbx", "landmarks": STALKER_LM,
               "material": {"color": [0.03, 0.03, 0.035], "rough": 0.28, "metal": 0.0, "except": ["OLHO", "OLHO2"]}},
}

os.makedirs(HERE + "/specs", exist_ok=True)
for bid, r in RIGS.items():
    d = dict(r)
    d["out"] = OUT + "/%s.glb" % bid
    d["save_blend"] = OUT + "/%s.blend" % bid
    json.dump(d, open(HERE + "/specs/rig_%s.json" % bid, "w"), indent=1)
print("wrote", len(RIGS))

# ---- in-game conversion (game/tests/tools/convert_creature.tscn) ------------------------------------------------------
LOOPS = ["idle", "idle_1h", "idle_2h", "idle_bow", "idle_dagger", "idle_dual", "idle_shield", "idle_spear", "idle_staff",
         "idle_wand", "idle_hurt", "idle_combat_hurt", "idle_knight", "idle_mage", "idle_ranger", "idle_shadowblade",
         "idle_look", "walk", "walk_back", "walk_hurt", "run", "run_combat", "run_hurt", "strafe_l", "strafe_r",
         "block_loop", "charge_hold", "cast_channel", "bow_draw_hold", "fem_idle", "fem_walk", "fem_run", "fem_stroll",
         "hero_walk", "hero_run", "hero_stroll"]
CONV = {
    "rimehorn": {"height": 5.6, "tint": [0.66, 0.76, 0.92], "saturation": 0.35, "value": 0.1, "rough": 0.9},
    "kharzul": {"height": 5.2, "shader": "res://src/actors/enemy/abyss_skin.gdshader",
                "params": {"seam_color": [1.0, 0.36, 0.06], "seam_energy": 5.5, "cells": 9.0}},
    "gorehelm": {"height": 4.4, "tint": [0.24, 0.07, 0.07], "saturation": 0.8, "value": 0.35, "rough": 0.45},
    "flayed_archivist": {"height": 3.8, "tint": [0.92, 0.82, 0.8], "saturation": 0.85, "value": 0.15, "rough": 0.5},
    "morvhaal": {"height": 4.8, "tint": [0.72, 0.68, 0.62], "saturation": 0.45, "value": 0.3, "rough": 0.75},
    "ysolde": {"height": 3.5, "rough": 0.3, "glow": [{"match": "OLHO", "color": [0.55, 1.0, 0.95], "energy": 6.0}]},
    "thalassor": {"height": 6.0, "tint": [0.6, 0.78, 0.74], "saturation": 0.7, "value": 0.25, "rough": 0.8},
}
for bid, c in CONV.items():
    d = dict(c)
    d.update({"src": OUT + "/%s.glb" % bid, "out": "res://assets/characters/bh042/%s.scn" % bid, "all_clips": True,
              "loops": LOOPS, "drop": ["Icosphere"]})
    json.dump(d, open(HERE + "/specs/conv_%s.json" % bid, "w"), indent=1)
print("conv", len(CONV))
