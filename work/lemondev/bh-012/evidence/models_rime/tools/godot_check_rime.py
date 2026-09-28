"""Scratch Godot import check for the Rimeglass Barrow GLBs (never touches game/ or shared evidence).
python godot_check_rime.py <scratch_dir> <godot.exe>  -> prints per-GLB nodes, tris, animations (name, length, loop)"""
import os, re, shutil, subprocess, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", ".."))
CHAR = os.path.join(ROOT, "game", "assets", "characters")
IDS = ["rime_husk", "barrow_jarl", "winter_crown", "ice_wraith", "rime_weaver"]
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
			print("GLB %s FAIL load" % f)
			continue
		var root := ps.instantiate()
		var mi: Array = []
		_find(root, "MeshInstance3D", mi)
		var tris := 0
		var names := []
		var mats := {}
		for m in mi:
			names.append(m.name)
			for s in m.mesh.get_surface_count():
				var mat: Material = m.mesh.surface_get_material(s)
				if mat: mats[mat.resource_name] = true
				var arr: Array = m.mesh.surface_get_arrays(s)
				var idx: PackedInt32Array = arr[Mesh.ARRAY_INDEX]
				tris += idx.size() / 3
		var sk: Array = []
		_find(root, "Skeleton3D", sk)
		var line: String = "GLB %s meshes=%s tris=%d bones=%d mats=%s" % [f, str(names), tris, (sk[0].get_bone_count() if sk.size() > 0 else 0), ",".join(PackedStringArray(mats.keys()))]
		var ap: Array = []
		_find(root, "AnimationPlayer", ap)
		if ap.size() > 0:
			var out := []
			for n in ap[0].get_animation_list():
				var a: Animation = (ap[0] as AnimationPlayer).get_animation(n)
				out.append("%s:%.2f%s" % [n, a.length, ("L" if a.loop_mode != Animation.LOOP_NONE else "")])
			line += " anims(%d)=%s" % [out.size(), " ".join(PackedStringArray(out))]
		print(line)
		root.free()
	quit(0)
'''
def main():
    scratch, godot = sys.argv[1], sys.argv[2]
    proj = os.path.join(scratch, "godot_rime")
    shutil.rmtree(proj, ignore_errors=True); os.makedirs(proj)
    open(os.path.join(proj, "project.godot"), "w").write('config_version=5\n\n[application]\nconfig/name="rime_check"\n')
    for c in IDS:
        shutil.copy(os.path.join(CHAR, c + ".glb"), proj)
        txt = open(os.path.join(CHAR, c + ".glb.import")).read()
        txt = re.sub(r'source_file="res://[^"]*/', 'source_file="res://', txt)
        open(os.path.join(proj, c + ".glb.import"), "w").write(txt)
    open(os.path.join(proj, "check.gd"), "w").write(GD)
    r = subprocess.run([godot, "--headless", "--path", proj, "--import"], capture_output=True, text=True, timeout=900)
    print("import errors:", [l for l in (r.stdout + r.stderr).splitlines() if "ERROR" in l][:5])
    r = subprocess.run([godot, "--headless", "--path", proj, "-s", "res://check.gd"], capture_output=True, text=True, timeout=900)
    for l in (r.stdout + r.stderr).splitlines():
        if l.startswith("GLB") or "ERROR" in l:
            print(l)
main()
