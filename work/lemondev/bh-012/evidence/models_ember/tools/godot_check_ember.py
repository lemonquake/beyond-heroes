"""Scratch-project Godot import check for Builder C's five Ember GLBs (never touches game/).
python godot_check_ember.py <scratch_dir> <godot.exe>"""
import json, os, re, shutil, subprocess, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), *[".."] * 6))
CH = os.path.join(ROOT, "game", "assets", "characters")
IDS = ["cinder_imp", "slag_hound", "forge_thrall", "magma_golem", "forgemaster"] + [x for x in os.environ.get("BASELINE", "").split(",") if x]
BASE = ("idle idle_look idle_hurt idle_1h idle_shield idle_2h idle_dagger idle_bow idle_staff idle_spear walk run walk_back "
        "strafe_l strafe_r run_combat walk_hurt run_hurt hit_light hit_heavy hit_front hit_back hit_left hit_right "
        "stagger_small stagger_heavy knockback launch wall_impact knockdown getup death death_back death_fwd death_crumple "
        "revive charge_hold cast_channel alert taunt block_loop block_impact").split()
EXP = {"cinder_imp": BASE + ["wand_1", "cast_quick", "cast_weapon", "dagger_1"],
       "forge_thrall": BASE + ["shield_bash", "axe_1", "axe_heavy", "sword_1"],
       "magma_golem": BASE + ["gs_1", "gs_2", "boss_slam", "cast_heavy", "boss_charge"],
       "forgemaster": BASE + ["gs_1", "gs_2", "gs_heavy", "boss_slam", "boss_sweep", "boss_charge", "boss_roar",
                              "boss_summon", "cast_heavy"],
       "goblin_skulker": BASE, "dire_wolf": "idle idle_look walk run run_combat hit_light hit_heavy stagger_small knockback death death_back alert".split(),
       "slag_hound": "idle idle_look walk run run_combat hit_light hit_heavy stagger_small knockback death death_back alert "
                     "hound_bite hound_lunge hound_breath".split()}
GD = '''extends SceneTree
func _find(n: Node, cls: String, out: Array) -> void:
	if n.is_class(cls):
		out.append(n)
	for c in n.get_children():
		_find(c, cls, out)
func _init() -> void:
	var meta := {}
	for mp in ["res://anim_meta.json", "res://creature_meta.json"]:
		var d: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(mp))
		for k in d["animations"]:
			if not meta.has(k):
				meta[k] = d["animations"][k]
	for f in DirAccess.get_files_at("res://"):
		if not f.ends_with(".glb"):
			continue
		var root := (load("res://" + f) as PackedScene).instantiate()
		var ap: Array = []
		_find(root, "AnimationPlayer", ap)
		var mi: Array = []
		_find(root, "MeshInstance3D", mi)
		var tris := 0
		var mats := {}
		for m in mi:
			for s in m.mesh.get_surface_count():
				var mat: Material = m.mesh.surface_get_material(s)
				if mat: mats[mat.resource_name] = true
				tris += (m.mesh.surface_get_arrays(s)[Mesh.ARRAY_INDEX] as PackedInt32Array).size() / 3
		var p: AnimationPlayer = ap[0]
		var items := []
		for n in p.get_animation_list():
			var a := p.get_animation(n)
			var want_loop: bool = meta.get(n, {}).get("loop", false)
			a.loop_mode = Animation.LOOP_LINEAR if want_loop else Animation.LOOP_NONE   # what character_visual.gd does
			var ml := float(meta.get(n, {}).get("length", -1.0))
			items.append("%s:%.3f:%s:%s" % [n, a.length, "L" if a.loop_mode == Animation.LOOP_LINEAR else "-", "ok" if absf(a.length - ml) < 0.04 else "LEN(meta %.3f)" % ml])
		print("GLB %s tris=%d mats=%d anims=%s" % [f, tris, mats.size(), ",".join(items)])
		root.free()
	quit(0)
'''
def main():
    scratch, godot = sys.argv[1], sys.argv[2]
    proj = os.path.join(scratch, "godot_check_ember")
    shutil.rmtree(proj, ignore_errors=True)
    os.makedirs(proj)
    open(os.path.join(proj, "project.godot"), "w").write('config_version=5\n\n[application]\nconfig/name="ember_check"\n')
    for i in IDS:
        shutil.copy(os.path.join(CH, i + ".glb"), proj)
        t = open(os.path.join(CH, i + ".glb.import")).read()
        t = "\n".join(l for l in t.splitlines() if not l.startswith(("uid=", "path=", "dest_files=")))
        open(os.path.join(proj, i + ".glb.import"), "w").write(re.sub(r'source_file="res://[^"]*/', 'source_file="res://', t) + "\n")
    for m in ("anim_meta.json", "creature_meta.json"):
        shutil.copy(os.path.join(CH, m), proj)
    open(os.path.join(proj, "check.gd"), "w").write(GD)
    r = subprocess.run([godot, "--headless", "--path", proj, "--import"], capture_output=True, text=True, timeout=1200)
    ierr = [l for l in (r.stdout + r.stderr).splitlines() if "ERROR" in l]
    r = subprocess.run([godot, "--headless", "--path", proj, "-s", "res://check.gd"], capture_output=True, text=True, timeout=600)
    ok = True
    print(f"import errors: {len(ierr)} {ierr[:3]}")
    for l in r.stdout.splitlines():
        if not l.startswith("GLB "):
            continue
        name = l.split()[1][:-4]
        anims = {a.split(":")[0]: a.split(":") for a in l.split("anims=")[1].split(",")}
        miss = [c for c in EXP[name] if c not in anims]
        bad = [a[0] for a in anims.values() if a[3] != "ok"]
        loops = [a[0] for a in anims.values() if a[2] == "L"]
        ok &= not miss and not bad
        print(f"{name}: {l.split(' anims=')[0].split(' ', 2)[2]} clips={len(anims)} missing={miss} length_bad={bad} looping={loops}")
    print("RESULT", "OK" if ok else "FAIL")
    return 0 if ok else 1
if __name__ == "__main__":
    sys.exit(main())
