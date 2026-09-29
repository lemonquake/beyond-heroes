class_name TownRowBuilder
extends RefCounted
## Builds a town's trade street from DataTownRows (bh-017): a signed gateway, then a stand for every merchant and crafting
## station along both sides, each with its trade painted on a big sign, a coloured pennant, a stall, a customer mat and
## a warm light — so a first-time hero can see at a glance where the potions, the arms, the rare dealer, the forge and
## the Tempo-Caller are. The camera looks from the south, so every sign faces +Z and its lettering turns with the view.

const WOOD := Color(0.17, 0.105, 0.06)

static func build(b: MapBuilder, map_id: StringName) -> void:
	var row := DataTownRows.row(map_id)
	if row.is_empty():
		return
	gateway(b, row)
	for s in row.stands:
		stand(b, s)

static func _mat(c: Color, glow := 0.0, rough := 0.85) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = c
	m.roughness = rough
	if glow > 0.0:
		m.emission_enabled = true
		m.emission = c
		m.emission_energy_multiplier = glow
	return m

static func _box(parent: Node3D, size: Vector3, pos: Vector3, mat: Material) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = size
	mi.mesh = bm
	mi.material_override = mat
	mi.position = pos
	parent.add_child(mi)
	return mi

static func _label(text: String, font: Font, size: int, px: float, col: Color, pos: Vector3, parent: Node3D) -> Label3D:
	var l := Label3D.new()
	l.text = text
	l.font = font
	l.font_size = size
	l.pixel_size = px
	l.billboard = BaseMaterial3D.BILLBOARD_FIXED_Y
	l.modulate = col
	l.outline_size = 10
	l.outline_modulate = Color(0.05, 0.03, 0.015, 0.95)
	l.position = pos
	parent.add_child(l)
	return l

static func _iron() -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = Color(0.12, 0.115, 0.11)
	m.metallic = 0.75
	m.roughness = 0.55
	return m

static func _wood() -> Material:
	var m = MaterialLibrary.env("BH_WoodDark")
	return m if m != null else _mat(WOOD)

## A trade sign on an iron arm: a wooden post, an arm reaching over the street, and the trade's own object hanging from it.
static func hang_sign(b: MapBuilder, foot: Vector3, toward: Vector3, model: String, title: String, sub: String, col: Color, size := 0.9) -> TownSign:
	var y := b.ground(foot.x, foot.z)
	var top := 3.7
	var post := MeshInstance3D.new()
	var pm := CylinderMesh.new()
	pm.top_radius = 0.06
	pm.bottom_radius = 0.08
	pm.height = top
	post.mesh = pm
	post.material_override = _wood()
	post.position = Vector3(foot.x, y + top * 0.5, foot.z)
	b.deco.add_child(post)
	var iron := _iron()
	var arm_len := 1.0
	var arm := MeshInstance3D.new()
	var am := BoxMesh.new()
	am.size = Vector3(0.05, 0.05, arm_len)
	arm.mesh = am
	arm.material_override = iron
	var arm_yaw := atan2(toward.x, toward.z)
	arm.position = Vector3(foot.x, y + top - 0.12, foot.z) + toward * arm_len * 0.5
	arm.rotation.y = arm_yaw
	b.deco.add_child(arm)
	var hook := Vector3(foot.x, y + top - 0.12, foot.z) + toward * (arm_len - 0.1)
	var chain := MeshInstance3D.new()
	var cm := CylinderMesh.new()
	cm.top_radius = 0.012
	cm.bottom_radius = 0.012
	cm.height = 0.3
	chain.mesh = cm
	chain.material_override = iron
	chain.position = hook + Vector3(0, -0.15, 0)
	b.deco.add_child(chain)
	var sign := TownSign.new().setup(model, title, sub, col, size)
	sign.position = hook + Vector3(0, -0.3 - size * 0.5, 0)
	sign.label_height = size * 0.5 + 1.4
	b.deco.add_child(sign)
	return sign

