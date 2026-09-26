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

# ---- The Salted Marlin (inn) and Seris's paid mending ----------------------------------------------------------

const REST_DURATION := 900.0          # seconds of play time the Well Rested bonus lasts

## Price of a night at the inn: grows gently with level; the Lantern Covenant pays less.
static func rest_cost(hero: HeroData) -> int:
	var base := 10 + 5 * maxi(1, hero.progress.level)
	return maxi(1, int(round(float(base) * (1.0 - GuildRules.inn_discount(hero)))))

static func can_rest(hero: HeroData) -> String:
	var fee := rest_cost(hero)
	if hero.inventory.gold < fee:
		return "Not enough gold (%d needed)" % fee
	return ""

## Pay exactly the quoted fee, restore HP/mana, cleanse, grant Well Rested. Returns "" or an error (nothing changes).
static func rest(hero: HeroData, p: Node) -> String:
	var err := can_rest(hero)
	if err != "":
		return err
	var fee := rest_cost(hero)
	hero.inventory.gold -= fee
	hero.inventory.changed.emit()
	hero.rested_until = hero.play_time + REST_DURATION
	hero.stats_dirty.emit()
	if p is Player and (p as Player).alive:
		heal(p)
	Events.rested.emit(fee)
	Events.notify.emit("You wake Well Rested (+%d%% experience)." % roundi(HeroData.RESTED_XP * 100.0), &"info")
	return ""

## Seris mends on the spot: twice the inn's price, no rest bonus.
static func mystic_heal_cost(hero: HeroData) -> int:
	return (10 + 5 * maxi(1, hero.progress.level)) * 2

static func mystic_heal(hero: HeroData, p: Node) -> String:
	var fee := mystic_heal_cost(hero)
	if hero.inventory.gold < fee:
		return "Not enough gold (%d needed)" % fee
	hero.inventory.gold -= fee
	hero.inventory.changed.emit()
	heal(p)
	return ""
