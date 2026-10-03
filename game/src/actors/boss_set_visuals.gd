class_name BossSetVisuals
extends RefCounted
## Authored modular boss regalia. Geometry is shared by item models and bone-bound
## worn pieces: each equipped slot is visible independently, including mixed sets.

const THEMES := {
	"dragonforge": ["Dragonforge", "682820", "e6b467", "ff632d", "axe", "knight"],
	"truth_of_raikuru": ["Truth of Raikuru", "d7e4ea", "bfa156", "65dfff", "crossbow", "ranger"],
	"crimson_glory": ["Crimson Glory", "8b1832", "f1c16b", "ffac65", "sword", "knight"],
	"grievance_of_the_fairy": ["Grievance of the Fairy", "284e42", "b5cbc6", "b9ff8b", "bow", "ranger"],
	"wailing_mistress": ["Wailing Mistress", "302345", "aa99bd", "c397ff", "staff", "mage"],
	"winter_court": ["Winter Court", "607e9f", "d9edfa", "8eeaff", "wand", "mage"],
	"sunken_crown": ["Sunken Crown", "205963", "b79964", "68edd7", "spear", "knight"],
	"thunder_abbot": ["Thunder Abbot", "233b69", "c59a58", "82baff", "staff", "mage"],
	"ashfall_pilgrim": ["Ashfall Pilgrim", "353438", "a88a70", "ff7445", "wand", "mage"],
	"starfall_hunter": ["Starfall Hunter", "25334f", "d3b774", "a4b9ff", "crossbow", "ranger"],
	"gale_nomad": ["Gale Nomad", "c6bc9e", "607d81", "85f1f3", "bow", "ranger"],
	"obsidian_oath": ["Obsidian Oath", "23222b", "bf7859", "e790c9", "greatsword", "knight"],
	"pale_requiem": ["Pale Requiem", "424f69", "d6d8c9", "8dbafa", "dagger", "shadowblade"],
	"serpent_veil": ["Serpent Veil", "194c40", "c3a469", "a1f577", "claw", "shadowblade"],
	"eclipse_dancer": ["Eclipse Dancer", "41335e", "bfc0d6", "bc93ff", "dagger", "shadowblade"]
}
const SLOTS := ["helm", "inner_garment", "armor", "leggings", "gloves_1", "gloves_2", "boots_1", "boots_2", "accessory_1", "accessory_2", "accessory_3", "accessory_4", "main_weapon"]
static var _materials := {}
static var _pieces := {}

static func has_theme(id: StringName) -> bool:
	return THEMES.has(String(id))

## bh-034: pieces worn as bone-bound regalia: the boss collections and the Ascendant collections (DataAscendant).
static func is_regalia(base: ItemBaseDef) -> bool:
	return base != null and (has_theme(base.set_id) or DataAscendant.is_ascendant(base))

## The under-layer colour beneath a regalia piece (the set's cloth).
const ASCENDANT_CLOTH := {BH.Rarity.COSMIC: "1b1840", BH.Rarity.DIVINE: "e8e2d0", BH.Rarity.ETERNAL: "4a1630", BH.Rarity.PRIMORDIAL: "3a0e0c"}

static func under_tint(base: ItemBaseDef) -> Color:
	if DataAscendant.is_ascendant(base):
		return Color(String(ASCENDANT_CLOTH.get(base.fixed_rarity, "302838"))).darkened(0.2)
	return Color(String(THEMES[String(base.set_id)][1])).darkened(0.35)

static func material(id: String, part: int) -> StandardMaterial3D:
	var key := id + str(part)
	if _materials.has(key):
		return _materials[key]
	var mat := StandardMaterial3D.new()
	mat.resource_name = "Boss_%s_%d" % [id, part]
	mat.albedo_color = Color(THEMES[id][mini(part + 1, 3)])
	mat.metallic = 0.78 if part < 2 else 0.25
	mat.roughness = 0.32 if part == 1 else 0.48
	if part == 2:
		mat.emission_enabled = true
		mat.emission = mat.albedo_color
		mat.emission_energy_multiplier = 1.3
	if part == 3:
		mat.albedo_color = Color(THEMES[id][1]).darkened(0.3)
		mat.metallic = 0.0
		mat.roughness = 0.88
		mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	_materials[key] = mat
	return mat