## No structure at the entrance (an arch in an open square marks nothing): only the street's name, as a plate that appears
## when the hero walks up to it.
static func gateway(b: MapBuilder, row: Dictionary) -> void:
	var g: Vector3 = row.gate
	var gs := TownSign.new().setup("", String(row.gate_text), String(row.gate_sub), row.col, 0.5, false)
	gs.position = Vector3(g.x, b.ground(g.x, g.z) + 2.2, g.z)
	gs.label_height = 0.0
	b.deco.add_child(gs)

static func stand(b: MapBuilder, s: Dictionary) -> void:
	var p: Vector3 = s.pos
	var yaw: float = s.yaw
	var col: Color = s.col
	var y := b.ground(p.x, p.z)
	var fwd := DataTownRows.front(s)
	var side := fwd.cross(Vector3.UP)
	var kind := String(s.kind)
	if kind == DataTownRows.SHRINE:
		_shrine(b, s, fwd, side)
	else:
		var st := b.kit("market_stall", p, yaw, 1.0, b.props, true)
		b.light(b.socket_pos(st, "light"), Color(1.0, 0.72, 0.42), 1.8, 7.0, false, true)
		if kind == DataTownRows.STATION:
			_station(b, s, fwd, side)
	# the trade's own object hangs over the street from an iron arm at the stall's corner
	hang_sign(b, p + fwd * 2.1 - side * 2.1, fwd, String(s.get("sign", "")), String(s.title), "" if kind == DataTownRows.STATION else String(s.sub), col, float(s.get("sign_size", 0.9)) * 1.4)
	var lan := p + fwd * 2.9 + side * 2.3
	var lk := b.kit("lantern_stand", Vector3(lan.x, 0, lan.z), rad_to_deg(atan2(-fwd.x, -fwd.z)), 1.0, b.props, true)
	b.light(b.socket_pos(lk, "light"), Color(1.0, 0.72, 0.42), 1.8, 7.0, false, true)
	if b.has_method("keep_clear"):
		b.call("keep_clear", p.x, p.z, 3.8)

static func _station(b: MapBuilder, s: Dictionary, fwd: Vector3, side: Vector3) -> void:
	var p: Vector3 = s.pos
	var yaw: float = s.yaw
	var station: StringName = s.station
	var at := p + fwd * 1.55
	match station:
		&"alchemy":
			var hearth := b.kit("cooking_hearth", p + side * 2.7 - fwd * 0.1, yaw, 1.0, b.props, true)
			b.flame(b.socket_pos(hearth, "flame"), 0.8)
			b.light(b.socket_pos(hearth, "light"), Color(0.6, 1.0, 0.7), 2.2, 7.0, false, true)
			b.kit("bookshelf_full", p - fwd * 1.5 - side * 0.5, yaw, 0.8, b.props, true)
			b.candles(Vector3(p.x, 1.05, p.z) + fwd * 0.6 + side * 0.9, 0.9, true)
		&"workbench":
			b.kit("table_long", p + fwd * 0.05, yaw + 90.0, 0.8, b.props, true)
			b.kit("trunk", p + side * 2.5, yaw, 1.0, b.props, true)
			b.decor("weapons_discarded", p + fwd * 3.0 + side * 1.5, yaw + 30.0, 0.8)
		&"forge":
			b.kit("anvil", p + fwd * 1.15, yaw + 90.0, 1.0, b.props, true)
			b.brazier(p + side * 2.6 + fwd * 0.6, 3.4, false, true)
			b.kit("weapon_rack", p - side * 2.5 + fwd * 0.3, yaw, 1.0, b.props, true)
			b.kit("armor_stand", p + side * 1.0 - fwd * 1.3, yaw, 1.0, b.props, true)
			at = p + fwd * 1.15 + side * 0.9
	b.crafting_station(station, Vector3(at.x, 0, at.z), String(s.label))

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
