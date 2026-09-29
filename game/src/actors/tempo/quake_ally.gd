class_name QuakeAlly
extends Tempo
## A Quake Team ally in the world (bh-017): a hero of its own that follows the player, stands between them and danger,
## uses its class skills, heals itself with draughts and skills, and shops for itself in town.
##
## It is built on the Tempo fighting AI (follow / engage / retreat / evade, class skills, dodge) but is not a spirit: it
## has a real hero's stats (its own class, level, attributes, gear), a solid body with its class model, and it does the
## errands of a player — walking from stand to stand along the town's trade row to buy the best gear it can afford
## and a Tempo of its own (QuakeBrain).

signal shopped(msgs: Array)

var mate: QuakeMate
var _shop_queue: Array = []
var _shop_pause := 0.0
var _town_t := 2.5
var _potion_cd := 0.0
var _plate_level := 0

const POTION_COOLDOWN := 7.0
const SHOP_LEASH := 26.0          # the mate stops shopping and comes back when the player is this far away

func bind_mate(m: QuakeMate, p_player: Node3D, p_slot := 0) -> QuakeAlly:
	mate = m
	setup(m.tdata, m.hero, p_player, p_slot)
	# the fighting AI reads the class and skills from the TempoData; the look is the hero's own
	tdef = tdef.duplicate()
	tdef["model"] = m.hero.cls.model_path
	tdef["rig"] = m.hero.cls.id
	tdef["color"] = Color(1.0, 0.86, 0.5)
	name = "QuakeAlly_%s" % m.display_name()
	return self

func _ready() -> void:
	super._ready()
	add_to_group(&"quake_ally")
	hero.equipment.changed.connect(_on_gear_changed)
	_update_plate()

## Beside and behind the leader, spread wide so three allies do not stack on each other or on the leader's own Tempos.
func _formation_point() -> Vector3:
	var p := owner_player
	var f: Vector3 = p.global_transform.basis.z.slide(Vector3.UP).normalized()
	if f.length() < 0.1:
		f = Vector3.BACK
	var side := f.cross(Vector3.UP)
	var offs := [Vector2(-2.9, 3.4), Vector2(2.9, 3.4), Vector2(0.0, 5.0)]
	var o: Vector2 = offs[slot_index % offs.size()]
	return p.global_position - f * o.y + side * o.x

## Solid and lit like a hero, not a ghost: a faint warm rim marks a friend.
func _spirit_look() -> void:
	visual.set_rim(Color(1.0, 0.85, 0.5), 0.22)
	visual.set_opacity(1.0)
	_light = OmniLight3D.new()
	_light.light_color = Color(1.0, 0.8, 0.5)
	_light.light_energy = 0.22
	_light.omni_range = 3.0
	_light.position = Vector3(0, 1.4, 0)
	add_child(_light)

func _update_plate() -> void:
	if _plate == null:
		return
	_plate_level = hero.progress.level
	_plate.text = "%s  Lv %d" % [mate.display_name(), _plate_level]
	_plate.modulate = Color(1.0, 0.86, 0.5)

# ---- looks and stats come from the hero -----------------------------------------------------------------------------

func refresh_equipment_visuals() -> void:
	if visual == null or hero == null:
		return
	var eq := hero.equipment
	var lo := eq.loadout()
	visual.detach_weapon(&"main")
	visual.detach_weapon(&"off")
	var main := eq.get_item(&"main_weapon")
	if main != null and lo.main_type != null:
		visual.attach_weapon(&"main", Player.weapon_model_for(main, lo.main_type), lo.main_type.grip_offset)
	var sub := eq.get_item(&"sub_weapon")
	if sub != null and sub.base.category == &"shield":
		visual.attach_weapon(&"off", sub.base.model_path())
	elif sub != null and lo.off_type != null:
		visual.attach_weapon(&"off", Player.weapon_model_for(sub, lo.off_type), lo.off_type.grip_offset)
	visual.set_stance(_stance_idle())
	visual.set_opacity(1.0)

func _stance_idle() -> StringName:
	var lo := stats.loadout if stats else hero.equipment.loadout()
	if lo.dual_wield:
		return &"idle_dual"
	if lo.has_shield:
		return &"idle_shield"
	return lo.main_type.idle_anim if lo.main_type else &"idle_1h"

func _level() -> int:
	return hero.progress.level

func rebuild_stats() -> void:
	var mods := status.stat_modifiers()
	mods.append_array(DataTempos.mods_from(data.trait_def().get("mods", []), data.trait_def().get("name", "Trait")))
	if _smoke_t > 0.0:
		mods.append(StatModifier.inc(&"evasion", 1.0, "Smoke"))
	stats = hero.compute_stats(mods)
	level = hero.progress.level
	if _plate and _plate_level != level:
		_update_plate()

func _on_gear_changed() -> void:
	mark_stats_dirty()
	refresh_equipment_visuals()

# ---- draughts -------------------------------------------------------------------------------------------------------

func _physics_process(delta: float) -> void:
	if Net.is_active():
		queue_free()      # no Quake Team in multiplayer
		return
	super._physics_process(delta)
	if not alive or mate == null:
		return
	_potion_cd = maxf(0.0, _potion_cd - delta)
	if _potion_cd <= 0.0:
		_drink()