static func _mesh(root: Node3D, mesh: Mesh, pos: Vector3, scale_v: Vector3, mat: Material, rot := Vector3.ZERO) -> MeshInstance3D:
	var n := MeshInstance3D.new()
	n.mesh = mesh
	n.material_override = mat
	n.position = pos
	n.scale = scale_v
	n.rotation = rot
	root.add_child(n)
	return n

static func _oval(root: Node3D, p: Vector3, dimensions: Vector3, mat: Material) -> void:
	var m := SphereMesh.new()
	m.radial_segments = 16
	m.rings = 8
	_mesh(root, m, p, dimensions, mat)

static func _bar(root: Node3D, a: Vector3, b: Vector3, radius: float, mat: Material, tip := -1.0, sides := 10) -> void:
	var d := b - a
	if d.length() < 0.0001:
		return
	var m := CylinderMesh.new()
	m.height = d.length()
	m.bottom_radius = radius
	m.top_radius = radius if tip < 0 else tip
	m.radial_segments = sides
	var n := _mesh(root, m, (a + b) * 0.5, Vector3.ONE, mat)
	n.quaternion = Quaternion(Vector3.UP, d.normalized())

static func _curve(root: Node3D, points: Array, radius: float, mat: Material, taper := false) -> void:
	for i in points.size() - 1:
		var f := 1.0 - float(i) / points.size() * 0.85 if taper else 1.0
		_bar(root, points[i], points[i + 1], radius * f, mat, maxf(0.001, radius * f * 0.65) if taper else -1.0)

static func _ring(root: Node3D, p: Vector3, radius: float, tube: float, mat: Material, rot := Vector3(PI * 0.5, 0, 0)) -> void:
	var m := TorusMesh.new()
	m.inner_radius = maxf(0.002, radius - tube)
	m.outer_radius = radius + tube
	m.rings = 24
	m.ring_segments = 8
	_mesh(root, m, p, Vector3.ONE, mat, rot)

## A ridged, bevelled lance/petal rather than a flat triangle. The same outline
## supports feathers, scales, crystalline blades and overlapping breast plates.
static func _leaf(root: Node3D, a: Vector3, b: Vector3, width: float, depth: float, mat: Material) -> void:
	var axis := b - a
	var side := axis.cross(Vector3.FORWARD).normalized() * width
	if side.length() < 0.001:
		side = Vector3.RIGHT * width
	var mid := a.lerp(b, 0.38)
	var ridge := mid + Vector3(0, 0, depth)
	var back := mid - Vector3(0, 0, depth * 0.4)
	var v := [a, mid + side, b, mid - side, ridge, back]
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for tri in [[0,1,4],[1,2,4],[2,3,4],[3,0,4],[1,0,5],[2,1,5],[3,2,5],[0,3,5]]:
		for idx in tri:
			st.add_vertex(v[idx])
	st.generate_normals()
	st.index()
	_mesh(root, st.commit(), Vector3.ZERO, Vector3.ONE, mat)

static func _gem(root: Node3D, p: Vector3, radius: float, mat: Material) -> void:
	_leaf(root, p - Vector3.UP * radius, p + Vector3.UP * radius, radius * 0.65, radius * 0.45, mat)

static func _cape(root: Node3D, mat: Material, trim: Material, split: bool, length := 0.85) -> void:
	for side in [-1.0, 1.0]:
		var st := SurfaceTool.new()
		st.begin(Mesh.PRIMITIVE_TRIANGLES)
		var start := 0.035 if split else 0.0
		for row in 5:
			for col in 3:
				var quad: Array[Vector3] = []
				for corner in [Vector2(0,0),Vector2(1,0),Vector2(1,1),Vector2(0,1)]:
					var u: float = (col + corner.x) / 3.0
					var v: float = (row + corner.y) / 5.0
					quad.append(Vector3(side * (start + u * (0.2 + v * 0.22)), 0.24 - v * length, -0.24 - v * 0.15 + sin(u * PI * 3) * 0.028))
				for i in [0,1,2,0,2,3]:
					st.add_vertex(quad[i])
		st.generate_normals()
		st.index()
		_mesh(root, st.commit(), Vector3.ZERO, Vector3.ONE, mat)
		_curve(root, [Vector3(side * 0.2,0.24,-0.24), Vector3(side * 0.3,-length*0.4,-0.31),Vector3(side*0.42,0.24-length,-0.39)], 0.012, trim)
	_ring(root,Vector3(0,-0.22,-0.39),.12,.012,trim)
	for s in [-1.0,1.0]:
		_leaf(root,Vector3(0,-.16,-.405),Vector3(s*.2,-.46,-.42),.04,.012,trim)

