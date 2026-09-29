extends Node
const BossSets = preload("res://src/data/data_boss_sets.gd")
## Loot and experience (autoload `Loot`): reacts to kills, awards XP, rolls drops and spawns them in the world.
##
## Drops per rank (before Magic Find):
##   normal  drop_chance -> 1 item; 10% health / 6% mana potion; family materials
##   elite   2-3 items, one guaranteed Advanced or better; 4% set piece, 1.5% Aether unique; 3x XP
##   boss    5-6 class items, all Master or better; 40% set piece, 15% Aether unique; boss materials
## Item level = monster level (+1 elite, +2 boss). Rarity uses ItemGenerator.roll_rarity with a rank bonus.

var rng := RandomNumberGenerator.new()

func _ready() -> void:
	rng.randomize()
	Events.actor_died.connect(_on_actor_died)
	Events.stage_cleared.connect(_on_stage_cleared)

## Every camp of a combat map cleared in one visit (Spawner): a purse and some experience, scaled to the map.
func _on_stage_cleared(map_id: StringName) -> void:
	var player := Game.player as Player
	var def := DB.map_def(map_id)
	if player == null or not is_instance_valid(player) or def == null or Game.hero == null:
		return
	var lvl := def.level_max
	var xp := maxi(1, int(round(XpCurve.monster_xp(lvl, 8.0) * XpCurve.level_diff_mult(Game.hero.progress.level, lvl))))
	Game.hero.progress.add_xp(xp)
	Events.xp_gained.emit(xp)
	var gold := 25 + 15 * lvl
	spawn_gold(player.global_position + Vector3(0, 0, 1.2), gold)
	Events.notify.emit("Stage cleared: +%d XP, a purse of %d gold." % [xp, gold], &"loot")

func _on_actor_died(actor: Node, killer: Node) -> void:
	if not (actor is Enemy):
		return
	var e := actor as Enemy
	var player := Game.player as Player
	if player == null or not is_instance_valid(player) or Game.hero == null:
		return
	award_xp(e, player)
	GuildJobs.on_kill(Game.hero, e.is_elite or e.is_boss, String(Game.current_map_id))
	drop_for(e, player)
	# Life / Mana on Kill gear (bh-012)
	if player.alive:
		var hk := player.stats.get_stat(&"hp_on_kill")
		var mk := player.stats.get_stat(&"mana_on_kill")
		if hk > 0.0:
			player.heal(hk, false)
		if mk > 0.0:
			player.restore_mana(mk)
	if e.is_boss and e.has_meta(&"boss_flag"):
		Game.set_world_flag(StringName(e.get_meta(&"boss_flag")), true)
	if e.is_miniboss():
		miniboss_down(e, player.hero)

## A miniboss fell: remember when (it returns after DataMinibosses.RESPAWN), count the clear, tell the HUD.
func miniboss_down(e: Enemy, hero: HeroData) -> void:
	var id := StringName(e.miniboss.id)
	var rec: Dictionary = hero.miniboss_log.get(id, {"kills": 0, "at": 0.0})
	hero.miniboss_log[id] = {"kills": int(rec.kills) + 1, "at": hero.play_time}
	hero.add_clear()
	Events.miniboss_defeated.emit(id)

func xp_for(e: Enemy, player: Player) -> int:
	var rank := 3.0 if e.is_elite else 1.0
	var base := XpCurve.monster_xp(e.level, e.def.xp_mult * rank)
	var mult := XpCurve.level_diff_mult(player.hero.progress.level, e.level) * (1.0 + player.stats.get_stat(&"xp_gain"))
	return maxi(1, int(round(base * mult)))

func award_xp(e: Enemy, player: Player) -> void:
	var xp := xp_for(e, player)
	player.hero.progress.add_xp(xp)
	Events.xp_gained.emit(xp)
	FX.text_popup(e.center() + Vector3.UP * 1.2, "+%d XP" % xp, Color(0.75, 0.6, 1.0), 0.8)

