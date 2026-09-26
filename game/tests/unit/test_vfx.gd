extends TestCase
## Directional effects must follow the attacker's facing (regression: slash arcs always pointed along world +Z).

func _init() -> void:
	strict = true

func test_slash_arcs_follow_facing() -> void:
	var holder := Node3D.new()
	host.add_child(holder)
	var prev: Node = FX.world if is_instance_valid(FX.world) else null
	FX.world = holder
	for deg in [0.0, 45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0]:
		var dir := Vector3(sin(deg_to_rad(deg)), 0, cos(deg_to_rad(deg)))
		var arc := VFXLib.slash_arc(Color.WHITE, 3.0, 120.0)
		FX.spawn_facing(arc, Vector3(2, 0, -1), dir)
		var c: Vector3 = arc.global_transform * arc.mesh.get_aabb().get_center() - arc.global_position
		c.y = 0.0
		near(rad_to_deg(c.normalized().angle_to(dir)), 0.0, 1.0, "arc centred on facing %d°" % deg)
		arc.queue_free()
	FX.world = prev if is_instance_valid(prev) else null
	holder.queue_free()
	done()

func test_no_unoriented_slash_spawns() -> void:
	# every slash_arc in gameplay code must be spawned with a facing
	for path in ["res://src/actors/player/player.gd", "res://src/actors/enemy/enemy.gd", "res://src/skills/skill_runner.gd"]:
		var src := FileAccess.get_file_as_string(path)
		for line in src.split("\n"):
			if line.find("VFXLib.slash_arc(") >= 0:
				ok(line.find("spawn_facing(") >= 0, "%s: %s" % [path.get_file(), line.strip_edges().left(80)])
	done()