static func create_piece(id: String, slot: String) -> Node3D:
	var cache_key := id + ":" + slot
	if _pieces.has(cache_key):
		return _pieces[cache_key].instantiate()
	var root := Node3D.new()
	root.name = "Boss_%s_%s" % [id, slot]
	var base := material(id, 0)
	var trim := material(id, 1)
	var glow := material(id, 2)
	var cloth := material(id, 3)
	var index: int = THEMES.keys().find(id)
	if slot == "helm":
		_oval(root, Vector3(0,0.04,-0.03), Vector3(0.43,0.26,0.38), base)
		_ring(root, Vector3(0,0.02,0), 0.2, 0.017, trim, Vector3.ZERO)
		for s in [-1.0,1.0]:
			_leaf(root, Vector3(s*0.16,0.04,0.08),Vector3(s*0.19,-0.16,0.1),0.06,0.026,base)
		_gem(root, Vector3(0,0.07,0.2),0.058,glow)
		_crest(root,id,index,base,trim,glow)
	elif slot == "armor":
		_oval(root, Vector3.ZERO, Vector3(0.66,0.48,0.46),base)
		for row in 4:
			for s in [-1.0,1.0]:
				_leaf(root,Vector3(s*0.29,0.16-row*0.085,0.11),Vector3(s*0.015,0.08-row*0.085,0.25),0.048,0.025,trim if row==0 else base)
		_gem(root, Vector3(0,0.08,0.255),0.095,glow)
		_shoulders(root,id,index,base,trim,glow)
		_cape(root,cloth,trim,index % 2 == 0, 0.72 + (index % 3)*0.11)
	elif slot == "inner_garment":
		_oval(root,Vector3.ZERO,Vector3(0.53,0.25,0.36),cloth)
		_ring(root,Vector3(0,0.02,0),0.25,0.026,trim,Vector3.ZERO)
		for s in [-1.0,1.0]:
			_leaf(root,Vector3(s*0.18,0.0,0.15),Vector3(s*0.12,-0.55,0.19),0.105,0.016,base)
			for row in 3:
				_gem(root,Vector3(s*0.12,-0.12-row*0.13,0.225),0.024,trim)
		_gem(root,Vector3(0,0.01,0.23),0.062,glow)
	elif slot == "leggings":
		# bh-024 fallback: a belt with a gem and a plate down each thigh
		_ring(root,Vector3(0,0.02,0),0.24,0.022,trim,Vector3.ZERO)
		_gem(root,Vector3(0,0.02,0.23),0.05,glow)
		for s in [-1.0,1.0]:
			_oval(root,Vector3(s*0.11,-0.26,0.03),Vector3(0.19,0.40,0.20),base)
			_leaf(root,Vector3(s*0.11,-0.08,0.13),Vector3(s*0.11,-0.44,0.14),0.06,0.02,trim)
	elif slot.begins_with("gloves") or slot.begins_with("boots"):
		var boot := slot.begins_with("boots")
		var length := 0.32 if boot else 0.23
		_bar(root,Vector3(0,-length*0.5,0),Vector3(0,length*0.5,0),0.10 if boot else 0.084,base,0.125 if boot else 0.1,12)
		for row in 4:
			_ring(root,Vector3(0,-length*0.4+row*length*0.26,0),0.10 if boot else 0.088,0.009,trim,Vector3.ZERO)
		_leaf(root,Vector3(0,-length*0.5,0.08),Vector3(0,length*0.8,0.10),0.082,0.035,trim)
		_gem(root,Vector3(0,length*0.15,0.145),0.045,glow)
		if boot:
			_oval(root,Vector3(0,-length*0.5,0.07),Vector3(0.19,0.10,0.34),base)
		for s in [-1.0,1.0]:
			_leaf(root,Vector3(s*0.07,length*0.2,0),Vector3(s*(0.15 if index%3==0 else 0.1),length*0.85,-0.02),0.038,0.015,base)
	elif slot.begins_with("accessory"):
		var kind := int(slot.right(1))
		var radius := 0.040 if kind <= 2 else 0.065
		_ring(root,Vector3.ZERO,radius,0.013,trim)
		_gem(root,Vector3(0,0,0.027),radius*0.78,glow)
		for k in 3 + index%5:
			var angle := k*TAU/(3+index%5)
			var p := Vector3(cos(angle),sin(angle),0)*radius
			_leaf(root,p*0.8,p*1.6,0.023,0.013,base)
		if kind >= 3:
			for s in [-1.0,1.0]:
				_curve(root,[Vector3.ZERO,Vector3(s*0.09,0.1,-0.01),Vector3(s*0.14,0.2,-0.06)],0.007,trim)
	elif slot == "sub_weapon":
		_oval(root,Vector3(0,0.12,0),Vector3(0.61,0.76,0.13),base)
		_ring(root,Vector3(0,0.14,0.08),0.235,0.026,trim)
		for s in [-1.0,1.0]:
			_leaf(root,Vector3(s*0.2,0.4,0.075),Vector3(0,-0.33,0.075),0.08,0.03,trim)
		_gem(root,Vector3(0,0.15,0.13),0.15,glow)
		_crest(root,id,index,base,trim,glow)
	else:
		_weapon(root,id,String(THEMES[id][4]),index,base,trim,glow)
	_merge(root)
	for child in root.get_children(): child.owner = root
	var packed := PackedScene.new()
	packed.pack(root)
	_pieces[cache_key] = packed
	return root