func drop_for(e: Enemy, player: Player) -> void:
	var mf := player.stats.get_stat(&"magic_find")
	var ilvl := e.level + (2 if e.is_boss or e.is_miniboss() else (1 if e.is_elite else 0))
	var at := e.global_position
	var drops: Array = []
	# Gold
	var g := rng.randi_range(e.def.gold.x, e.def.gold.y)
	g = int(round(float(g) * (1.0 + 0.12 * float(e.level - 1)) * (3.0 if e.is_elite else 1.0) * (4.0 if e.is_miniboss() else 1.0) * (1.0 + player.stats.get_stat(&"gold_find")) \
		* (1.0 + (GuildRules.elite_gold_bonus(player.hero) if e.is_elite or e.is_boss else 0.0))))
	if g > 0 and (rng.randf() < 0.75 or e.is_elite or e.is_boss):
		spawn_gold(at, g)
	drops.append_array(equipment_for(e, player))
	# Consumables and materials
	if rng.randf() < 0.10:
		drops.append(DB.make_item(&"health_potion", BH.Rarity.COMMON, ilvl, rng.randi()))
	if rng.randf() < 0.06:
		drops.append(DB.make_item(&"mana_potion", BH.Rarity.COMMON, ilvl, rng.randi()))
	# bh-006 consumables (tonics, wards, bombs, scrolls ...): one roll, more for elites and bosses
	var cons_p := 0.55 if e.is_boss else (0.3 if e.is_elite else 0.07)
	for i in (2 if e.is_boss else 1):
		if rng.randf() < cons_p:
			var cb := ItemGenerator.random_consumable(rng, ilvl)
			if cb:
				drops.append(DB.make_item(cb.id, BH.Rarity.COMMON, ilvl, rng.randi()))
	for entry in e.def.loot:
		if rng.randf() < float(entry[1]):
			var it := DB.make_item(StringName(entry[0]), BH.Rarity.COMMON, ilvl, rng.randi())
			if it:
				it.count = rng.randi_range(int(entry[2]), int(entry[3]))
				drops.append(it)
	if e.is_miniboss():
		# the champion's essence (Elite and Master crafting) and, sometimes, a recipe scroll
		var ce := DB.make_item(&"champion_essence", BH.Rarity.COMMON, ilvl, rng.randi())
		ce.count = rng.randi_range(1, 2)
		drops.append(ce)
		if rng.randf() < DataMinibosses.RECIPE_CHANCE:
			var pool := DataMinibosses.scroll_pool()
			if not pool.is_empty():
				drops.append(DB.make_item(pool[rng.randi_range(0, pool.size() - 1)], BH.Rarity.COMMON, ilvl, rng.randi()))
	# bh-018: socket crystals — every boss drops one (any grade), every miniboss a Fragment or a Shard
	if e.is_boss or e.is_miniboss():
		var cid := DataCrystals.roll_drop(rng, e.level, e.is_boss)
		var cr := DB.make_item(cid, BH.Rarity.COMMON, ilvl, rng.randi())
		if cr:
			drops.append(cr)
	if e.stats and e.stats.has_flag(&"aether_blink"):
		var sh := DB.make_item(&"aether_shard", BH.Rarity.COMMON, ilvl, rng.randi())
		sh.count = rng.randi_range(1, 2)
		drops.append(sh)
	for i in drops.size():
		var ang := TAU * float(i) / maxf(1.0, drops.size()) + rng.randf() * 0.5
		spawn_item(drops[i], at, ang, 1.0 + rng.randf() * (1.8 if e.is_boss or e.is_miniboss() else 1.0))

## Equipment rolls are separate from world spawning so every rank/class combination can be verified.
## Bosses: every piece Master+, minibosses: every piece Elite+, always class gear, including a weapon.
## Normal attribute, level and earned-rank equip requirements still apply.
func equipment_for(e: Enemy, player: Player) -> Array:
	var mf := player.stats.get_stat(&"magic_find")
	var ilvl := e.level + (2 if e.is_boss or e.is_miniboss() else (1 if e.is_elite else 0))
	var rank_bonus := 2.0 if e.is_boss else (1.2 if e.is_miniboss() else (0.6 if e.is_elite else 0.0))
	var reward := float(e.get_meta(&"dungeon_reward_bonus", 0.0))
	rank_bonus += reward
	var drops: Array = []
	var n := 0
	if e.is_boss:
		n = rng.randi_range(5, 6)
	elif e.is_miniboss():
		n = rng.randi_range(3, 4)
	elif e.is_elite:
		n = rng.randi_range(2, 3)
	elif rng.randf() < e.def.drop_chance * 0.6:
		n = 1
	var cls: StringName = player.hero.cls.id
	var guaranteed := e.is_boss or e.is_miniboss()
	var fit := 1.0
	var used_bases := []
	for i in n:
		var rarity := ItemGenerator.roll_rarity(rng, mf, rank_bonus, ilvl)
		if e.is_boss:
			rarity = maxi(rarity, BH.Rarity.MASTER)
		elif e.is_miniboss():
			rarity = maxi(rarity, BH.Rarity.ELITE)
		elif i == 0 and e.is_elite:
			rarity = maxi(rarity, BH.Rarity.ADVANCED)
		var base := ItemGenerator.random_base(rng, ilvl, [&"weapon"] if guaranteed and i == 0 else [], cls, fit, used_bases)
		if base:
			used_bases.append(base.id)
			drops.append(ItemGenerator.generate(base, ilvl, rarity, _item_rng()))
	# Set pieces and Aether uniques
	var set_p := 0.4 if e.is_boss else (0.04 if e.is_elite else 0.002)
	var uniq_p := 0.15 if e.is_boss else (0.015 if e.is_elite else 0.0005)
	if BossSets.eligible(e):
		var stored: Array = HeroVault.shared().cells if player.hero == Game.hero else []
		drops.append(BossSets.roll(e, player.hero, rng, stored))
	elif rng.randf() < set_p * (1.0 + mf):
		var sb := ItemGenerator.random_special(rng, ilvl, true, cls, fit)
		if sb:
			drops.append(ItemGenerator.generate(sb, ilvl, BH.Rarity.MASTER, _item_rng()))
	if e.has_meta(&"depth_guardian"):
		uniq_p = 0.35 if e.level < 50 else 0.65
	if rng.randf() < uniq_p * (1.0 + mf):
		var ub := DataDepthEquipment.special(rng, ilvl, cls) if e.has_meta(&"depth_guardian") else ItemGenerator.random_special(rng, ilvl, false, cls, fit)
		if ub:
			drops.append(ItemGenerator.generate(ub, ilvl, BH.Rarity.AETHER, _item_rng()))
	return drops

