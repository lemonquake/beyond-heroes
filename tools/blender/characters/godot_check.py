"""Godot import check on a THROWAWAY project (never on game/): copies the exported GLBs + anim_meta.json into
<scratch>/godot_check, imports them headless and reports skeleton bones, AnimationPlayer animations (names, lengths,
loop modes), materials and triangle counts. Appends a Godot section to validation.txt.

python3 godot_check.py [--scratch DIR] [--godot godot]
"""
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
CHAR = os.path.join(ROOT, "game", "assets", "characters")
WPN = os.path.join(ROOT, "game", "assets", "weapons")
EVID = os.path.join(ROOT, "work", "lemondev", "bh-002", "evidence", "characters")

GD = r'''extends SceneTree

const BONES := ["root", "hips", "spine", "chest", "neck", "head", "shoulder.L", "upper_arm.L", "forearm.L", "hand.L",
	"weapon.L", "shoulder.R", "upper_arm.R", "forearm.R", "hand.R", "weapon.R", "thigh.L", "shin.L", "foot.L", "toe.L",
	"thigh.R", "shin.R", "foot.R", "toe.R"]

func _find(n: Node, cls: String, out: Array) -> void:
	if n.is_class(cls):
		out.append(n)
	for c in n.get_children():
		_find(c, cls, out)

func _init() -> void:
	var meta: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://anim_meta.json"))
	var anims_meta: Dictionary = meta["animations"]
	var ok := true
	for f in DirAccess.get_files_at("res://"):
		if not f.ends_with(".glb"):
			continue
		var ps: PackedScene = load("res://" + f)
		if ps == null:
			print("GLB %s FAIL: could not load" % f)
			ok = false
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
				tris += idx.size() / 3 if idx.size() > 0 else (arr[Mesh.ARRAY_VERTEX] as PackedVector3Array).size() / 3
		var line := "GLB %s tris=%d materials=%s" % [f, tris, ",".join(PackedStringArray(mats.keys()))]
		if sk.size() > 0:
			var s3: Skeleton3D = sk[0]
			var missing := []
			for b in BONES:
				if s3.find_bone(b) < 0:
					missing.append(b)
			line += " skeleton=%s bones=%d missing_bones=%s" % [s3.name, s3.get_bone_count(), str(missing)]
			if missing.size() > 0:
				ok = false
		if ap.size() > 0:
			var p: AnimationPlayer = ap[0]
			var names := p.get_animation_list()
			var miss := []
			for k in anims_meta.keys():
				if not names.has(k):
					miss.append(k)
			var bad_len := []
			var loops := 0
			for n in names:
				var a := p.get_animation(n)
				if anims_meta.has(n) and absf(a.length - float(anims_meta[n]["length"])) > 0.04:
					bad_len.append("%s:%.3f/%.3f" % [n, a.length, float(anims_meta[n]["length"])])
			line += " animations=%d missing_vs_meta=%s length_mismatch=%s" % [names.size(), str(miss), str(bad_len)]
			if miss.size() > 0 or bad_len.size() > 0:
				ok = false
			# sample one pose to be sure tracks resolve on the skeleton
			var a0 := p.get_animation("sword_1")
			if a0:
				var unresolved := 0
				for t in a0.get_track_count():
					var np := a0.track_get_path(t)
					if root.get_node_or_null(NodePath(str(np).split(":")[0])) == null:
						unresolved += 1
				line += " sword_1_tracks=%d unresolved=%d" % [a0.get_track_count(), unresolved]
		print(line)
		root.free()
	print("GODOT_RESULT " + ("OK" if ok else "FAIL"))
	quit(0 if ok else 1)
'''


def main():
    args = sys.argv[1:]
    scratch = os.environ.get("BH_SCRATCH", "/tmp/claude-0/c6")
    godot = "godot"
    if "--scratch" in args:
        scratch = args[args.index("--scratch") + 1]
    if "--godot" in args:
        godot = args[args.index("--godot") + 1]
    proj = os.path.join(scratch, "godot_check")
    if os.path.exists(proj):
        shutil.rmtree(proj)
    os.makedirs(proj)
    with open(os.path.join(proj, "project.godot"), "w") as f:
        f.write('config_version=5\n\n[application]\nconfig/name="bh_glb_check"\n')
    for d in (CHAR, WPN):
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            if fn.endswith(".glb") or fn == "anim_meta.json":
                shutil.copy(os.path.join(d, fn), proj)
    with open(os.path.join(proj, "check.gd"), "w") as f:
        f.write(GD)
    ver = subprocess.run([godot, "--version"], capture_output=True, text=True).stdout.strip()
    r = subprocess.run([godot, "--headless", "--path", proj, "--import"], capture_output=True, text=True, timeout=1800)
    imp_err = [l for l in (r.stdout + r.stderr).splitlines() if "ERROR" in l]
    r = subprocess.run([godot, "--headless", "--path", proj, "-s", "res://check.gd"], capture_output=True, text=True,
                       timeout=1800)
    out = r.stdout + r.stderr
    lines = [l for l in out.splitlines() if l.startswith(("GLB ", "GODOT_RESULT"))]
    errs = [l for l in out.splitlines() if "ERROR" in l]
    sec = ["", "== Godot import check (throwaway project %s, Godot %s)" % (proj, ver)]
    sec += ["  import errors: %d %s" % (len(imp_err), imp_err[:5])]
    sec += ["  " + l for l in lines]
    sec += ["  runtime errors: %d %s" % (len(errs), errs[:5])]
    print("\n".join(sec))
    vp = os.path.join(EVID, "validation.txt")
    txt = open(vp).read() if os.path.exists(vp) else ""
    txt = re.split(r"\n== Godot import check", txt)[0].rstrip("\n") + "\n"
    with open(vp, "w") as f:
        f.write(txt + "\n".join(sec) + "\n")
    return 0 if any("GODOT_RESULT OK" in l for l in lines) else 1


if __name__ == "__main__":
    sys.exit(main())
