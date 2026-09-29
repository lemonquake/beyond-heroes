class_name TownRowBuilder
extends RefCounted
## Builds a town's trade quarter from DataTownRows (bh-018): every shopkeeper's own purpose-built stand (environment kit
## `stand_*`, `station_*`), placed and turned as the table says, with its lights, forge fire, chimney smoke and crafting
## hotspots hung on the model's own sockets (light_a, light_b, flame, smoke, use). No sign-poles, no lettered boards:
## the goods on the stand are its sign, and the shopkeeper's name plate names it. The Shrine of the Fallen keeps its
## old dressing (Veyra is a spirit-caller, not a merchant).

const WARM := Color(1.0, 0.72, 0.42)

static func build(b: MapBuilder, map_id: StringName) -> void:
	var row := DataTownRows.row(map_id)
	if row.is_empty():
		return
	for s in row.stands:
		stand(b, s)

static func has_model(name: String) -> bool:
	return name != "" and ResourceLoader.exists(MapBuilder.ENV_DIR % name)

static func stand(b: MapBuilder, s: Dictionary) -> void:
	var p: Vector3 = s.pos
	var yaw: float = s.yaw
	var fwd := DataTownRows.front(s)
	var side := DataTownRows.side(s)
	var kind := String(s.kind)
	if kind == DataTownRows.SHRINE:
		_shrine(b, s, fwd, side)
	elif kind == DataTownRows.DUMMY:
		_dummy(b, s)
	else:
		var model := String(s.get("model", ""))
		var n: Node3D
		if has_model(model):
			n = b.kit(model, p, yaw, 1.0, b.props, true)
			n.name = "Stand_%s" % s.id
			_dress(b, n)
		else:
			# a stand whose model is not built yet: the plain market stall, so the quarter still works
			n = b.kit("market_stall", p, yaw, 1.0, b.props, true)
			n.name = "Stand_%s" % s.id
			b.light(b.socket_pos(n, "light"), WARM, 1.8, 7.0, false, true)
		if s.has("station"):
			var at: Vector3 = b.socket_pos(n, "use") if n.find_child("use", true, false) else DataTownRows.customer_spot(s)
			b.crafting_station(StringName(s.station), Vector3(at.x, 0, at.z), String(s.get("label", "")))
		if kind == DataTownRows.VAULT:
			var at: Vector3 = b.socket_pos(n, "use") if n.find_child("use", true, false) else DataTownRows.customer_spot(s)
			var vp := VaultPoint.new()
			vp.position = Vector3(at.x, b.ground(at.x, at.z), at.z)
			b.markers.add_child(vp)
	if b.has_method("keep_clear"):
		b.call("keep_clear", p.x, p.z, 3.8)

## bh-019: a practice dummy (it carries its own model; the "Stand_" holder keeps the row's stand count honest).
static func _dummy(b: MapBuilder, s: Dictionary) -> void:
	var p: Vector3 = s.pos
	var holder := Node3D.new()
	holder.name = "Stand_%s" % s.id
	holder.position = Vector3(p.x, b.ground(p.x, p.z), p.z)
	holder.rotation.y = deg_to_rad(float(s.yaw))
	b.props.add_child(holder)
	var d := PracticeDummy.new()
	holder.add_child(d)

## Lights, fire and smoke at the stand model's sockets.
static func _dress(b: MapBuilder, n: Node3D) -> void:
	for sname in ["light_a", "light_b"]:
		if n.find_child(sname, true, false):
			b.light(b.socket_pos(n, sname), WARM, 1.9 if sname == "light_a" else 1.3, 7.5, false, true)
	if n.find_child("flame", true, false):
		var f := b.socket_pos(n, "flame")
		b.flame(f, 0.7)
		b.light(f + Vector3(0, 0.5, 0), Color(1.0, 0.55, 0.25), 2.6, 7.0, false, true)
		var sparks := VFXLib.particles(Color(1.0, 0.6, 0.25, 0.9), 10, 1.2, false, 0.2, 1.4, 25.0, Vector3(0, 1.2, 0), 0.06, false)
		sparks.position = f + Vector3(0, 0.2, 0)
		b.deco.add_child(sparks)
	if n.find_child("smoke", true, false):
		var smoke := VFXLib.particles(Color(0.32, 0.32, 0.34, 0.22), 12, 4.0, false, 1.2, 0.7, 8.0, Vector3(0, 0.7, 0), 0.25, false)
		smoke.position = b.socket_pos(n, "smoke")
		b.deco.add_child(smoke)

static func _shrine(b: MapBuilder, s: Dictionary, fwd: Vector3, side: Vector3) -> void:
	# a small open shrine: weapons of the fallen, candles and a cold spirit light; the Tempo-Caller keeps it
	var p: Vector3 = s.pos
	var yaw: float = s.yaw
	b.kit("shrine_small", p - fwd * 0.6, yaw, 1.5, b.props, true)
	b.candles(p + fwd * 0.9 + side * 1.3, 1.0, true)
	b.candles(p + fwd * 0.5 - side * 1.5, 1.0, true)
	b.decor("weapons_discarded", p + fwd * 1.4 + side * 2.2, yaw + 40.0, 1.0, true, true)
	b.decor("weapons_discarded", p + fwd * 1.2 - side * 2.4, yaw - 70.0, 0.9, true, true)
	b.kit("banner_torn", p - side * 2.4 + Vector3(0, 3.0 + b.ground(p.x, p.z), 0), yaw, 0.8, b.deco)
	b.light(p + Vector3(0, 1.8 + b.ground(p.x, p.z), 0) + fwd * 0.4, Color(0.55, 0.95, 1.0), 1.8, 7.5, false, true)
	var motes := VFXLib.particles(Color(0.6, 0.95, 1.0, 0.7), 24, 3.0, false, 0.08, 0.35, 60.0, Vector3(0, 0.25, 0), 1.6)
	motes.position = p + Vector3(0, 0.6 + b.ground(p.x, p.z), 0) + fwd * 0.2
	b.deco.add_child(motes)