## Soul Embers a kill drops (0 = none): rare on the surface, common in the dungeons, generous from champions.
func ember_roll(e: Enemy, in_dungeon: bool, find := 0.0) -> int:
	var n := 0
	if e.is_boss:
		n = rng.randi_range(30, 45) if in_dungeon else rng.randi_range(20, 30)
	elif e.is_miniboss():
		n = rng.randi_range(10, 18) if in_dungeon else rng.randi_range(6, 10)
	elif e.is_elite:
		n = rng.randi_range(3, 6) if in_dungeon else (rng.randi_range(1, 3) if rng.randf() < 0.5 else 0)
	elif rng.randf() < (0.22 if in_dungeon else 0.04) * e.def.xp_mult:
		n = rng.randi_range(1, 2)
	return int(round(float(n) * (1.0 + maxf(0.0, find))))

## The Relic Cache tier a kill drops (-1 = none).
func cache_roll(e: Enemy, in_dungeon: bool) -> int:
	if e.is_boss:
		return 2 if (in_dungeon and rng.randf() < 0.35) else 1
	if e.is_miniboss():
		return 1 if rng.randf() < (0.2 if in_dungeon else 0.08) else (0 if in_dungeon or rng.randf() < 0.4 else -1)
	if e.is_elite and rng.randf() < (0.04 if in_dungeon else 0.01):
		return 0
	return -1

## A dungeon chest opened (TreasureChest): gold, gear (one piece guaranteed Advanced / Elite / Master by tier), Soul
## Embers, a draught or two and sometimes a Relic Cache.
func drop_chest(tier: int, level: int, at: Vector3, hero: HeroData) -> Array:
	var player := Game.player as Player
	var mf := player.stats.get_stat(&"magic_find") if player else 0.0
	var ef := player.stats.get_stat(&"ember_find") if player else 0.0
	var gf := player.stats.get_stat(&"gold_find") if player else 0.0
	var ilvl := level + tier
	var drops: Array = []
	var n: int = [rng.randi_range(1, 2), rng.randi_range(2, 3), 4][clampi(tier, 0, 2)]
	var floor_r: int = [BH.Rarity.ADVANCED, BH.Rarity.ELITE, BH.Rarity.MASTER][clampi(tier, 0, 2)]
	var cls: StringName = hero.cls.id if hero and hero.cls else &""
	var used_bases := []
	for i in n:
		var rarity := ItemGenerator.roll_rarity(rng, mf, 0.4 + 0.6 * tier, ilvl)
		if i == 0:
			rarity = maxi(rarity, floor_r)
		if i == 1 and tier == 2 and rng.randf() < 0.5:
			rarity = maxi(rarity, BH.Rarity.MYTHICAL)
		var base := ItemGenerator.random_base(rng, ilvl, [], cls, 1.0, used_bases)
		if base:
			used_bases.append(base.id)
			drops.append(ItemGenerator.generate(base, ilvl, rarity, _item_rng()))
	var em := DB.make_item(&"soul_ember", BH.Rarity.COMMON, ilvl, rng.randi())
	em.count = int(round(float([rng.randi_range(3, 6), rng.randi_range(8, 15), rng.randi_range(25, 40)][clampi(tier, 0, 2)]) * (1.0 + ef)))
	drops.append(em)
	for i in tier + 1:
		var cb := ItemGenerator.random_consumable(rng, ilvl)
		if cb and rng.randf() < 0.6:
			drops.append(DB.make_item(cb.id, BH.Rarity.COMMON, ilvl, rng.randi()))
	var cache := -1
	match tier:
		0: cache = 0 if rng.randf() < 0.08 else -1
		1: cache = 1 if rng.randf() < 0.08 else (0 if rng.randf() < 0.35 else -1)
		_: cache = 2 if rng.randf() < 0.3 else 1
	if cache >= 0:
		drops.append(DB.make_item(DataRelics.CACHES[cache].id, BH.Rarity.COMMON, ilvl, rng.randi()))
	spawn_gold(at, int(round(float(20 + 8 * level) * [1.0, 2.2, 5.0][clampi(tier, 0, 2)] * rng.randf_range(0.8, 1.25) * (1.0 + gf))))
	for i in drops.size():
		spawn_item(drops[i], at, TAU * float(i) / maxf(1.0, drops.size()) + rng.randf() * 0.4, 1.0 + rng.randf() * 0.8)
	return drops