static func _crest(r: Node3D, id: String, i: int, b: Material, t: Material, g: Material) -> void:
	match id:
		"dragonforge":
			for s in [-1.0,1.0]:
				_curve(r,[Vector3(s*.16,.1,-.04),Vector3(s*.3,.25,-.07),Vector3(s*.34,.4,-.01),Vector3(s*.24,.51,.07)],.062,t,true)
				for k in 3: _leaf(r,Vector3(s*.14,.1-k*.07,-.03),Vector3(s*.32,.15-k*.06,-.08),.04,.02,b)
		"truth_of_raikuru":
			_ring(r,Vector3(0,.3,-.12),.32,.021,t)
			for s in [-1.0,1.0]: _curve(r,[Vector3(s*.21,.43,-.12),Vector3(s*.08,.24,-.08),Vector3(s*.2,.26,-.08),Vector3(s*.1,.09,-.04)],.016,g)
		"crimson_glory":
			for k in 7:
				var a := k*PI/6
				_leaf(r,Vector3(cos(a)*.17,.09+sin(a)*.07,0),Vector3(cos(a)*.3,.16+sin(a)*.38,-.01),.054,.025,t)
		"grievance_of_the_fairy":
			for s in [-1.0,1.0]:
				_curve(r,[Vector3(s*.14,.07,0),Vector3(s*.26,.25,-.03),Vector3(s*.2,.45,0)],.02,t,true)
				for k in 3: _leaf(r,Vector3(s*.22,.16+k*.065,0),Vector3(s*(.34-k*.02),.22+k*.08,.01),.055,.009,g)
		"wailing_mistress":
			for k in 9:
				var x := (k-4)*.045
				_curve(r,[Vector3(x,.15,.15),Vector3(x,-.05,.215),Vector3(x,-.31,.18)],.009,t)
			_ring(r,Vector3(0,.3,-.06),.16,.018,g)
		"winter_court":
			for k in 9:
				var a := k*TAU/9
				_leaf(r,Vector3(cos(a)*.16,.09,sin(a)*.12),Vector3(cos(a)*.24,.27+(.2 if k%2==0 else 0),sin(a)*.17),.049,.029,g)
		"sunken_crown":
			for s in [-1.0,1.0]:
				for k in 3: _curve(r,[Vector3(s*.16,.1,-.05),Vector3(s*(.25+k*.035),.2+k*.035,-.04),Vector3(s*(.23+k*.05),.33+k*.055,0)],.024,t,true)
		"thunder_abbot":
			for radius in [.25,.32]: _ring(r,Vector3(0,.14,-.17),radius,.014,t)
			for k in 8:
				var a := k*TAU/8
				_oval(r,Vector3(cos(a)*.32,.14+sin(a)*.32,-.17),Vector3.ONE*.054,g)
		"ashfall_pilgrim":
			_leaf(r,Vector3(0,.06,-.04),Vector3(0,.56,-.03),.23,.14,b)
			for s in [-1.0,1.0]: _curve(r,[Vector3(s*.05,.1,.16),Vector3(s*.12,.22,.06),Vector3(0,.42,.0)],.015,g)
		"starfall_hunter":
			for k in 5:
				var a := k*TAU/5
				_leaf(r,Vector3(0,.25,-.07),Vector3(cos(a)*.29,.25+sin(a)*.29,-.07),.048,.02,t)
			_gem(r,Vector3(0,.25,0),.095,g)
		"gale_nomad":
			for k in 6: _leaf(r,Vector3(.12,.08,-.06),Vector3(.27+k*.035,.18+k*.055,-.13),.047,.008,t if k%2 else g)
		"obsidian_oath":
			for s in [-1.0,1.0]: _leaf(r,Vector3(s*.14,.02,0),Vector3(s*.24,.48,-.01),.086,.056,b)
			_leaf(r,Vector3(0,.08,.14),Vector3(0,.33,.12),.07,.027,t)
		"pale_requiem":
			for s in [-1.0,1.0]:
				_curve(r,[Vector3(s*.12,.11,0),Vector3(s*.29,.27,-.02),Vector3(s*.36,.45,-.05)],.032,t,true)
				for k in 3: _bar(r,Vector3(s*(.2+k*.045),.2+k*.07,-.03),Vector3(s*(.13+k*.05),.31+k*.065,-.03),.015,t,0.002)
		"serpent_veil":
			for s in [-1.0,1.0]:
				_curve(r,[Vector3(s*.15,.02,0),Vector3(s*.3,.1,-.04),Vector3(s*.27,.33,0),Vector3(s*.1,.38,.02)],.034,t,true)
				_oval(r,Vector3(s*.11,.37,.05),Vector3(.10,.055,.09),b)
				_gem(r,Vector3(s*.10,.38,.1),.019,g)
		"eclipse_dancer":
			for k in 12:
				var a := -.7 + k*4.7/11
				var c := Vector3(cos(a)*.3,.27+sin(a)*.3,-.1)
				var d := Vector3(cos(a+.3)*.3,.27+sin(a+.3)*.3,-.1)
				_bar(r,c,d,.021,t)
			_gem(r,Vector3(0,.27,-.09),.072,g)