func _drink() -> void:
	var f := hp_frac()
	if f < 0.4 and _drink_kind(QuakeBrain.HEAL_IDS, &"heal"):
		return
	if mana < max_mana() * 0.22 and max_mana() > 20.0 and _drink_kind(QuakeBrain.MANA_IDS, &"mana"):
		return

## Drink the strongest draught of a kind the mate carries. True when one was drunk.
func _drink_kind(ids: Array, key: StringName) -> bool:
	for i in range(ids.size() - 1, -1, -1):
		var id: StringName = ids[i]
		if hero.inventory.count_of(id) <= 0:
			continue
		var b := DB.item_base(id)
		if b == null:
			continue
		hero.inventory.consume(id, 1)
		var fx := b.consumable_effect
		var potion := 1.0 + stats.get_stat(&"potion_power")
		if key == &"heal":
			var mult := (1.0 + stats.get_stat(&"healing")) * potion
			status.apply(&"regen", 2.0, max_hp() * float(fx.get("heal", 0.3)) * mult / 2.0)
		else:
			restore_mana(max_mana() * float(fx.get("mana", 0.3)) * potion)
		_potion_cd = POTION_COOLDOWN
		Audio.play_at(&"potion_drink", global_position)
		FX.text_popup(center() + Vector3.UP * 1.0, "%s" % b.display_name, Color(0.95, 0.4, 0.4) if key == &"heal" else Color(0.45, 0.6, 1.0), 0.8)
		return true
	return false

# ---- shopping in town -----------------------------------------------------------------------------------------------

func _in_town() -> bool:
	return not DataTownRows.row(Game.current_map_id).is_empty() and not Game.travelling

func _think() -> void:
	var p := owner_player
	if p != null and is_instance_valid(p) and alive and _in_town():
		if _shop_step():
			return
	elif not _shop_queue.is_empty():
		_shop_queue.clear()
	super._think()

## One step of the errand. True when the mate is busy with it (the fighting AI should not move it this tick).
func _shop_step() -> bool:
	var dp := _flat(owner_player.global_position)
	if not _shop_queue.is_empty() and dp > SHOP_LEASH:
		_shop_queue.clear()
		return false
	if _shop_pause > 0.0:
		_shop_pause -= THINK
		_move_goal = Vector3.INF
		mode = Mode.FOLLOW
		return true
	if _shop_queue.is_empty():
		_town_t -= THINK
		if _town_t <= 0.0:
			_town_t = 4.0
			_plan_shopping()
		return false
	if _nearest_enemy_dist() < 12.0:
		_shop_queue.clear()
		return false
	var step: Dictionary = _shop_queue[0]
	var spot: Vector3 = step.spot
	if _flat(spot) > 1.5:
		_move_goal = spot
		mode = Mode.FOLLOW
		return true
	_shop_queue.pop_front()
	_face_now(step.stand.pos)
	var before := hero.tempos.size()
	var res := QuakeBrain.visit_stand(mate, step.stand)
	if not (res.msgs as Array).is_empty():
		for m in res.msgs:
			Events.notify.emit(String(m), &"info")
		shopped.emit(res.msgs)
	if hero.tempos.size() > before:
		TempoParty.spawn_for(get_parent(), self, hero)
	if _shop_queue.is_empty():
		QuakeBrain.trip_done(mate, Game.current_map_id)
	_shop_pause = 0.9
	return true

func _plan_shopping() -> void:
	var map_id := Game.current_map_id
	if not QuakeBrain.wants_trip(mate, map_id) or hero.inventory.gold < 30:
		return
	var stands := []
	for s in DataTownRows.row(map_id).stands:
		if s.kind == DataTownRows.SHOP or (s.kind == DataTownRows.SHRINE and hero.tempos.size() < QuakeMate.MAX_TEMPOS):
			stands.append(s)
	var from := global_position
	_shop_queue.clear()
	while not stands.is_empty():
		var best := 0
		var bd := INF
		for i in stands.size():
			var sp: Vector3 = DataTownRows.customer_spot(stands[i])
			var d := Vector2(sp.x - from.x, sp.z - from.z).length()
			if d < bd:
				bd = d
				best = i
		var s: Dictionary = stands[best]
		stands.remove_at(best)
		var spot := DataTownRows.customer_spot(s)
		spot = CombatQuery.ground_at(get_world_3d(), spot + Vector3.UP * 3.0)
		_shop_queue.append({"stand": s, "spot": spot})
		from = spot
	if _shop_queue.is_empty():
		QuakeBrain.trip_done(mate, map_id)

# ---- falling -------------------------------------------------------------------------------------------------------

func _fall_notice() -> void:
	Events.notify.emit("%s was knocked out - back on their feet in a moment." % mate.display_name(), &"error")
	QuakeTeam.on_ally_fell(self)

## Rejoin the player at once (a Quake Team ally never gets left behind).
func heal_full() -> void:
	if alive:
		heal(max_hp() - hp, false)
		restore_mana(max_mana())
