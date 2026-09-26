extends Node
## Loot and experience (autoload `Loot`): reacts to kills, awards XP, rolls drops and spawns them in the world.
##
## Drops per rank (before Magic Find):
##   normal  drop_chance -> 1 item; 10% health / 6% mana potion; family materials
##   elite   2-3 items, one guaranteed Advanced or better; 4% set piece, 1.5% Aether unique; 3x XP
##   boss    5-6 items, one guaranteed Master or better; 40% set piece, 15% Aether unique; boss materials
## Item level = monster level (+1 elite, +2 boss). Rarity uses ItemGenerator.roll_rarity with a rank bonus.

var rng := RandomNumberGenerator.new()

func _ready() -> void:
	rng.randomize()
	Events.actor_died.connect(_on_actor_died)

func _on_actor_died(actor: Node, killer: Node) -> void:
	if not (actor is Enemy):
		return
	var e := actor as Enemy
	var player := Game.player as Player
	if player == null or not is_instance_valid(player) or Game.hero == null:
		return
	award_xp(e, player)
	drop_for(e, player)
	if e.is_boss and e.has_meta(&"boss_flag"):
		Game.set_world_flag(StringName(e.get_meta(&"boss_flag")), true)

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
	var ilvl := e.level + (2 if e.is_boss else (1 if e.is_elite else 0))
	var rank_bonus := 2.0 if e.is_boss else (0.6 if e.is_elite else 0.0)
	var at := e.global_position
	var drops: Array = []
	# Gold
	var g := rng.randi_range(e.def.gold.x, e.def.gold.y)
	g = int(round(float(g) * (1.0 + 0.12 * float(e.level - 1)) * (3.0 if e.is_elite else 1.0) * (1.0 + player.stats.get_stat(&"gold_find")) \
		* (1.0 + (GuildRules.elite_gold_bonus(player.hero) if e.is_elite or e.is_boss else 0.0))))
	if g > 0 and (rng.randf() < 0.75 or e.is_elite or e.is_boss):
		spawn_gold(at, g)
	# Equipment
	var n := 0
	if e.is_boss:
		n = rng.randi_range(5, 6)
	elif e.is_elite:
		n = rng.randi_range(2, 3)
	elif rng.randf() < e.def.drop_chance * 0.6:
		n = 1
	var cls: StringName = player.hero.cls.id
	for i in n:
		var rarity := ItemGenerator.roll_rarity(rng, mf, rank_bonus, ilvl)
		if i == 0 and e.is_boss:
			rarity = maxi(rarity, BH.Rarity.MASTER)
		elif i == 0 and e.is_elite:
			rarity = maxi(rarity, BH.Rarity.ADVANCED)
		var base := ItemGenerator.random_base(rng, ilvl, [], cls if rng.randf() < 0.6 else &"")
		if base:
			drops.append(ItemGenerator.generate(base, ilvl, rarity, _item_rng()))
	# Set pieces and Aether uniques
	var set_p := 0.4 if e.is_boss else (0.04 if e.is_elite else 0.002)
	var uniq_p := 0.15 if e.is_boss else (0.015 if e.is_elite else 0.0005)
	if rng.randf() < set_p * (1.0 + mf):
		var sb := ItemGenerator.random_special(rng, ilvl + 4, true)
		if sb:
			drops.append(ItemGenerator.generate(sb, ilvl, BH.Rarity.MASTER, _item_rng()))
	if rng.randf() < uniq_p * (1.0 + mf):
		var ub := ItemGenerator.random_special(rng, ilvl + 4, false)
		if ub:
			drops.append(ItemGenerator.generate(ub, ilvl, BH.Rarity.AETHER, _item_rng()))
	# Consumables and materials
	if rng.randf() < 0.10:
		drops.append(DB.make_item(&"health_potion", BH.Rarity.COMMON, ilvl, rng.randi()))
	if rng.randf() < 0.06:
		drops.append(DB.make_item(&"mana_potion", BH.Rarity.COMMON, ilvl, rng.randi()))
	for entry in e.def.loot:
		if rng.randf() < float(entry[1]):
			var it := DB.make_item(StringName(entry[0]), BH.Rarity.COMMON, ilvl, rng.randi())
			if it:
				it.count = rng.randi_range(int(entry[2]), int(entry[3]))
				drops.append(it)
	if e.stats and e.stats.has_flag(&"aether_blink"):
		var sh := DB.make_item(&"aether_shard", BH.Rarity.COMMON, ilvl, rng.randi())
		sh.count = rng.randi_range(1, 2)
		drops.append(sh)
	for i in drops.size():
		var ang := TAU * float(i) / maxf(1.0, drops.size()) + rng.randf() * 0.5
		spawn_item(drops[i], at, ang, 1.0 + rng.randf() * (1.8 if e.is_boss else 1.0))

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
		land = CombatQuery.ground_at(FX.world.get_world_3d(), land)
	d.launch(from + Vector3.UP * 0.8, land)
	Events.loot_dropped.emit(item, land)
	return d

func spawn_gold(from: Vector3, amount: int) -> LootDrop:
	if FX.world == null:
		return null
	var d := LootDrop.new()
	d.gold = amount
	FX.world.add_child(d)
	var land := from + Vector3(rng.randf_range(-0.8, 0.8), 0, rng.randf_range(-0.8, 0.8))
	if FX.world.is_inside_tree():
		land = CombatQuery.ground_at(FX.world.get_world_3d(), land)
	d.launch(from + Vector3.UP * 0.8, land)
	return d
