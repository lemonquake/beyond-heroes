class_name NetAvatar
extends Actor
## Another player's hero or Tempo, mirrored from their snapshots (bh-008). It walks, turns and plays the same actions
## as the original, with a name tag and a health bar. On the host it is a real target: monsters chase it and hit it,
## and every hit is forwarded to the machine that owns the original, which resolves it against the real hero. Nothing
## it does changes the world by itself.
## A fallen human hero is an interactable (bh-011): stand beside them and press Interact to revive them.

const LERP_RATE := 14.0

var owner_peer := 0
var key := ""                       # "p" the hero, "t<uid>" a Tempo
var is_hero := false
var guild_tag := ""                  # bh-027: a Call to Arms fighter's guild (shown instead of "X's Tempo")
var _target_pos := Vector3.ZERO
var _target_yaw := 0.0
var _vel := Vector3.ZERO
var _engaged := false
var _serial := -1
var _built := false
var _max_hp := 100.0
var _tag: Label3D
var _sub: Label3D                    # human heroes: "Level 3 Knight · Mobile"
var _ring: MeshInstance3D            # human heroes: a ring in their colour at their feet
var _bar: MeshInstance3D
var _bar_mat: StandardMaterial3D
var _was_alive := true
var interact_range := 2.4

func _init() -> void:
	team = BH.Team.PLAYER

func setup(peer: int, p_key: String, first: Dictionary) -> NetAvatar:
	owner_peer = peer
	key = p_key
	is_hero = p_key == "p"
	display_name = String(first.get("name", "Hero"))
	level = int(first.get("lvl", 1))
	_max_hp = maxf(1.0, float(first.get("mhp", 100.0)))
	hp = float(first.get("hp", _max_hp))
	name = "NetAvatar_%d_%s" % [peer, p_key]
	return self

func _ready() -> void:
	super._ready()
	add_to_group(&"net_ally")
	if is_hero:
		add_to_group(&"net_hero")
		add_to_group(&"interactable")      # only offered while fallen (can_interact)
	collision_layer = BH.LAYER_PLAYER
	collision_mask = 0                  # moved by snapshots, never pushed
	var cs := CollisionShape3D.new()
	var cap := CapsuleShape3D.new()
	cap.radius = 0.4
	cap.height = 1.8
	cs.shape = cap
	cs.position.y = 0.9
	add_child(cs)
	body_radius = 0.4
	body_height = 1.8
	var col := Net.player_color(owner_peer)
	_tag = Label3D.new()
	_tag.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	_tag.no_depth_test = true
	_tag.fixed_size = true
	_tag.outline_size = 12
	_tag.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	if is_hero:
		# a real person: their colour, a bold plate with a marker, class and device underneath, a ring at their feet
		_tag.pixel_size = 0.0007
		_tag.font_size = 30
		_tag.modulate = col.lightened(0.25)
		_tag.outline_modulate = Color(0.08, 0.05, 0.02, 0.95)
		_tag.position = Vector3(0, 2.42, 0)
		_tag.offset = Vector2(0, 40)             # screen-space stacking: stays readable at any camera distance
		_sub = Label3D.new()
		_sub.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		_sub.no_depth_test = true
		_sub.fixed_size = true
		_sub.pixel_size = 0.0005
		_sub.font_size = 24
		_sub.outline_size = 8
		_sub.modulate = UITheme.GOLD
		_sub.position = Vector3(0, 2.42, 0)
		add_child(_sub)
		_ring = MeshInstance3D.new()
		var tm := TorusMesh.new()
		tm.inner_radius = 0.62
		tm.outer_radius = 0.74
		tm.rings = 32
		tm.ring_segments = 6
		_ring.mesh = tm
		var rm := StandardMaterial3D.new()
		rm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		rm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		rm.albedo_color = Color(col, 0.75)
		rm.emission_enabled = true
		rm.emission = col
		rm.emission_energy_multiplier = 1.5
		_ring.material_override = rm
		_ring.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		_ring.scale = Vector3(1, 0.15, 1)
		_ring.position.y = 0.06
		add_child(_ring)
	else:
		# a Tempo: small and plain, and whose it is
		_tag.pixel_size = 0.0005
		_tag.font_size = 22
		_tag.outline_size = 8
		_tag.modulate = Color(0.8, 0.85, 0.8, 0.9)
		_tag.position = Vector3(0, 2.3, 0)
	add_child(_tag)
	var bm := QuadMesh.new()
	bm.size = Vector2(1.0, 0.09)
	_bar = MeshInstance3D.new()
	_bar.mesh = bm
	_bar_mat = StandardMaterial3D.new()
	_bar_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_bar_mat.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
	_bar_mat.no_depth_test = true
	_bar_mat.albedo_color = Color(0.3, 0.9, 0.4)
	_bar.material_override = _bar_mat
	_bar.position = Vector3(0, 2.18, 0)
	_bar.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(_bar)
	_refresh_tag()

func rebuild_stats() -> void:
	stats = DerivedStats.new()
	stats.level = level
	stats.set_stat(&"max_hp", _max_hp)
	stats.set_stat(&"move_speed", 5.0)

