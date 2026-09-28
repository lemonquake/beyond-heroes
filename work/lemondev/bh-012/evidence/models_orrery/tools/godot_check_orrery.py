"""Godot import check for Builder E's five GLBs on a THROWAWAY project (never game/).
python godot_check_orrery.py --scratch DIR --godot GODOT_EXE  -> writes ../godot_check.txt"""
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", "..", ".."))
CHAR = os.path.join(ROOT, "game", "assets", "characters")
sys.path.insert(0, os.path.join(ROOT, "tools", "blender", "characters"))

BASE = ("idle idle_look idle_hurt idle_1h idle_shield idle_2h idle_dagger idle_bow idle_staff idle_spear walk run walk_back "
        "strafe_l strafe_r run_combat walk_hurt run_hurt hit_light hit_heavy hit_front hit_back hit_left hit_right "
        "stagger_small stagger_heavy knockback launch wall_impact knockdown getup death death_back death_fwd "
        "death_crumple revive charge_hold cast_channel alert taunt block_loop block_impact").split()
EXPECT = {
    "clockwork_sentry": ["bow_release", "bow_1", "sword_1"],
    "astral_duelist": ["sword_1", "sword_2", "sword_3", "sword_heavy", "dagger_heavy"],
    "void_seer": ["staff_1", "cast_quick", "cast_heavy", "cast_area", "cast_channel", "blink"],
    "astrarch": ["staff_1", "staff_heavy", "cast_heavy", "cast_area", "cast_ultimate", "cast_channel", "boss_slam",
                 "boss_sweep", "boss_summon", "boss_roar"],
    "star_mote": None,
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
		var mi: Array = []
		_find(root, "MeshInstance3D", mi)
		var tris := 0
		var mats := {}
		var nodes := []
		for m in mi:
			nodes.append(str(m.name))
			var mesh: Mesh = m.mesh
			for s in mesh.get_surface_count():
				var mat := mesh.surface_get_material(s)
				if mat:
					mats[mat.resource_name] = true
				var arr := mesh.surface_get_arrays(s)
				var idx: PackedInt32Array = arr[Mesh.ARRAY_INDEX]
				tris += idx.size() / 3
		var sk: Array = []
		_find(root, "Skeleton3D", sk)
		var ap: Array = []
		_find(root, "AnimationPlayer", ap)
		var line := "GLB %s tris=%d nodes=%s materials=%s bones=%d" % [f, tris, ",".join(PackedStringArray(nodes)), ",".join(PackedStringArray(mats.keys())), (sk[0] as Skeleton3D).get_bone_count() if sk.size() > 0 else 0]
		if ap.size() > 0:
			var p: AnimationPlayer = ap[0]
			var parts := []
			for n in p.get_animation_list():
				var a := p.get_animation(n)
				parts.append("%s:%.3f:%s" % [n, a.length, "L" if a.loop_mode != Animation.LOOP_NONE else "-"])
			line += " anims=" + ";".join(PackedStringArray(parts))
		print(line)
		root.free()
	quit(0)
'''


def main():
    a = sys.argv[1:]
    scratch = a[a.index("--scratch") + 1]
    godot = a[a.index("--godot") + 1]
    proj = os.path.join(scratch, "godot_check_orrery")
    if os.path.exists(proj):
        shutil.rmtree(proj)
    os.makedirs(proj)
    open(os.path.join(proj, "project.godot"), "w").write('config_version=5\n\n[application]\nconfig/name="orrery_check"\n')
    for c in EXPECT:
        shutil.copy(os.path.join(CHAR, c + ".glb"), proj)
        txt = open(os.path.join(CHAR, c + ".glb.import")).read()
        txt = "\n".join(l for l in txt.splitlines() if not l.startswith(("uid=", "path=", "dest_files=")))
        txt = re.sub(r'source_file="res://[^"]*/', 'source_file="res://', txt)
        open(os.path.join(proj, c + ".glb.import"), "w").write(txt + "\n")
    open(os.path.join(proj, "check.gd"), "w").write(GD)
    ver = subprocess.run([godot, "--version"], capture_output=True, text=True).stdout.strip()
    r = subprocess.run([godot, "--headless", "--path", proj, "--import"], capture_output=True, text=True, timeout=1800)
    imp_err = [l for l in (r.stdout + r.stderr).splitlines() if "ERROR" in l]
    r = subprocess.run([godot, "--headless", "--path", proj, "-s", "res://check.gd"], capture_output=True, text=True,
                       timeout=600)
    meta = json.load(open(os.path.join(CHAR, "anim_meta.json")))["animations"]
    out = [f"Godot {ver} scratch import ({proj}); import errors: {len(imp_err)} {imp_err[:3]}"]
    ok = True
    for l in (r.stdout + r.stderr).splitlines():
        if not l.startswith("GLB "):
            continue
        name = l.split()[1][:-4]
        head = l.split(" anims=")[0]
        out.append(head)
        exp = EXPECT[name]
        if exp is None:
            need = {"core", "ring_1", "ring_2", "ring_3", "ribbons"}
            nodes = set(re.search(r"nodes=(\S*)", l).group(1).split(","))
            res = "OK" if need <= nodes and " anims=" not in l else "FAIL"
            ok &= res == "OK"
            out.append(f"  floating nodes {sorted(nodes)} -> {res}")
            continue
        anims = {}
        for tok in l.split(" anims=")[1].split(";"):
            n, ln, lp = tok.rsplit(":", 2)
            anims[n] = (float(ln), lp == "L")
        bad = []
        for c in list(dict.fromkeys(BASE + exp)):
            key = c
            if c not in anims and c.endswith("_loop") and c[:-5] in anims:
                key = c[:-5]           # use_name_suffixes=true strips _loop and sets loop mode
            if key not in anims:
                bad.append(f"{c}:missing")
                continue
            ln, lp = anims[key]
            want_loop = bool(meta.get(c, {}).get("loop", False))
            if c not in meta:
                continue
            if abs(ln - float(meta[c]["length"])) > 0.04:
                bad.append(f"{c}:len {ln:.3f}/{meta[c]['length']} loop {lp}/{want_loop}")
        res = "OK" if not bad else "FAIL " + str(bad)
        ok &= not bad
        out.append(f"  {len(anims)} anims; attack clips {exp}: " + ", ".join(
            f"{c}={anims.get(c, (0, 0))[0]:.3f}s{'(loop)' if anims.get(c, (0, 0))[1] else ''}" for c in exp) + f" -> {res}")
    out.append("note: loop modes are applied at runtime by character_visual.gd from anim_meta.json (the game's existing "
               "enemies import the same way); block_loop imports as 'block' (use_name_suffixes=true, like every enemy)")
    out.append("RESULT " + ("OK" if ok else "FAIL"))
    txt = "\n".join(out)
    print(txt)
    open(os.path.join(HERE, "..", "godot_check.txt"), "w").write(txt + "\n")


if __name__ == "__main__":
    main()