static func _shoulders(r: Node3D, id: String, i: int, b: Material, t: Material, g: Material) -> void:
	for s in [-1.0,1.0]:
		_oval(r,Vector3(s*.35,.17,0),Vector3(.30,.18,.35),b)
		for k in 3: _leaf(r,Vector3(s*(.27+k*.04),.23-k*.035,.09),Vector3(s*(.48+k*.04),.18-k*.045,.06),.08,.028,t if k==0 else b)
		match id:
			"dragonforge", "obsidian_oath":
				for k in 3: _bar(r,Vector3(s*(.32+k*.07),.22,0),Vector3(s*(.4+k*.1),.46-k*.025,-.04),.043,t if k==0 else b,0.002,6)
			"crimson_glory", "gale_nomad":
				for k in 5: _leaf(r,Vector3(s*.36,.2,-.05),Vector3(s*(.62+k*.055),.45-k*.08,-.16),.068,.015,t if k%2 else b)
			"grievance_of_the_fairy":
				for k in 3: _leaf(r,Vector3(s*.16,.05,-.23),Vector3(s*(.68-k*.13),.68-k*.32,-.27),.17,.014,g if k==0 else t)
			"wailing_mistress", "pale_requiem":
				for k in 4: _curve(r,[Vector3(s*.35,.14,.12),Vector3(s*(.45+k*.03),-.10-k*.045,.11),Vector3(s*.2,-.2-k*.025,.23)],.01,t)
			"winter_court":
				for k in 4: _leaf(r,Vector3(s*.32,.18,0),Vector3(s*(.45+k*.08),.5-k*.065,-.04),.07,.045,g)
			"sunken_crown":
				for k in 4: _curve(r,[Vector3(s*.36,.18,-.07),Vector3(s*(.47+k*.07),.33,-.09),Vector3(s*(.42+k*.085),.51-k*.04,-.04)],.023,t,true)
			"thunder_abbot":
				_ring(r,Vector3(s*.38,.28,-.10),.17,.025,t)
				_oval(r,Vector3(s*.38,.28,-.10),Vector3.ONE*.1,g)
			"ashfall_pilgrim":
				for k in 3: _oval(r,Vector3(s*(.36+k*.08),.26+k*.02,0),Vector3(.09,.13,.09),t)
			"starfall_hunter":
				_ring(r,Vector3(s*.43,.26,-.04),.18,.012,t)
				for k in 5:
					var a := k*TAU/5
					_leaf(r,Vector3(s*.43,.26,0),Vector3(s*.43+cos(a)*.23,.26+sin(a)*.23,0),.028,.012,g)
			"serpent_veil":
				_curve(r,[Vector3(s*.25,.18,-.1),Vector3(s*.48,.35,-.12),Vector3(s*.62,.25,-.02),Vector3(s*.5,.11,.11)],.043,t,true)
			"eclipse_dancer":
				_ring(r,Vector3(s*.41,.26,0),.19,.022,t)
				_leaf(r,Vector3(s*.36,.25,.03),Vector3(s*.63,.47,0),.07,.018,b)

