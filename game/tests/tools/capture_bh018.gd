extends Node
## bh-018 evidence (real renderer): town trade quarters, dungeon gates, the socketing system.
##   godot --path game --resolution 1916x1011 res://tests/tools/capture_bh018.tscn -- --out=<dir> --only=gates,towns
## Map views use a free camera at the game's own pitch (54 deg); `gates` also prints how high each gate's
## floor stands above the ground around it and whether a walker reaches the dais.

var args := {}
var out := ""
var only: PackedStringArray = []

func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
	out = String(args.get("out", ProjectSettings.globalize_path("res://").path_join("../work/lemondev/bh-018/evidence/shots")))
	only = String(args.get("only", "")).split(",", false)
	DirAccess.make_dir_recursive_absolute(out)
	var world := Node3D.new()
	add_child(world)
	Game.world_parent = world
	if Game.hero == null:
		var h := HeroData.new()
		h.setup(DB.class_def(&"knight"), "Capture")
		h.init_new()
		Game.hero = h
	if _want("gates"):
		await _gates()
	if _want("towns"):
		await _towns()
	print("BH018 CAPTURE DONE -> ", out)
	get_tree().quit()

func _want(k: String) -> bool:
	return only.is_empty() or only.has(k)

var _map: MapRoot
var _cam: Camera3D

func _load(id: StringName) -> void:
	if _map != null and Game.current_map_id == id:
		return
	if Game.current_map:
		Game.current_map.queue_free()
		Game.current_map = null
		await get_tree().process_frame
	_map = Game.load_map(id)
	_cam = Camera3D.new()
	_map.add_child(_cam)
	_cam.far = 400.0
	_cam.fov = 45.0
	_cam.make_current()
	for i in 20:
		await get_tree().process_frame

func _look(target: Vector3, dist := 22.0, pitch := 54.0, yaw := 0.0) -> void:
	var off := Vector3(0, 0, dist).rotated(Vector3.RIGHT, -deg_to_rad(pitch)).rotated(Vector3.UP, deg_to_rad(yaw))
	_cam.global_position = _map.to_global(target) + off
	_cam.look_at(_map.to_global(target), Vector3.UP if pitch < 89.0 else Vector3.FORWARD)

func _shot(label: String, frames := 16) -> void:
	for i in frames:
		await get_tree().process_frame
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(out.path_join(label + ".png"))
	print("BH018 SHOT ", label)

func _gates() -> void:
	for id in DataDungeons.order():
		var s: Dictionary = DataDungeons.get_def(id).surface
		await _load(StringName(s.map))
		var p: Vector2 = s.pos
		var t: Teleporter = null
		for tp in _map.teleporters():
			if tp.teleporter_id == DataDungeons.gate_id(id):
				t = tp
		var gy: float = 0.0
		var top := _ray_down(Vector3(p.x, 40, p.y))
		var ring := []
		for k in 8:
			var a := TAU * k / 8.0
			ring.append(snappedf(_ray_down(Vector3(p.x + cos(a) * 4.2, 40, p.y + sin(a) * 4.2)) - top, 0.01))
		print("GATE %s map=%s pos=%s ground=%.2f top=%.2f dais=%.2f ring_minus_top=%s" % [id, s.map, p, gy, top,
			(t.position.y if t else -99.0), ring])
		await get_tree().process_frame
		await _look(Vector3(p.x, top, p.y), 16.0)
		await _shot("gate_%s" % id, 12)

func _ray_down(from: Vector3) -> float:
	var space := _map.get_world_3d().direct_space_state
	var q := PhysicsRayQueryParameters3D.create(_map.to_global(from), _map.to_global(from - Vector3(0, 80, 0)), BH.LAYER_WORLD | BH.LAYER_GROUND)
	var hit := space.intersect_ray(q)
	return (_map.to_local(hit.position).y) if not hit.is_empty() else -99.0

func _towns() -> void:
	for m in [&"sanctuary", &"olivar", &"wyman_outpost"]:
		await _load(m)
		var row := DataTownRows.row(m)
		if row.is_empty():
			continue
		var rc: Rect2 = row.rect
		var c := Vector3(rc.get_center().x, 0, rc.get_center().y)
		await _look(c, 44.0, 89.0)
		await _shot("town_%s_top" % m, 12)
		await _look(c, 26.0)
		await _shot("town_%s_game" % m, 12)
		for s in row.stands:
			var sp: Vector3 = s.pos
			await _look(Vector3(sp.x, 0, sp.z), 13.0)
			await _shot("town_%s_%s" % [m, s.id], 10)
