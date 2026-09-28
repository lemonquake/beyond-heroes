"""Godot import check for the five Hollowroot Warren GLBs on a THROWAWAY project (never game/).

python godot_check_warren.py --godot "C:/Users/Lemon PC/Desktop/Godot.exe"
Copies the GLBs (+ .import settings without uid/path lines) into work/lemondev/bh-012/scratch/warren/godot_check,
imports headless, lists every AnimationPlayer clip with length + loop mode, checks the expected clips, prints
triangles / materials. Output -> ../godot_check.txt
"""
import os
import re
import shutil
import subprocess
import sys

ROOT = r"A:\Python\beyond-heroes"
CHAR = os.path.join(ROOT, "game", "assets", "characters")
PROJ = os.path.join(ROOT, "work", "lemondev", "bh-012", "scratch", "warren", "godot_check")
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "godot_check.txt")
BASE = ("idle idle_look idle_hurt idle_1h idle_shield idle_2h idle_dagger idle_bow idle_staff idle_spear walk run "
        "walk_back strafe_l strafe_r run_combat walk_hurt run_hurt hit_light hit_heavy hit_front hit_back hit_left "
        "hit_right stagger_small stagger_heavy knockback launch wall_impact knockdown getup death death_back death_fwd "
        "death_crumple revive charge_hold cast_channel alert taunt block_loop block_impact").split()
CREATURE = "idle idle_look walk run run_combat hit_light hit_heavy stagger_small knockback death death_back alert".split()
EXPECT = {
    "sporeling": BASE + ["axe_1", "axe_2", "cast_quick"],
    "rootweaver": BASE + ["staff_1", "cast_quick", "cast_area", "cast_heavy", "cast_weapon"],
    "mycelid_hulk": BASE + ["axe_1", "axe_2", "boss_slam", "cast_heavy", "boss_charge"],
    "rot_mother": BASE + ["staff_1", "staff_heavy", "cast_area", "cast_heavy", "cast_ultimate", "boss_roar",
                          "boss_summon", "boss_slam"],
    "rootback_boar": CREATURE + ["boar_gore", "boar_charge", "boar_stomp"],
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


def main():
    godot = sys.argv[sys.argv.index("--godot") + 1] if "--godot" in sys.argv else "godot"
    if os.path.exists(PROJ):
        shutil.rmtree(PROJ)
    os.makedirs(PROJ)
    with open(os.path.join(PROJ, "project.godot"), "w") as f:
        f.write('config_version=5\n\n[application]\nconfig/name="bh012_warren_check"\n')
    for n in EXPECT:
        shutil.copy(os.path.join(CHAR, n + ".glb"), PROJ)
        txt = open(os.path.join(CHAR, n + ".glb.import")).read()
        txt = "\n".join(l for l in txt.splitlines() if not l.startswith(("uid=", "path=", "dest_files=")))
        txt = re.sub(r'source_file="res://[^"]*/', 'source_file="res://', txt)
        open(os.path.join(PROJ, n + ".glb.import"), "w").write(txt + "\n")
    open(os.path.join(PROJ, "check.gd"), "w").write(GD)
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
    for n, exp in EXPECT.items():
        got = clips.get(n, {})
        # game enemy imports keep use_name_suffixes=true (as necromancer / ghoul_brute do): block_loop -> "block"
        miss = [c for c in exp if c not in got and not (c == "block_loop" and "block" in got)]
        rep += [l for l in lines if l.startswith(f"GLB {n}.glb")]
        loops = sorted(c for c, (_, lp) in got.items() if lp != "loop=0")
        rep.append(f"  {n}: {len(got)} clips, missing {miss}; clips imported with a loop mode: {loops}")
        own = [c for c in exp if c not in BASE and c not in CREATURE]
        rep.append("  attack clips: " + ", ".join(f"{c} {got[c][0]:.3f}s {got[c][1]}" for c in own if c in got))
        ok = ok and not miss
    rep.append("RESULT " + ("OK" if ok else "FAIL"))
    open(OUT, "w").write("\n".join(rep) + "\n")
    print("\n".join(rep))


if __name__ == "__main__":
    main()