static func _weapon(r: Node3D, id: String, typ: String, i: int, b: Material, t: Material, g: Material) -> void:
	if typ in ["bow","crossbow"]:
		var cross := typ == "crossbow"
		for s in [-1.0,1.0]:
			var p := [Vector3.ZERO,Vector3(s*.22,.12,0),Vector3(s*.42,.04,0),Vector3(s*.57,.18,0)] if cross else [Vector3.ZERO,Vector3(s*.13,s*.26,0),Vector3(s*.22,s*.49,0),Vector3(s*.08,s*.72,0)]
			_curve(r,p,.032,b)
			for k in 3: _leaf(r,p[1].lerp(p[2],k/3.0),p[1].lerp(p[2],k/3.0)+Vector3(s*.09,.12,0),.035,.016,t)
		if cross:
			_bar(r,Vector3(0,-.36,-.06),Vector3(0,.5,-.06),.052,b)
			_bar(r,Vector3(-.57,.18,0),Vector3(0,-.17,0),.004,t)
			_bar(r,Vector3(.57,.18,0),Vector3(0,-.17,0),.004,t)
			_ring(r,Vector3(0,.3,.045),.055,.012,t)
		else:
			_bar(r,Vector3(.08,.72,0),Vector3(-.08,-.72,0),.004,t)
		_gem(r,Vector3(0,0,.045),.07,g)
	elif typ in ["staff","wand","spear"]:
		var length := .92 if typ != "wand" else .44
		_bar(r,Vector3(0,-.2,0),Vector3(0,length,0),.027,b)
		for k in 7: _ring(r,Vector3(0,k*length/8,0),.031,.008,t,Vector3.ZERO)
		if typ=="spear":
			_leaf(r,Vector3(0,length-.1,0),Vector3(0,length+.48,0),.08,.025,t)
			for s in [-1.0,1.0]: _curve(r,[Vector3(0,length,0),Vector3(s*.12,length+.06,0),Vector3(s*.14,length+.27,0)],.018,t,true)
		else:
			_ring(r,Vector3(0,length+.1,0),.17,.023,t)
			_gem(r,Vector3(0,length+.1,.015),.13,g)
			for k in 5: _leaf(r,Vector3(0,length+.1,0),Vector3(cos(k*TAU/5)*.25,length+.1+sin(k*TAU/5)*.25,0),.036,.016,b)
	elif typ == "axe":
		_bar(r,Vector3(0,-.17,0),Vector3(0,.93,0),.032,b)
		for s in [-1.0,1.0]:
			_leaf(r,Vector3(0,.65,0),Vector3(s*.32,.96,0),.17,.024,t)
			_leaf(r,Vector3(s*.27,.86,0),Vector3(s*.31,.43,0),.13,.018,b)
		_gem(r,Vector3(0,.71,.05),.1,g)
	elif typ == "claw":
		_ring(r,Vector3.ZERO,.085,.027,t)
		for s in [-1.0,0.0,1.0]: _leaf(r,Vector3(s*.07,.04,0),Vector3(s*.14,.56,0),.047,.025,t)
		_gem(r,Vector3(0,.13,.04),.06,g)
	else:
		var length := .6 if typ=="dagger" else (1.35 if typ=="greatsword" else .95)
		_bar(r,Vector3(0,-.2,0),Vector3(0,.08,0),.025,b)
		_leaf(r,Vector3(0,.04,0),Vector3(0,length,0),.07 if typ=="dagger" else .11,.028,t)
		_leaf(r,Vector3(0,.12,.027),Vector3(0,length*.88,.018),.019,.011,g)
		for s in [-1.0,1.0]: _curve(r,[Vector3.ZERO,Vector3(s*.13,.04,0),Vector3(s*.23,.16,0)],.022,b,true)
		_gem(r,Vector3(0,-.18,.012),.055,g)

