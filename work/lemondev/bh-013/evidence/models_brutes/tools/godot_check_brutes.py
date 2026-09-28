"""Scratch-project Godot import check for the bh-013 brutes/warriors GLBs (Builder B2) (never touches game/). Verifies every expected clip exists,
its length matches the meta (anim_meta.json for humanoids, creature_meta.json for the crab) and reports the loop flag
the game will apply at runtime (character_visual._prepare_animations reads loop from the meta)."""
import json, os, re, shutil, subprocess, sys
ROOT = r"A:\Python\beyond-heroes"
CH = os.path.join(ROOT, "game", "assets", "characters")
PROJ = os.path.join(ROOT, "work", "lemondev", "bh-013", "scratch", "brutes", os.environ.get("GC_PROJ", "godot_check"))
GODOT = r"C:\Users\Lemon PC\Desktop\Godot.exe"
IDS = sys.argv[1:]
sys.path.insert(0, os.path.join(ROOT, "tools", "blender", "characters"))
GD = r'''extends SceneTree
func _find(n: Node, cls: String, out: Array) -> void:
	if n.is_class(cls):
		out.append(n)
	for c in n.get_children():
		_find(c, cls, out)
func _init() -> void:
	var exp: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://expected.json"))
	var ok := true
	for id in exp.keys():
		var ps: PackedScene = load("res://%s.glb" % id)
		if ps == null:
			print("GLB %s FAIL load" % id); ok = false; continue
		var root := ps.instantiate()
		var ap: Array = []; _find(root, "AnimationPlayer", ap)
		var sk: Array = []; _find(root, "Skeleton3D", sk)
		var mi: Array = []; _find(root, "MeshInstance3D", mi)
		var tris := 0
		var mats := {}
		for m in mi:
			for s in m.mesh.get_surface_count():
				var arr: Array = m.mesh.surface_get_arrays(s)
				tris += (arr[Mesh.ARRAY_INDEX] as PackedInt32Array).size() / 3
				var mat: Material = m.mesh.surface_get_material(s)
				if mat: mats[mat.resource_name] = true
		var p: AnimationPlayer = ap[0]
		var names := p.get_animation_list()
		var missing := []
		var bad := []
		var loops := []
		var imp_loops := []
		var aliased := []
		for an in names:
			if p.get_animation(an).loop_mode != Animation.LOOP_NONE:
				imp_loops.append(an)
		for n in (exp[id] as Dictionary).keys():
			var e: Dictionary = exp[id][n]
			var nn: String = n
			if not names.has(nn) and nn == "block_loop" and names.has("block"):
				nn = "block"
				aliased.append("block_loop->block")
			if not names.has(nn):
				missing.append(n); continue
			var a := p.get_animation(nn)
			if float(e["length"]) > 0.0 and absf(a.length - float(e["length"])) > 0.04:
				bad.append("%s:%.3f/%.3f" % [n, a.length, float(e["length"])])
			if e["loop"]:
				loops.append(n)
		print("GLB %s tris=%d bones=%d mats=%d anims=%d expected=%d missing=%s length_mismatch=%s meta_loop=%s imported_loop=%s aliased=%s" % [id, tris, (sk[0] as Skeleton3D).get_bone_count(), mats.size(), names.size(), (exp[id] as Dictionary).size(), str(missing), str(bad), str(loops), str(imp_loops), str(aliased)])
		if missing.size() > 0 or bad.size() > 0: ok = false
		root.free()
	print("GODOT_RESULT " + ("OK" if ok else "FAIL"))
	quit(0 if ok else 1)
'''
if __name__ == "__main__":
    if os.path.exists(PROJ): shutil.rmtree(PROJ)
    os.makedirs(PROJ)
    open(os.path.join(PROJ, "project.godot"), "w").write('config_version=5\n\n[application]\nconfig/name="brutes_check"\n')
    am = json.load(open(os.path.join(CH, "anim_meta.json")))["animations"]
    cm = json.load(open(os.path.join(CH, "creature_meta.json")))
    base = ("idle idle_look idle_hurt idle_1h idle_shield idle_2h idle_dagger idle_bow idle_staff idle_spear walk run walk_back "
            "strafe_l strafe_r run_combat walk_hurt run_hurt hit_light hit_heavy hit_front hit_back hit_left hit_right "
            "stagger_small stagger_heavy knockback launch wall_impact knockdown getup death death_back death_fwd "
            "death_crumple revive charge_hold cast_channel alert taunt block_loop block_impact").split()
    extra = {"necromancer": ["staff_1", "cast_quick", "cast_area", "cast_heavy", "cast_weapon", "boss_summon"],
             "gravecaller": ["staff_1", "staff_heavy", "cast_quick", "cast_area", "cast_heavy", "boss_summon"],
             "riftcaller": ["cast_quick", "cast_area", "cast_heavy", "cast_ultimate", "boss_summon", "blink"],
             "mirage_weaver": ["dual_1", "dual_2", "dual_heavy", "cast_quick", "cast_area", "blink"],
             "bloodbinder": ["dagger_1", "dagger_2", "dagger_heavy", "cast_quick", "cast_heavy", "cast_area"],
             "aegis_acolyte": ["shield_bash", "sword_1", "sword_2", "cast_quick", "cast_area", "taunt"],
             "storm_herald": ["staff_1", "staff_heavy", "cast_quick", "cast_area", "cast_heavy", "cast_ultimate"],
             "mirror_knight": ["sword_1", "sword_2", "sword_heavy", "shield_bash", "taunt", "war_cry"],
             "warband_chieftain": ["axe_1", "axe_2", "axe_heavy", "war_cry", "boss_roar", "boss_slam"],
             "soulbound_twin": ["sword_1", "sword_2", "sword_3", "sword_heavy", "taunt", "cast_quick"],
             "briar_lasher": ["sword_1", "sword_2", "spear_heavy", "cast_quick", "cast_area", "boss_roar"],
             "broodhost": ["axe_1", "axe_2", "axe_heavy", "boss_slam", "boss_roar", "cast_area"],
             "goblin_sapper": ["dagger_1", "dagger_2", "cast_quick", "cast_weapon", "blink"],
             "treasure_gremlin": ["dagger_1", "cast_quick", "blink"]}
    exp = {}
    for cid in IDS:
        if cid == "reef_crawler":
            exp[cid] = {k: {"length": v["length"], "loop": v["loop"]} for k, v in cm["models"][cid]["clips"].items()}
        else:
            exp[cid] = {k: {"length": am.get(k, {}).get("length", -1.0), "loop": am.get(k, {}).get("loop", False)} for k in base + extra[cid]}
        shutil.copy(os.path.join(CH, cid + ".glb"), PROJ)
        t = open(os.path.join(CH, cid + ".glb.import")).read()
        t = "\n".join(l for l in t.splitlines() if not l.startswith(("uid=", "path=", "dest_files=")))
        t = re.sub(r'source_file="res://[^"]*/', 'source_file="res://', t)
        open(os.path.join(PROJ, cid + ".glb.import"), "w").write(t + "\n")
    json.dump(exp, open(os.path.join(PROJ, "expected.json"), "w"))
    open(os.path.join(PROJ, "check.gd"), "w").write(GD)
    r = subprocess.run([GODOT, "--headless", "--path", PROJ, "--import"], capture_output=True, text=True, timeout=1200)
    ie = [l for l in (r.stdout + r.stderr).splitlines() if "ERROR" in l]
    r = subprocess.run([GODOT, "--headless", "--path", PROJ, "-s", "res://check.gd"], capture_output=True, text=True,
                       timeout=600)
    out = [l for l in (r.stdout + r.stderr).splitlines() if l.startswith(("GLB ", "GODOT_RESULT")) or "ERROR" in l]
    print("import errors:", len(ie), ie[:5])
    print("\n".join(out))
