"""Godot import check for the bh-013 Builder C creature GLBs on a THROWAWAY project (never game/).

python godot_check_creatures.py --godot "C:/Users/Lemon PC/Desktop/Godot.exe" [ids...]
Copies the GLBs (+ .import settings without uid/path lines) into work/lemondev/bh-013/scratch/creatures/godot_check,
imports headless, lists every AnimationPlayer clip with length + imported loop mode, checks the expected clips and the
loop mode the game applies (character_visual._prepare_animations: DB.anim(name).loop from anim_meta.json, then
creature_meta.json for keys anim_meta lacks), prints triangles / bones / materials. Output -> ../godot_check.txt
"""
import json
import os
import re
import shutil
import subprocess
import sys

ROOT = r"A:\Python\beyond-heroes"
CHAR = os.path.join(ROOT, "game", "assets", "characters")
PROJ = os.path.join(ROOT, "work", "lemondev", "bh-013", "scratch", "creatures", "godot_check")
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "godot_check.txt")
CREATURE = "idle idle_look walk run run_combat hit_light hit_heavy stagger_small knockback death death_back alert".split()
ALL = {
    "gloam_ooze": ["ooze_slam", "ooze_spit", "ooze_split"],
    "tunnel_maw": ["maw_bite", "maw_slam", "maw_spit", "maw_burrow", "maw_emerge"],
    "stonegaze_basilisk": ["basilisk_bite", "basilisk_gaze", "basilisk_tail"],
    "shellback_grinder": ["shell_bite", "shell_swipe", "shell_curl", "shell_roll", "shell_uncurl", "shell_flipped"],
}

GD = r'''extends SceneTree
func _find(n: Node, cls: String, out: Array) -> void:
	if n.is_class(cls):
		out.append(n)
	for c in n.get_children():
		_find(c, cls, out)
func _init() -> void:
	for f in DirAccess.get_files_at("res://"):
		if not f.ends_with(".glb"):
			continue
		var ps: PackedScene = load("res://" + f)
		if ps == null:
			print("GLB %s LOADFAIL" % f)
			continue
		var root := ps.instantiate()
		var sk: Array = []
		_find(root, "Skeleton3D", sk)
		var ap: Array = []
		_find(root, "AnimationPlayer", ap)
		var mi: Array = []
		_find(root, "MeshInstance3D", mi)
		var mats := {}
		var tris := 0
		for m in mi:
			var mesh: Mesh = m.mesh
			for s in mesh.get_surface_count():
				var mat := mesh.surface_get_material(s)
				if mat:
					mats[mat.resource_name] = true
				var arr := mesh.surface_get_arrays(s)
				var idx: PackedInt32Array = arr[Mesh.ARRAY_INDEX]
				tris += idx.size() / 3
		print("GLB %s tris=%d bones=%d materials=%s" % [f, tris, (sk[0] as Skeleton3D).get_bone_count() if sk.size() > 0 else 0, ",".join(PackedStringArray(mats.keys()))])
		if ap.size() > 0:
			var p: AnimationPlayer = ap[0]
			for n in p.get_animation_list():
				var a := p.get_animation(n)
				print("CLIP %s %s %.3f loop=%d" % [f, n, a.length, a.loop_mode])
		root.free()
	quit(0)
'''


def game_loop(name, anim, crea):
    d = anim.get(name) or crea.get(name) or {}
    return bool(d.get("loop", False))


def main():
    godot = sys.argv[sys.argv.index("--godot") + 1] if "--godot" in sys.argv else "godot"
    ids = [a for a in sys.argv[1:] if a in ALL] or [k for k in ALL if os.path.exists(os.path.join(CHAR, k + ".glb"))]
    if os.path.exists(PROJ):
        shutil.rmtree(PROJ)
    os.makedirs(PROJ)
    with open(os.path.join(PROJ, "project.godot"), "w") as f:
        f.write('config_version=5\n\n[application]\nconfig/name="bh013_creatures_check"\n')
    for n in ids:
        shutil.copy(os.path.join(CHAR, n + ".glb"), PROJ)
        txt = open(os.path.join(CHAR, n + ".glb.import")).read()
        txt = "\n".join(l for l in txt.splitlines() if not l.startswith(("uid=", "path=", "dest_files=")))
        txt = re.sub(r'source_file="res://[^"]*/', 'source_file="res://', txt)
        open(os.path.join(PROJ, n + ".glb.import"), "w").write(txt + "\n")
    open(os.path.join(PROJ, "check.gd"), "w").write(GD)
    anim = json.load(open(os.path.join(CHAR, "anim_meta.json"))).get("animations", {})
    cm = json.load(open(os.path.join(CHAR, "creature_meta.json")))
    crea = cm.get("animations", {})
    ver = subprocess.run([godot, "--version"], capture_output=True, text=True).stdout.strip()
    r = subprocess.run([godot, "--headless", "--path", PROJ, "--import"], capture_output=True, text=True, timeout=1800)
    imp_err = [l for l in (r.stdout + r.stderr).splitlines() if "ERROR" in l]
    r = subprocess.run([godot, "--headless", "--path", PROJ, "-s", "res://check.gd"], capture_output=True, text=True,
                       timeout=1800)
    lines = (r.stdout + r.stderr).splitlines()
    clips = {}
    for l in lines:
        if l.startswith("CLIP "):
            _, f, name, ln, lp = l.split()
            clips.setdefault(f[:-4], {})[name] = (float(ln), lp)
    rep = [f"Godot {ver}, throwaway project {PROJ}", f"import errors: {len(imp_err)} {imp_err[:5]}"]
    ok = not imp_err
    for n in ids:
        exp = CREATURE + ALL[n]
        got = clips.get(n, {})
        miss = [c for c in exp if c not in got]
        rep += [l for l in lines if l.startswith(f"GLB {n}.glb")]
        model = cm.get("models", {}).get(n, {}).get("clips", {})
        bad_len = [c for c in exp if c in got and c in model and abs(got[c][0] - model[c]["length"]) > 0.02]
        rep.append(f"  {n}: {len(got)} clips, missing {miss}, length mismatches vs models.{n}: {bad_len}")
        rep.append("  " + ", ".join(f"{c} {got[c][0]:.3f}s imported {got[c][1]} game-loop={int(game_loop(c, anim, crea))}"
                                    for c in exp if c in got))
        own_bad = [c for c in ALL[n] if c in model and bool(model[c]["loop"]) != game_loop(c, anim, crea)]
        rep.append(f"  own clip loop flags (model vs what the game applies) mismatched: {own_bad}")
        ok = ok and not miss and not bad_len and not own_bad
    rep.append("RESULT " + ("OK" if ok else "FAIL"))
    open(OUT, "w").write("\n".join(rep) + "\n")
    print("\n".join(rep))


if __name__ == "__main__":
    main()
