"""Scratch-project Godot import check for the 5 Deeps GLBs (never touches game/). Verifies every expected clip exists,
its length matches the meta (anim_meta.json for humanoids, creature_meta.json for the crab) and reports the loop flag
the game will apply at runtime (character_visual._prepare_animations reads loop from the meta)."""
import json, os, re, shutil, subprocess, sys
ROOT = r"A:\Python\beyond-heroes"
CH = os.path.join(ROOT, "game", "assets", "characters")
PROJ = os.path.join(ROOT, "work", "lemondev", "bh-012", "scratch", "deeps", "godot_check")
GODOT = r"C:\Users\Lemon PC\Desktop\Godot.exe"
IDS = sys.argv[1:] or ["drowned_deckhand", "brinecaller", "reef_crawler", "barnacle_hulk", "bell_warden"]
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
		for n in (exp[id] as Dictionary).keys():
			var e: Dictionary = exp[id][n]
			if not names.has(n):
				missing.append(n); continue
			var a := p.get_animation(n)
			if float(e["length"]) > 0.0 and absf(a.length - float(e["length"])) > 0.04:
				bad.append("%s:%.3f/%.3f" % [n, a.length, float(e["length"])])
			if e["loop"]:
				loops.append(n)
		print("GLB %s tris=%d bones=%d mats=%d anims=%d expected=%d missing=%s length_mismatch=%s meta_loop=%s" % [id, tris, (sk[0] as Skeleton3D).get_bone_count(), mats.size(), names.size(), (exp[id] as Dictionary).size(), str(missing), str(bad), str(loops)])
		if missing.size() > 0 or bad.size() > 0: ok = false
		root.free()
	print("GODOT_RESULT " + ("OK" if ok else "FAIL"))
	quit(0 if ok else 1)
'''
if __name__ == "__main__":
    if os.path.exists(PROJ): shutil.rmtree(PROJ)
    os.makedirs(PROJ)
    open(os.path.join(PROJ, "project.godot"), "w").write('config_version=5\n\n[application]\nconfig/name="deeps_check"\n')
    am = json.load(open(os.path.join(CH, "anim_meta.json")))["animations"]
    cm = json.load(open(os.path.join(CH, "creature_meta.json")))
    base = ("idle idle_look idle_hurt idle_1h idle_shield idle_2h idle_dagger idle_bow idle_staff idle_spear walk run walk_back "
            "strafe_l strafe_r run_combat walk_hurt run_hurt hit_light hit_heavy hit_front hit_back hit_left hit_right "
            "stagger_small stagger_heavy knockback launch wall_impact knockdown getup death death_back death_fwd "
            "death_crumple revive charge_hold cast_channel alert taunt block_loop block_impact").split()
    extra = {"necromancer": ["staff_1", "cast_quick", "cast_area", "cast_heavy", "cast_weapon", "boss_summon"], "drowned_deckhand": ["spear_1", "spear_2", "spear_heavy"],
             "brinecaller": ["staff_1", "cast_quick", "cast_heavy", "cast_area", "cast_weapon"],
             "barnacle_hulk": ["gs_1", "gs_2", "boss_slam", "boss_charge", "cast_heavy"],
             "bell_warden": ["spear_1", "spear_2", "spear_heavy", "boss_sweep", "boss_slam", "boss_charge", "boss_roar",
                             "boss_summon", "cast_heavy"]}
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
