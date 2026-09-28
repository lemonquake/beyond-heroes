"""Scratch Godot import check for the bh-013 Builder D GLBs (never touches game/ or shared evidence).
python godot_check_floaters.py <scratch_dir> <godot.exe> -> per GLB: node tree (Godot-space position / rotation),
triangles, materials; plus a wing-flap sanity check (wing tip must rise for +/- flap as the game applies it)."""
import os, re, shutil, subprocess, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", ".."))
CHAR = os.path.join(ROOT, "game", "assets", "characters")
IDS = ["hive_drone", "gloomwraith", "prism_sentinel", "void_rift", "hive_nest"]
GD = r'''extends SceneTree
func _walk(n: Node, depth: int, out: Dictionary) -> void:
	if n is Node3D and depth > 0:
		var n3 := n as Node3D
		var line := "  ".repeat(depth) + "%s [%s] pos=%s rot_deg=%s" % [n.name, n.get_class(), str(n3.position.snapped(Vector3.ONE * 0.001)), str(n3.rotation_degrees.snapped(Vector3.ONE * 0.1))]
		if n is MeshInstance3D:
			var m: Mesh = (n as MeshInstance3D).mesh
			var t := 0
			for s in m.get_surface_count():
				var mat: Material = m.surface_get_material(s)
				if mat: out["mats"][mat.resource_name] = true
				var arr: Array = m.surface_get_arrays(s)
				var idx: PackedInt32Array = arr[Mesh.ARRAY_INDEX]
				t += idx.size() / 3 if idx.size() > 0 else (arr[Mesh.ARRAY_VERTEX] as PackedVector3Array).size() / 3
			out["tris"] += t
			line += " tris=%d aabb=%s" % [t, str(m.get_aabb().size.snapped(Vector3.ONE * 0.01))]
		out["lines"].append(line)
	for c in n.get_children():
		_walk(c, depth + 1, out)
func _init() -> void:
	for f in DirAccess.get_files_at("res://"):
		if not f.ends_with(".glb"):
			continue
		var ps: PackedScene = load("res://" + f)
		if ps == null:
			print("GLB %s FAIL load" % f)
			continue
		var root := ps.instantiate()
		var out := {"lines": [], "tris": 0, "mats": {}}
		_walk(root, 0, out)
		var sk := root.find_children("*", "Skeleton3D", true, false)
		var ap := root.find_children("*", "AnimationPlayer", true, false)
		print("GLB %s tris=%d skeletons=%d animplayers=%d mats=%s" % [f, out["tris"], sk.size(), ap.size(), ",".join(PackedStringArray(out["mats"].keys()))])
		for l in out["lines"]:
			print("NODE " + l)
		for need in ["core", "ring_1", "ring_2", "ring_3", "ribbons", "wing_l", "wing_r", "base"]:
			var nd := root.find_child(need, true, false)
			print("HAS %s %s: %s" % [f, need, "yes" if nd else "no"])
		for wi in 2:
			var w := root.find_child(["wing_l", "wing_r"][wi], true, false) as Node3D
			if w == null:
				continue
			var mi := w as MeshInstance3D
			var aabb := mi.mesh.get_aabb()
			var tip := Vector3(aabb.end.x if wi == 0 else aabb.position.x, 0, 0)
			var rest := w.transform
			var res := []
			for flap in [deg_to_rad(35.0), -deg_to_rad(35.0)]:
				var fl: float = flap * (1.0 if wi == 0 else -1.0)
				var t := rest * Transform3D(Basis(Vector3.BACK, fl), Vector3.ZERO)
				res.append("%+.0fdeg tip_y=%.3f" % [rad_to_deg(flap), (t * tip).y - (rest * tip).y])
			print("FLAP %s %s tip_local_x=%.3f %s" % [f, w.name, tip.x, " ".join(PackedStringArray(res))])
		root.free()
	quit(0)
'''
def main():
    scratch, godot = sys.argv[1], sys.argv[2]
    proj = os.path.join(scratch, "godot_floaters")
    shutil.rmtree(proj, ignore_errors=True); os.makedirs(proj)
    open(os.path.join(proj, "project.godot"), "w").write('config_version=5\n\n[application]\nconfig/name="floaters_check"\n')
    for c in IDS:
        shutil.copy(os.path.join(CHAR, c + ".glb"), proj)
        txt = open(os.path.join(CHAR, c + ".glb.import")).read()
        txt = re.sub(r'source_file="res://[^"]*/', 'source_file="res://', txt)
        open(os.path.join(proj, c + ".glb.import"), "w").write(txt)
    open(os.path.join(proj, "check.gd"), "w").write(GD)
    r = subprocess.run([godot, "--headless", "--path", proj, "--import"], capture_output=True, text=True, timeout=900)
    errs = [l for l in (r.stdout + r.stderr).splitlines() if "ERROR" in l]
    print("import errors:", len(errs), errs[:5])
    r = subprocess.run([godot, "--headless", "--path", proj, "-s", "res://check.gd"], capture_output=True, text=True, timeout=900)
    for l in (r.stdout + r.stderr).splitlines():
        if l.startswith(("GLB", "NODE", "HAS", "FLAP")) or "ERROR" in l:
            print(l)
main()