## Combine many authored details into one mesh per material (four surfaces at
## most) so a dressed character does not add hundreds of draw calls.
static func _merge(root: Node3D) -> void:
	var groups := {}
	for child in root.get_children():
		var mi := child as MeshInstance3D
		if not mi: continue
		var mat: Material = mi.material_override
		if not groups.has(mat):
			var st := SurfaceTool.new()
			st.begin(Mesh.PRIMITIVE_TRIANGLES)
			groups[mat] = st
		for surface in mi.mesh.get_surface_count():
			groups[mat].append_from(mi.mesh,surface,mi.transform)
		root.remove_child(mi)
		mi.free()
	for mat in groups:
		var mi := MeshInstance3D.new()
		mi.name = mat.resource_name
		mi.mesh = groups[mat].commit()
		mi.material_override = mat
		root.add_child(mi)

## bh-023: the regalia was modelled around the armoured class bodies; the hero's own body is a real person's size,
## so each piece is scaled (x across, y along the body or limb, z front to back) and shifted to sit on it.
const HERO_FIT := {
	"helm": [Vector3(0.74, 0.78, 0.80), Vector3(0.0, -0.095, 0.035)],
	"armor": [Vector3(0.80, 0.98, 0.74), Vector3(0.0, 0.0, -0.005)],
	"inner_garment": [Vector3(0.90, 1.0, 0.86), Vector3(0.0, 0.0, -0.01)],
	"gloves": [Vector3(0.84, 1.0, 0.84), Vector3.ZERO],
	"boots": [Vector3(0.82, 1.0, 0.82), Vector3.ZERO],
	"accessory_3": [Vector3.ONE, Vector3(0.0, 0.0, -0.10)],
	"accessory_4": [Vector3.ONE, Vector3(0.05, -0.02, -0.07)],
}

## bh-024: the Legguards are the other way round — authored on the hero's own legs, so it is the armoured class bodies
## (Tempos, other models) that wear them scaled up round the hips.
const CLASS_LEGS_FIT := Vector3(1.15, 1.0, 1.15)

static func _hero_fit(slot: String) -> Transform3D:
	var key := slot
	if slot.begins_with("gloves") or slot.begins_with("boots"):
		key = slot.left(slot.length() - 2)
	if not HERO_FIT.has(key):
		return Transform3D.IDENTITY
	return Transform3D(Basis.from_scale(HERO_FIT[key][0]), HERO_FIT[key][1])