func _item_rng() -> RandomNumberGenerator:
	var r := RandomNumberGenerator.new()
	r.seed = rng.randi()
	return r

func spawn_item(item: ItemInstance, from: Vector3, angle := 0.0, dist := 1.2) -> LootDrop:
	if FX.world == null or item == null:
		return null
	var d := LootDrop.new()
	d.item = item
	FX.world.add_child(d)
	var land := from + Vector3(cos(angle), 0, sin(angle)) * dist
	if FX.world.is_inside_tree():
		land = landing_point(FX.world.get_world_3d(), from, angle, dist)
	d.launch(from + Vector3.UP * 0.8, land)
	Events.loot_dropped.emit(item, land)
	return d

func spawn_gold(from: Vector3, amount: int) -> LootDrop:
	if FX.world == null:
		return null
	var d := LootDrop.new()
	d.gold = amount
	FX.world.add_child(d)
	var off := Vector2(rng.randf_range(-0.8, 0.8), rng.randf_range(-0.8, 0.8))
	var land := from + Vector3(off.x, 0, off.y)
	if FX.world.is_inside_tree():
		land = landing_point(FX.world.get_world_3d(), from, off.angle(), off.length())
	d.launch(from + Vector3.UP * 0.8, land)
	return d

## Where a drop thrown from a corpse (feet at `from`) toward `angle` comes to rest: on walkable ground at about the
## corpse's height, never on top of a wall, tree, rock or roof and never inside or behind one. (The old landing ray
## started 6 m above the spot and returned the first surface it met, so drops near trees and walls landed on canopies
## and wall tops, out of reach of the R key — the "cannot pick it up" bug.)
static func landing_point(world: World3D, from: Vector3, angle: float, dist: float) -> Vector3:
	var space := world.direct_space_state
	var waist := from + Vector3.UP * 0.7
	var tries := [[angle, dist], [angle + 1.3, dist], [angle - 1.3, dist], [angle + 2.6, dist * 0.6], [angle, dist * 0.35]]
	for t in tries:
		var dir := Vector3(cos(float(t[0])), 0.0, sin(float(t[0])))
		var d := float(t[1])
		# keep clear of walls / trees / props between the corpse and the landing spot
		var q := PhysicsRayQueryParameters3D.create(waist, waist + dir * (d + 0.4), BH.LAYER_WORLD | BH.LAYER_PROPS)
		var hit := space.intersect_ray(q)
		if not hit.is_empty():
			d = minf(d, (hit.position - waist).length() - 0.45)
			if d < 0.25:
				continue
		var g = floor_under(space, waist + dir * d, from.y)
		if g != null:
			return g
	var g0 = floor_under(space, waist, from.y)
	return g0 if g0 != null else from

## The walkable surface under `p` near height `ref_y` (from 1 m above down to 4 m below), or null. Steep hits (wall
## faces) are rejected.
static func floor_under(space: PhysicsDirectSpaceState3D, p: Vector3, ref_y: float) -> Variant:
	var q := PhysicsRayQueryParameters3D.create(Vector3(p.x, ref_y + 1.0, p.z), Vector3(p.x, ref_y - 4.0, p.z), BH.LAYER_WORLD | BH.LAYER_GROUND)
	var hit := space.intersect_ray(q)
	if hit.is_empty() or (hit.normal as Vector3).y < 0.6:
		return null
	return hit.position
