class_name NpcServices
## Services townspeople perform: healing and unweaving (respec) skills and talents.

## Gold cost of a full respec at a level. Cheap early (experimenting is encouraged), meaningful later.
static func respec_cost(level: int) -> int:
	return int(snappedf(40.0 * pow(float(maxi(1, level)), 1.35), 10.0))

## Everything that would be refunded: {"skill_points": n, "talent_points": n}.
static func respec_preview(hero: HeroData) -> Dictionary:
	var starting := 0
	for s in hero.cls.starting_skills:
		starting += 1 if hero.skill_tree.rank(s) > 0 else 0
	return {"skill_points": maxi(0, hero.skill_tree.points_spent() - starting), "talent_points": hero.talent_tree.points_spent()}

## Refund every skill and talent point (starting skills stay learned). Returns "" or an error.
static func respec(hero: HeroData, pay := true) -> String:
	var pv := respec_preview(hero)
	if pv.skill_points == 0 and pv.talent_points == 0:
		return "Nothing to unweave"
	var cost := respec_cost(hero.progress.level) if pay else 0
	if hero.inventory.gold < cost:
		return "Not enough gold (%d needed)" % cost
	hero.inventory.gold -= cost
	hero.inventory.changed.emit()
	hero.skill_tree.reset()
	for s in hero.cls.starting_skills:
		hero.skill_tree.ranks[s] = 1
	for i in hero.skill_bar.size():
		if hero.skill_bar[i] != &"" and hero.skill_rank(hero.skill_bar[i]) <= 0:
			hero.skill_bar[i] = &""
	hero.talent_tree.reset()
	hero.progress.skill_points += int(pv.skill_points)
	hero.progress.talent_points += int(pv.talent_points)
	hero.skill_tree.changed.emit()
	hero.progress.points_changed.emit()
	hero.skills_changed.emit()
	return ""

## Full heal of a player node (and cleansing of harmful statuses).
static func heal(p: Node) -> void:
	var pl := p as Player
	if pl == null or not pl.alive:
		return
	pl.hp = pl.max_hp()
	pl.mana = pl.max_mana()
	pl.status.cleanse_harmful()
	pl.health_changed.emit(pl.hp, pl.max_hp())
	pl.mana_changed.emit(pl.mana, pl.max_mana())
	FX.spawn(VFXLib.ring_wave(Color(0.6, 0.98, 1.0, 0.9), 2.5, 0.6, 0.7), pl.global_position)
	Audio.play_ui(&"level_up")
	Events.notify.emit("Fully restored", &"info")