static func wear(visual: Node3D, equipment: Equipment, hero := false, skip_helm := false) -> Array[Node3D]:
	var result: Array[Node3D] = []
	var skeleton: Skeleton3D = visual.skeleton
	if not skeleton: return result
	if not hero:
		_wear_special(skeleton, equipment, result)
	for slot in SLOTS:
		if slot == "main_weapon" or (slot == "helm" and skip_helm): continue
		var item := equipment.get_item(StringName(slot))
		if item == null or not is_regalia(item.base): continue
		var id := String(item.base.set_id)
		var model := item.base.model_path()
		var asc := DataAscendant.is_ascendant(item.base)
		# bh-034: one Ascendant gauntlet or boot fits either side; the right one has its own mirrored model
		if asc and slot.ends_with("_2") and (slot.begins_with("gloves") or slot.begins_with("boots")):
			var right := model.get_basename() + "_R.glb"
			if ResourceLoader.exists(right):
				model = right
		if asc and not ResourceLoader.exists(model):
			continue
		var bone := "chest"
		if slot == "helm": bone = "head"
		elif slot == "inner_garment" or slot == "leggings": bone = "hips"
		elif slot.begins_with("gloves"): bone = "forearm." + ("L" if slot.ends_with("1") else "R")
		elif slot.begins_with("boots"): bone = "shin." + ("L" if slot.ends_with("1") else "R")
		elif slot in ["accessory_1","accessory_2"]: bone = "hand." + ("L" if slot.ends_with("1") else "R")
		var bone_idx := skeleton.find_bone(bone)
		if bone_idx < 0: continue
		var rest := skeleton.get_bone_global_rest(bone_idx)
		var target := Transform3D(Basis.IDENTITY, rest.origin)
		if slot == "helm": target.origin += Vector3(0,.13,0)
		elif slot == "armor": target.origin += Vector3(0,.04,0)
		elif slot == "inner_garment" or slot == "leggings": target.origin += Vector3(0,-.05,0)
		elif slot.begins_with("gloves") or slot.begins_with("boots"):
			var end_bone := bone.replace("forearm","hand").replace("shin","foot")
			var end := skeleton.get_bone_global_rest(skeleton.find_bone(end_bone)).origin
			target.origin = rest.origin.lerp(end,.65)
			target.basis = Basis(Quaternion(Vector3.UP,(rest.origin-end).normalized()))
		elif slot == "accessory_3": target.origin += Vector3(0,.02,.29)
		elif slot == "accessory_4": target.origin += Vector3(-.23,.15,.22)
		else: target.origin += Vector3(0,-.04,.06)
		var ba := BoneAttachment3D.new()
		ba.name = "Set_" + slot
		ba.bone_name = bone
		skeleton.add_child(ba)
		if hero:
			target = Transform3D(target.basis, target.origin + _hero_fit(slot).origin) * Transform3D(_hero_fit(slot).basis, Vector3.ZERO)
		elif slot == "leggings":
			target = target * Transform3D(Basis.from_scale(CLASS_LEGS_FIT), Vector3.ZERO)
		var piece := _worn_piece(id, slot, model)
		ba.add_child(piece)
		piece.transform = rest.affine_inverse() * target
		result.append(ba)
		if asc:
			AscendantFx.dress(piece, item.base.fixed_rarity)
			if slot in ["helm", "armor"] or slot.begins_with("gloves") or slot.begins_with("accessory_3"):
				ba.add_child(AscendantFx.aura(item.base.fixed_rarity, 0.22 if slot == "armor" else 0.14))
		# bh-022: parts that follow another bone (pauldrons, hand plates, sabatons, tassets) ride their own attachment
		for child in piece.get_children():
			var nm := String(child.name)
			if not nm.begins_with("AT_") or not (child is Node3D):
				continue
			var other := nm.substr(3)
			if other.ends_with("_L") or other.ends_with("_R"):
				other = other.left(other.length() - 2) + "." + other.right(1)
			var oi := skeleton.find_bone(other)
			if oi < 0:
				continue
			var ob := BoneAttachment3D.new()
			ob.name = "SetPart_%s_%s" % [slot, other.replace(".", "_")]
			ob.bone_name = other
			skeleton.add_child(ob)
			var local := (child as Node3D).transform
			piece.remove_child(child)
			ob.add_child(child)
			(child as Node3D).transform = skeleton.get_bone_global_rest(oi).affine_inverse() * target * local
			result.append(ob)
	return result

## bh-026: the Ember Dragonhide on an armoured class body (a knight-type Tempo). The hero wears the fitted, skinned
## cuirass (HeroWear); its item model is the same cuirass as it sits on the hero in the idle pose, authored round the
## chest joint, so here it rides the chest bone, scaled out to the bulkier class body.
const SPECIAL_CLASS_FIT := Vector3(1.2, 1.02, 1.28)

static func _wear_special(skeleton: Skeleton3D, equipment: Equipment, result: Array[Node3D]) -> void:
	var item := equipment.get_item(&"armor")
	if item == null or not DataSpecialWeapons.is_special(item.base):
		return
	var bi := skeleton.find_bone("chest")
	if bi < 0:
		return
	var ba := BoneAttachment3D.new()
	ba.name = "Set_special_armor"
	ba.bone_name = "chest"
	skeleton.add_child(ba)
	var piece := ItemModels.instance(item.base)
	ba.add_child(piece)
	var rest := skeleton.get_bone_global_rest(bi)
	piece.transform = rest.affine_inverse() * Transform3D(Basis.from_scale(SPECIAL_CLASS_FIT), rest.origin)
	result.append(ba)

## bh-022: the worn piece is the item's own model (tools/blender/items/boss_regalia.py) with the game's materials;
## the older procedural regalia (create_piece) remains the fallback when a model is missing.
static func _worn_piece(id: String, slot: String, path: String) -> Node3D:
	if path != "" and ResourceLoader.exists(path):
		var ps: PackedScene = load(path)
		var n: Node3D = ps.instantiate()
		var ms: Array[MeshInstance3D] = []
		for c in n.find_children("*", "MeshInstance3D", true, false):
			ms.append(c)
		if n is MeshInstance3D:
			ms.append(n)
		MaterialLibrary.apply_character(ms, Color(0.55, 0.18, 0.16))
		return n
	return create_piece(id, slot)