## Build the model the first time its appearance arrives (and again if the gear changes).
func set_appearance(app: Dictionary) -> void:
	if app.is_empty():
		return
	if visual == null:
		visual = CharacterVisual.new()
		visual.name = "Visual"
		add_child(visual)
		visual.setup(String(app.get("model", "")), float(app.get("scale", 1.0)), app.get("tint", Color.WHITE), StringName(app.get("pers", &"")))
		_built = true
	# bh-023: another player's hero wears their own look (cleaned by HeroLook before use)
	if visual.hero:
		var lk = app.get("look", {})
		if lk is Dictionary and HeroLook.signature(lk) != HeroLook.signature(visual.hero.look):
			visual.set_look(lk)
	var want: Dictionary = app.get("weapons", {})
	for hand in [&"main", &"off"]:
		var w = want.get(hand)
		var have = visual.appearance.get("weapons", {}).get(hand)
		if w == null and have != null:
			visual.detach_weapon(hand)
		elif w != null and (have == null or String(have[0]) != String(w[0])):
			visual.attach_weapon(hand, String(w[0]), w[1])
	# Reconstruct presentation-only pieces from known base IDs. Missing data from
	# an older peer also clears any previous set appearance without changing stats.
	var gear = app.get("set_gear", {})
	var equipment := Equipment.new()
	if gear is Dictionary:
		for slot in BH.SLOTS:
			var id := StringName(str(gear.get(slot, "")))
			var base := DB.item_base(id) if id != &"" else null
			if base != null and ((base.boss_exclusive and base.equip_slots.has(slot)) or (visual.hero != null and base.equipment_slots().has(slot))):
				var piece := ItemInstance.new()
				piece.base = base
				equipment.slots[slot] = piece
	visual.dress_equipment(equipment)
	if app.has("stance"):
		visual.set_stance(StringName(app.stance))

## One snapshot: [pos, yaw, vel, hp, max_hp, alive, action, serial, rate, loop, engaged, level]
func apply_state(s: Array) -> void:
	_target_pos = s[0]
	_target_yaw = s[1]
	_vel = s[2]
	hp = s[3]
	var mhp: float = s[4]
	if absf(mhp - _max_hp) > 0.5:
		_max_hp = mhp
		mark_stats_dirty()
	var now_alive: bool = s[5]
	_engaged = s[10]
	if s.size() > 11 and int(s[11]) != level:
		level = int(s[11])
		_refresh_tag()
	elif _tag and _tag.text.find(display_name) < 0:
		_refresh_tag()
	if visual and now_alive:
		var act := StringName(s[6])
		var serial := int(s[7])
		if serial != _serial:
			_serial = serial
			if act != &"":
				if bool(s[9]):
					visual.hold_action(act, float(s[8]))
				else:
					visual.play_action(act, float(s[8]))
		elif act == &"" and visual.current_action() != &"":
			visual.stop_action()
	if now_alive != _was_alive:
		_was_alive = now_alive
		alive = now_alive
		_refresh_tag()
		if visual:
			if not now_alive:
				visual.play_death(&"death")
			else:
				visual.revive()
	alive = now_alive

func snap_to(p: Vector3, yaw: float) -> void:
	_target_pos = p
	_target_yaw = yaw
	global_position = p
	rotation.y = yaw

func _physics_process(delta: float) -> void:
	if not is_finite(delta) or delta <= 0.0:
		return
	var k := 1.0 - exp(-LERP_RATE * delta)
	if global_position.distance_to(_target_pos) > 8.0:
		global_position = _target_pos       # teleported, respawned
	else:
		global_position = global_position.lerp(_target_pos + _vel * 0.05, k)
	rotation.y = lerp_angle(rotation.y, _target_yaw, k)
	if visual:
		var local := global_transform.basis.inverse() * Vector3(_vel.x, 0, _vel.z)
		visual.update_locomotion(Vector2(local.x, local.z), _engaged, 0.0, delta)
	var f := clampf(hp / maxf(1.0, _max_hp), 0.0, 1.0)
	if _bar:
		_bar.scale = Vector3(maxf(0.02, f), 1, 1)
		_bar_mat.albedo_color = Color(0.3, 0.9, 0.4).lerp(Color(0.95, 0.25, 0.2), 1.0 - f)
		_bar.visible = alive

func _refresh_tag() -> void:
	if _tag == null:
		return
	var p: Dictionary = Net.peers.get(owner_peer, {})
	if is_hero:
		_tag.text = ("◆ %s ◆" % display_name) if alive else ("◆ %s · Fallen ◆" % display_name)
		if _sub:
			var cls := DB.class_def(StringName(p.get("cls", "")))
			_sub.text = "Level %d %s · %s%s" % [level, cls.display_name if cls else "Hero", p.get("device", "PC"), " · Host" if owner_peer == 1 else ""]
	elif guild_tag != "":
		_tag.text = "%s (%s · %s)" % [display_name, guild_tag, p.get("name", "Ally")]
	else:
		_tag.text = "%s (%s's Tempo)" % [display_name, p.get("name", "Ally")]

func _process(delta: float) -> void:
	if _ring:
		_ring.rotation.y += delta * 0.8
		var pulse := 1.0 + sin(Time.get_ticks_msec() * 0.004) * 0.05
		_ring.scale = Vector3(pulse, 0.15, pulse)
		_ring.visible = alive

## A monster (on the host) hit this ally: the real one lives on another machine, so the hit goes there.
func receive_hit(req: DamageRequest, attacker: Node = null, hit_point := Vector3.INF) -> DamageResult:
	var r := DamageResult.new()
	if not alive:
		return r
	Net.forward_ally_hit(self, req, attacker, hit_point)
	return r

func heal(_amount: float, _show := true) -> void:
	pass                                   # the owner's machine heals the real ally

func apply_knockback(_dir: Vector3, _speed: float, _source: DerivedStats, _source_node: Node, _depth := 0, _launch := 0.0) -> void:
	pass

func in_combat() -> bool:
	return _engaged

# ---- Interactable: revive a fallen friend (bh-011) -----------------------------------------------------------------

func can_interact(p: Node) -> bool:
	return is_hero and not alive and p is Player and (p as Player).alive

func interact_text() -> String:
	return "Revive %s" % display_name

func interact_anim() -> StringName:
	return &"interact_teleport"

func interact(_p: Node) -> void:
	Net.revive(self)
