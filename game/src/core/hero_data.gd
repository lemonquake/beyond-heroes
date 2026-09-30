class_name HeroData
extends RefCounted
## Complete persistent state of a hero (everything the save file stores except settings).
## Pure model: no nodes. Emits `stats_dirty` when anything affecting derived stats changes.

signal stats_dirty
signal inventory_changed
signal skills_changed

const SKILL_BAR_SIZE := 6
const START_TOWN_PORTALS := 5 # free Town Portal Scrolls in a new hero's bag

var cls: ClassDef
var hero_name := "Hero"
## bh-023: the hero's customised look (HeroLook; only what differs from the plain hero). Empty = the plain hero, which
## is what every save from before the creator loads as. Optional in a save.
var look := {}
var progress := HeroProgress.new()
var equipment := Equipment.new()
var inventory := Inventory.new()
var skill_tree: TreeState
var talent_tree: TreeState
var skill_bar: Array = []                 # skill ids (StringName) or &""
var discovered_maps := {}                 # map id -> true
var unlocked_teleporters := {}            # teleporter id -> true (discovered: a locked dais is recorded too)
## Waypoint network shrines the hero has awakened (stood on while unlocked): only these are travel destinations.
var awakened_shrines := {}                # teleporter id -> true
## Non-public places found by walking near them (DataIsland.PLACES with public = false): place id -> true.
var known_places := {}
## The tracked route (directions HUD): {"dest": place id, "mode": RoutePlanner.Mode} or empty.
var route := {}
var world_flags := {}                     # e.g. &"boss_warden_defeated"
var current_map: StringName = &"sanctuary"
var current_spawn: StringName = &"start"
var play_time := 0.0
## The potion belt (bh-011): what the two belt keys (Q / E, the HP / Mana orbs on a phone) drink. Each slot is
## BELT_AUTO_HEAL / BELT_AUTO_MANA (the strongest draught of that kind the bag holds) or any consumable's base id.
const BELT_AUTO_HEAL := &"auto_heal"
const BELT_AUTO_MANA := &"auto_mana"
const BELT_SIZE := 2
var potion_belt: Array[StringName] = [BELT_AUTO_HEAL, BELT_AUTO_MANA]
var difficulty := 1
## Per-NPC memory: npc id -> {"visited": {node_id: true}, "rel": int}. Relationship is reputation-ready (-100..100).
var dialogue := {}
## Free-form NPC state (met, gifts given, services used ...): npc id -> Dictionary.
var npc_state := {}
## Merchant state that must survive saving (stock, refresh clock, sold specials): shop id -> Shop.to_dict().
var shops := {}
## Guild membership and hero tier (docs/LORE.md §5). tier: 0 Unranked, 1..8 = E..SSS (DataGuilds.TIERS).
var guild: StringName = &""
var tier := 0
var tier_cheat_level := -1 # Hold a manually chosen rank until the next level, including across saves.
## "Well Rested" from the inn: active while play_time < rested_until (seconds of play time).
var rested_until := 0.0
## Tempos (spirit companions, LORE §9): the bound spirits (at most DataTempos.MAX_ACTIVE, fallen ones included), the
## spirits currently answering the Tempo-Caller ({offers: [TempoData dicts], refresh_at, serial}) and the uid counter.
var tempos: Array = []
var tempo_roster := {}
var tempo_serial := 0
## Open Town Portal (TownPortal): {"map": map id, "pos": [x, y, z], "yaw": float} or empty. Cleared on death / dispel.
var town_portal := {}
## Crafting (bh-007): recipes learned from scrolls (recipe id -> true; recipes marked `known` need no entry) and how
## many things this hero has made.
var known_recipes := {}
var crafted_count := 0
## Stages and minibosses (bh-007). clear_count: every stage cleared and every miniboss defeated (Olivar's merchants
## restock whenever it moves). stages_cleared: map id -> times. miniboss_log: miniboss id -> {"kills", "at" (play time)}.
var clear_count := 0
var stages_cleared := {}
var miniboss_log := {}
## The last camp checkpoint rested at (Wyman Outpost's bonfire): {"map", "spawn", "name"} or empty.
var checkpoint := {}
## Herb patches picked: "map/node" -> play time they were picked (they regrow after GatherNode.REGROW seconds).
var gather_log := {}
## Dungeon chests opened (bh-012): "map/n" -> play time; a chest refills DataDungeons.CHEST_RESPAWN seconds later.
var chest_log := {}
## Dungeon raids (bh-013): dungeon id -> {at, until (unix seconds), count}; DataDungeons.record_raid / recovering.
var dungeon_raids := {}
## Tempo summoning (bh-012, TempoGacha): calls made, calls since the last 4-star / 5-star (pity), the welcome gift,
## and the last summons for the history list.
var summon := {}
## Spirits called at the shrine but not bound: they wait in the Spirit Hall (TempoData), swapped in for free.
var spirit_hall: Array = []
## Guild House miniquests (bh-016): GuildJobs.state / to_dict / from_dict.
var guild_jobs := {}
## bh-017: what the hero calls their guild ("" = the guild's own name) and the banner they uploaded (a JPEG, "" = the
## guild's own banner). Both are optional in a save, so older saves load unchanged.
var guild_alias := ""
## bh-017: the AI allies the `quake team` cheat called (QuakeMate), at most QuakeTeam.MAX; optional in a save.
var quake_team: Array = []
var guild_banner := PackedByteArray()
var starter_name := ""                   # bh-015: the first Tempo's rolled name (the guide quotes it)
## The Knight's active aura (bh-010): a learned aura skill id, or &"" (auras are toggled; one at a time).
var active_aura: StringName = &""
var _loading_equipment := false
var _checking_promotions := false

const RESTED_XP := 0.10
const RESTED_REGEN := 0.5

func setup(p_cls: ClassDef, p_name: String) -> void:
	equipment.tier_rank = tier
	equipment.wearer = p_cls.id if p_cls else &""
	cls = p_cls
	hero_name = p_name
	progress.setup(cls)
	skill_tree = TreeState.new(DB.tree(cls.skill_tree_id))
	talent_tree = TreeState.new(DB.tree(cls.talent_tree_id))
	skill_bar.resize(SKILL_BAR_SIZE)
	skill_bar.fill(&"")
	_connect()

# Bound methods (not lambdas) so the RefCounted children never hold a strong reference back to this object.
func _connect() -> void:
	progress.points_changed.connect(_dirty)
	progress.leveled_up.connect(_on_level)
	equipment.changed.connect(_dirty)
	inventory.changed.connect(_inv_changed)
	skill_tree.changed.connect(_skills_changed)
	talent_tree.changed.connect(_dirty)

func _dirty() -> void:
	stats_dirty.emit()

func _on_level(_l: int, _g: int) -> void:
	check_promotions()
	stats_dirty.emit()
	if not quake_team.is_empty():
		QuakeTeam.sync_owner(self)

func _inv_changed() -> void:
	if not _loading_equipment:
		recover_unequipped_gear()
	inventory_changed.emit()
	check_promotions()

func check_promotions() -> void:
	if _loading_equipment or _checking_promotions or tier_cheat_level == progress.level:
		return
	_checking_promotions = true
	GuildRules.auto_promote(self)
	_checking_promotions = false

## Legacy incompatible off-hand gear returns as space opens, without discarding items from a full bag.
func recover_unequipped_gear() -> void:
	var sources: Array = [equipment]
	for t in tempos + spirit_hall:
		sources.append(t.equipment)
	# Place directly: emitting Inventory.changed inside this signal handler would recurse.
	for source: Equipment in sources:
		while not source.recovered_items.is_empty():
			var item: ItemInstance = source.recovered_items[0]
			var index := inventory.first_free(item)
			if index < 0:
				return
			inventory.cells[index] = source.recovered_items.pop_front()

func _skills_changed() -> void:
	skills_changed.emit()
	stats_dirty.emit()

## New character: starting skills, starting gear, a couple of potions.
func init_new() -> void:
	var i := 0
	for s in cls.starting_skills:
		skill_tree.ranks[s] = 1
		skill_bar[i] = s
		i += 1
	for base_id in cls.starting_items:
		var it := DB.make_item(base_id, BH.Rarity.BEGINNER, 1, hash(String(base_id)))
		var slot := equipment.auto_slot(it)
		var res := equipment.equip(it, slot, progress.level, progress.base_attributes())
		if not res.ok:
			inventory.add(it)
	var hp := DB.make_item(&"health_potion", BH.Rarity.COMMON, 1, 1)
	hp.count = 4
	inventory.add(hp)
	var mp := DB.make_item(&"mana_potion", BH.Rarity.COMMON, 1, 2)
	mp.count = 3
	inventory.add(mp)
	var tp := DB.make_item(&"town_portal", BH.Rarity.COMMON, 1, 3)
	tp.count = START_TOWN_PORTALS
	inventory.add(tp)
	discovered_maps[&"sanctuary"] = true
	awakened_shrines[&"sanctuary_waypoint"] = true

## All persistent stat modifiers: equipment + talents + guild/tier + the inn's rest bonus.
func persistent_modifiers() -> Array:
	var mods := equipment.modifiers()
	mods.append_array(talent_tree.modifiers())
	mods.append_array(skill_tree.passive_modifiers(item_skill_levels(mods)))
	mods.append_array(GuildRules.modifiers(self))
	if is_rested():
		mods.append(StatModifier.inc(&"xp_gain", RESTED_XP, "Well Rested"))
		mods.append(StatModifier.flat(&"hp_regen", RESTED_REGEN, "Well Rested"))
	return mods

# ---- Guild, tier, rest -------------------------------------------------------------------------------------

func set_tier(rank: int) -> void:
	tier = clampi(rank, 0, DataGuilds.MAX_RANK)
	equipment.tier_rank = tier
	stats_dirty.emit()
	Events.tier_changed.emit(tier)

func is_rested() -> bool:
	return rested_until > play_time

func rested_seconds_left() -> float:
	return maxf(0.0, rested_until - play_time)

## Derived stats. `runtime_mods` are temporary (buffs/debuffs/class resource states) supplied by the actor.
func compute_stats(runtime_mods: Array = []) -> DerivedStats:
	var mods := persistent_modifiers()
	mods.append(StatModifier.flat(&"carry_weight", carried_weight()))
	mods.append_array(runtime_mods)
	return StatCalculator.compute(cls, progress.level, progress.base_attributes(), mods, equipment.loadout())

## Weight of the worn equipment plus the bag.
func carried_weight() -> float:
	return equipment.weight() + inventory.weight()

# ---- Skills -----------------------------------------------------------------------------------------------

func skill_rank(skill_id: StringName) -> int:
	return skill_tree.rank(skill_id)

## "+N to all skills" from equipment (raises learned passives too, like actives).
static func item_skill_levels(mods: Array) -> int:
	var n := 0.0
	for m in mods:
		if m is StatModifier and m.stat == &"skill_levels" and m.op == StatModifier.Op.FLAT:
			n += m.value
	return clampi(int(n), 0, 5)

## Learned passive nodes (the Disciplines/Mastery/Instincts pages).
func learned_passives() -> Array:
	var out := []
	for n in skill_tree.tree.nodes:
		if n.get("kind", "") == "passive" and skill_tree.rank(n.id) > 0:
			out.append(n.id)
	return out

## Diablo II style synergies: each learned rank of a listed node adds pct% damage to this skill (param "syn_pct").
func synergy_pct(skill_id: StringName) -> float:
	var n := skill_tree.tree.node(skill_id)
	var total := 0.0
	for syn in n.get("synergies", []):
		total += float(syn[1]) * skill_tree.tree.power_of(StringName(syn[0]), skill_tree.rank(StringName(syn[0])))
	return total

func learned_skills() -> Array:
	var out := []
	for n in skill_tree.tree.nodes:
		if n.kind == "skill" and skill_tree.rank(n.id) > 0:
			out.append(n.skill)
	return out

## Summed upgrade parameter deltas for a skill.
func skill_upgrades(skill_id: StringName) -> Dictionary:
	var out := {}
	for n in skill_tree.tree.nodes:
		if n.kind != "upgrade" or n.get("skill") != skill_id:
			continue
		var r := skill_tree.tree.power_of(n.id, skill_tree.rank(n.id))
		if r <= 0.0:
			continue
		var p: Dictionary = n.get("params", {})
		for k in p:
			out[k] = float(out.get(k, 0.0)) + float(p[k]) * r
	var syn := synergy_pct(skill_id)
	if syn > 0.0:
		out["syn_pct"] = float(out.get("syn_pct", 0.0)) + syn
	return out

func resolved_skill(skill_id: StringName) -> Dictionary:
	var s := DB.skill(skill_id)
	if s == null:
		return {}
	return s.resolve(skill_rank(skill_id), skill_upgrades(skill_id))

func spend_skill_point(node_id: StringName) -> String:
	var err := skill_tree.can_rank_up(node_id, progress.skill_points, progress.level)
	if err != "":
		return err
	var used := skill_tree.rank_up(node_id, progress.skill_points, progress.level)
	progress.skill_points -= used
	# Auto-place newly learned skills on the first empty bar slot.
	var n := skill_tree.tree.node(node_id)
	if n.kind == "skill" and skill_tree.rank(node_id) == 1 and not skill_bar.has(n.skill):
		var idx := skill_bar.find(&"")
		if idx >= 0:
			skill_bar[idx] = n.skill
	progress.points_changed.emit()
	skills_changed.emit()
	return ""

func refund_skill_point(node_id: StringName) -> String:
	if cls.starting_skills.has(node_id) and skill_tree.rank(node_id) == 1:
		return "Starting skill cannot be unlearned"
	var err := skill_tree.can_refund(node_id)
	if err != "":
		return err
	progress.skill_points += skill_tree.refund(node_id)
	var n := skill_tree.tree.node(node_id)
	if n.kind == "skill" and skill_tree.rank(node_id) == 0:
		var idx := skill_bar.find(n.skill)
		if idx >= 0:
			skill_bar[idx] = &""
		if active_aura == n.skill:
			active_aura = &""
	progress.points_changed.emit()
	skills_changed.emit()
	return ""

func spend_talent_point(node_id: StringName) -> String:
	var err := talent_tree.can_rank_up(node_id, progress.talent_points, progress.level)
	if err != "":
		return err
	progress.talent_points -= talent_tree.rank_up(node_id, progress.talent_points, progress.level)
	progress.points_changed.emit()
	return ""

func refund_talent_point(node_id: StringName) -> String:
	var err := talent_tree.can_refund(node_id)
	if err != "":
		return err
	progress.talent_points += talent_tree.refund(node_id)
	progress.points_changed.emit()
	return ""

# ---- Equipment flow ---------------------------------------------------------------------------------------

## Equip an inventory item. Displaced items go back to the inventory. Returns "" or an error.
func equip_from_inventory(item: ItemInstance, slot: StringName = &"") -> String:
	if slot == &"":
		slot = equipment.auto_slot(item)
	var err := equipment.check(item, slot, progress.level, progress.base_attributes())
	if err != "":
		return err
	var idx := inventory.index_of(item)
	# A two-handed replacement can return both hands. Reserved belt cells cannot
	# hold either piece, so check general bag space before changing equipment.
	var needed := 1 if equipment.get_item(slot) != null else 0
	if slot == &"main_weapon":
		var wt := equipment.weapon_type_of(item)
		var sub := equipment.get_item(&"sub_weapon")
		if sub != null and wt != null and (wt.two_handed or (sub.base.is_weapon() and not wt.dual_wieldable)):
			needed += 1
	if needed > inventory.free_cells() + (1 if idx >= 0 and idx < inventory.bag_capacity else 0):
		return "Gear Bag needs room for the replaced equipment"
	_loading_equipment = true
	if idx >= 0:
		inventory.cells[idx] = null
	var res := equipment.equip(item, slot, progress.level, progress.base_attributes())
	for d in res.displaced:
		if idx >= 0 and inventory.cells[idx] == null:
			inventory.cells[idx] = d
		else:
			inventory.add(d)
	_loading_equipment = false
	inventory.changed.emit()
	return ""

func unequip_to_inventory(slot: StringName) -> String:
	var it := equipment.get_item(slot)
	if it == null:
		return ""
	var needed := 1
	if slot == &"main_weapon" and equipment.get_item(&"sub_weapon") != null and equipment.get_item(&"sub_weapon").base.is_weapon():
		needed = 2
	if inventory.free_cells() < needed:
		return "Inventory is full"
	_loading_equipment = true
	equipment.unequip(slot)
	inventory.add(it)
	var orphan := equipment.orphaned_sub()
	if orphan != null:
		equipment.unequip(&"sub_weapon")
		inventory.add(orphan)
	_loading_equipment = false
	inventory.changed.emit()
	return ""

## Swap two equipped items (two rings, two gloves). Both must fit the other's slot.
func swap_equipped(a: StringName, b: StringName) -> String:
	var ia := equipment.get_item(a)
	var ib := equipment.get_item(b)
	if ia == null:
		return ""
	if not (BH.CATEGORY_SLOTS.get(ia.base.category, []) as Array).has(b):
		return "Does not fit there"
	if ib != null and not (BH.CATEGORY_SLOTS.get(ib.base.category, []) as Array).has(a):
		return "Does not fit there"
	equipment.slots[a] = ib
	equipment.slots[b] = ia
	# Validate the resulting pair, so dragging a bow into the off hand cannot bypass equip rules.
	var error := equipment.check(ia, b, progress.level, progress.base_attributes())
	if error == "" and ib != null:
		error = equipment.check(ib, a, progress.level, progress.base_attributes())
	if error != "":
		equipment.slots[a] = ia
		equipment.slots[b] = ib
		return error
	equipment.changed.emit()
	return ""

# ---- NPCs & dialogue ---------------------------------------------------------------------------------------

const REL_MIN := -100
const REL_MAX := 100

func _npc_mem(npc_id: StringName) -> Dictionary:
	if not dialogue.has(npc_id):
		dialogue[npc_id] = {"visited": {}, "rel": 0}
	return dialogue[npc_id]

func dialogue_visited(npc_id: StringName, node_id: String) -> bool:
	return dialogue.has(npc_id) and dialogue[npc_id].visited.has(node_id)

func mark_dialogue_visited(npc_id: StringName, node_id: String) -> void:
	_npc_mem(npc_id).visited[node_id] = true

func relationship(npc_id: StringName) -> int:
	return int(dialogue[npc_id].rel) if dialogue.has(npc_id) else 0

func add_relationship(npc_id: StringName, delta: int) -> void:
	var m := _npc_mem(npc_id)
	m.rel = clampi(int(m.rel) + delta, REL_MIN, REL_MAX)

func npc(npc_id: StringName) -> Dictionary:
	if not npc_state.has(npc_id):
		npc_state[npc_id] = {}
	return npc_state[npc_id]

# ---- Serialization ----------------------------------------------------------------------------------------

func to_dict() -> Dictionary:
	var bar := []
	for s in skill_bar:
		bar.append(String(s))
	return {
		"class": String(cls.id), "name": hero_name, "progress": progress.to_dict(),
		"equipment": equipment.to_dict(), "inventory": inventory.to_array(), "gold": inventory.gold,
		"skills": skill_tree.to_dict(), "talents": talent_tree.to_dict(), "skill_bar": bar,
		"discovered_maps": discovered_maps.keys().map(func(k): return String(k)),
		"teleporters": unlocked_teleporters.keys().map(func(k): return String(k)),
		"awakened_shrines": awakened_shrines.keys().map(func(k): return String(k)),
		"known_places": known_places.keys().map(func(k): return String(k)), "route": route.duplicate(),
		"flags": _flags_out(), "map": String(current_map), "spawn": String(current_spawn), "play_time": play_time,
		"difficulty": difficulty, "dialogue": _dialogue_out(), "npcs": _keyed_out(npc_state), "shops": _keyed_out(shops),
		"guild": String(guild), "tier": tier, "tier_cheat_level": tier_cheat_level, "tier_rules_version": 2, "rested_until": rested_until,
		"tempos": tempos.map(func(t): return t.to_dict()), "tempo_roster": tempo_roster.duplicate(true), "tempo_serial": tempo_serial,
		"town_portal": town_portal.duplicate(true), "belt": potion_belt.map(func(b): return String(b)),
		"known_recipes": known_recipes.keys().map(func(k): return String(k)), "crafted_count": crafted_count,
		"clear_count": clear_count, "stages_cleared": _keyed_plain(stages_cleared), "miniboss_log": _keyed_out(miniboss_log),
		"checkpoint": checkpoint.duplicate(true), "gather_log": gather_log.duplicate(),
		"active_aura": String(active_aura), "chest_log": chest_log.duplicate(), "summon": summon.duplicate(true), "dungeon_raids": dungeon_raids.duplicate(true),
		"spirit_hall": spirit_hall.map(func(t): return t.to_dict()), "starter_name": starter_name,
		"guild_jobs": GuildJobs.to_dict(self),
		"quake_team": quake_team.map(func(m): return (m as QuakeMate).to_dict()),
		"guild_alias": guild_alias, "guild_banner": Marshalls.raw_to_base64(guild_banner) if not guild_banner.is_empty() else "",
		"look": HeroLook.to_save(HeroLook.sanitize(look)),
	}

static func _keyed_plain(src: Dictionary) -> Dictionary:
	var d := {}
	for k in src:
		d[String(k)] = src[k]
	return d

## A clear (stage or miniboss) happened: count it and tell listeners (Olivar restocks, HUD notice).
func add_clear() -> void:
	clear_count += 1
	Events.clears_changed.emit(clear_count)

func _dialogue_out() -> Dictionary:
	var d := {}
	for k in dialogue:
		d[String(k)] = {"visited": dialogue[k].visited.keys(), "rel": int(dialogue[k].rel)}
	return d

static func _keyed_out(src: Dictionary) -> Dictionary:
	var d := {}
	for k in src:
		d[String(k)] = src[k].duplicate(true)
	return d

func _flags_out() -> Dictionary:
	var d := {}
	for k in world_flags:
		d[String(k)] = world_flags[k]
	return d

static func from_dict(d: Dictionary) -> HeroData:
	var c := DB.class_def(StringName(d.get("class", "knight")))
	if c == null:
		return null
	var h := HeroData.new()
	h.setup(c, String(d.get("name", "Hero")))
	h._loading_equipment = true
	h.progress.from_dict(d.get("progress", {}))
	h.equipment.from_dict(d.get("equipment", {}))
	h.inventory.from_array(d.get("inventory", []))
	h.inventory.gold = int(d.get("gold", 0))
	h.skill_tree.from_dict(d.get("skills", {}))
	h.talent_tree.from_dict(d.get("talents", {}))
	var bar: Array = d.get("skill_bar", [])
	for i in SKILL_BAR_SIZE:
		h.skill_bar[i] = StringName(bar[i]) if i < bar.size() else &""
	var belt: Array = d.get("belt", [])
	for i in BELT_SIZE:
		h.set_belt(i, StringName(belt[i]) if i < belt.size() else &"")
	for m in d.get("discovered_maps", []):
		h.discovered_maps[StringName(m)] = true
	for t in d.get("teleporters", []):
		h.unlocked_teleporters[StringName(t)] = true
	for t in d.get("awakened_shrines", []):
		if DataIsland.NETWORK.has(StringName(t)):
			h.awakened_shrines[StringName(t)] = true
	for p in d.get("known_places", []):
		if not DataIsland.place(String(p)).is_empty():
			h.known_places[String(p)] = true
	var rt = d.get("route", {})
	if rt is Dictionary and not DataIsland.place(String(rt.get("dest", ""))).is_empty():
		h.route = {"dest": String(rt.dest), "mode": clampi(int(rt.get("mode", 0)), 0, 2)}
	var fl: Dictionary = d.get("flags", {})
	for k in fl:
		h.world_flags[StringName(k)] = fl[k]
	var tp = d.get("town_portal", {})
	if tp is Dictionary and tp.has("map") and tp.get("pos") is Array and (tp.pos as Array).size() == 3:
		h.town_portal = {"map": String(tp.map), "pos": (tp.pos as Array).map(func(v): return float(v)), "yaw": float(tp.get("yaw", 0.0))}
	h.current_map = StringName(d.get("map", "sanctuary"))
	h.current_spawn = StringName(d.get("spawn", "start"))
	h.play_time = float(d.get("play_time", 0.0))
	h.difficulty = int(d.get("difficulty", 1))
	var dl: Dictionary = d.get("dialogue", {})
	for k in dl:
		var vis := {}
		for n in dl[k].get("visited", []):
			vis[String(n)] = true
		h.dialogue[StringName(k)] = {"visited": vis, "rel": clampi(int(dl[k].get("rel", 0)), REL_MIN, REL_MAX)}
	var ns: Dictionary = d.get("npcs", {})
	for k in ns:
		h.npc_state[StringName(k)] = (ns[k] as Dictionary).duplicate(true)
	var sh: Dictionary = d.get("shops", {})
	for k in sh:
		h.shops[StringName(k)] = (sh[k] as Dictionary).duplicate(true)
	# guild data (absent in older saves: Unranked, nothing equipped is removed)
	var g := StringName(d.get("guild", ""))
	h.guild = g if DataGuilds.GUILDS.has(g) else &""
	h.tier_cheat_level = int(d.get("tier_cheat_level", -1))
	h.tier = clampi(int(d.get("tier", 0)), 0, DataGuilds.MAX_RANK) if h.guild != &"" or h.tier_cheat_level >= 1 else 0
	h.equipment.tier_rank = h.tier
	h.rested_until = float(d.get("rested_until", 0.0))
	# Tempos (absent in older saves: none bound)
	for td in d.get("tempos", []):
		if td is Dictionary and h.tempos.size() < DataTempos.MAX_ACTIVE:
			h.tempos.append(TempoData.from_dict(td))
	var roster = d.get("tempo_roster", {})
	if roster is Dictionary and not (roster as Dictionary).is_empty():
		# normalised through TempoData so a JSON round trip (ints read back as floats) stays exact
		h.tempo_roster = {"offers": (roster.get("offers", []) as Array).map(func(o): return TempoData.from_dict(o).to_dict()),
			"refresh_at": float(roster.get("refresh_at", 0.0)), "serial": int(roster.get("serial", 0)),
			"grade": clampi(int(roster.get("grade", 1)), 1, DataTempos.max_grade())}
	# crafting, stages, minibosses, checkpoint, herbs (bh-007; absent in older saves)
	for rid in d.get("known_recipes", []):
		if not DataCrafting.recipe(StringName(rid)).is_empty():
			h.known_recipes[StringName(rid)] = true
	h.crafted_count = int(d.get("crafted_count", 0))
	h.clear_count = maxi(0, int(d.get("clear_count", 0)))
	var sc = d.get("stages_cleared", {})
	if sc is Dictionary:
		for k in sc:
			h.stages_cleared[StringName(k)] = int(sc[k])
	var ml = d.get("miniboss_log", {})
	if ml is Dictionary:
		for k in ml:
			if ml[k] is Dictionary:
				h.miniboss_log[StringName(k)] = {"kills": int(ml[k].get("kills", 0)), "at": float(ml[k].get("at", 0.0))}
	var cp = d.get("checkpoint", {})
	if cp is Dictionary and cp.has("map") and DB.map_def(StringName(cp.map)) != null:
		h.checkpoint = {"map": String(cp.map), "spawn": String(cp.get("spawn", "start")), "name": String(cp.get("name", ""))}
	var gl = d.get("gather_log", {})
	if gl is Dictionary:
		for k in gl:
			h.gather_log[String(k)] = float(gl[k])
	var cl = d.get("chest_log", {})
	if cl is Dictionary:
		for k in cl:
			h.chest_log[String(k)] = float(cl[k])
	var dr = d.get("dungeon_raids", {})
	if dr is Dictionary:
		for k in dr:
			if dr[k] is Dictionary:
				h.dungeon_raids[String(k)] = {"at": float(dr[k].get("at", 0.0)), "until": float(dr[k].get("until", 0.0)), "count": int(dr[k].get("count", 1))}
	var sm = d.get("summon", {})
	if sm is Dictionary:
		h.summon = sm.duplicate(true)
	# heroes from before bh-015 met Tobren
	h.starter_name = String(d.get("starter_name", DataTempos.STARTER.name))
	for td in d.get("spirit_hall", []):
		if td is Dictionary:
			var st := TempoData.from_dict(td)
			if st != null:
				h.spirit_hall.append(st)
	h.guild_jobs = GuildJobs.from_dict(d.get("guild_jobs", {}))
	h.guild_alias = GuildRules.clean_alias(String(d.get("guild_alias", "")))
	for qd in d.get("quake_team", []):
		if qd is Dictionary and h.quake_team.size() < QuakeTeam.MAX:
			var qm := QuakeMate.from_dict(qd)
			if qm != null:
				h.quake_team.append(qm)
	h.guild_banner = GuildRules.load_banner_bytes(String(d.get("guild_banner", "")))
	var lk = d.get("look", {})
	h.look = HeroLook.to_save(HeroLook.sanitize(lk)) if lk is Dictionary else {}
	var aura := StringName(d.get("active_aura", ""))
	if aura != &"" and h.skill_tree.rank(aura) > 0 and DB.skill(aura) != null and DB.skill(aura).is_aura():
		h.active_aura = aura
	h.tempo_serial = int(d.get("tempo_serial", 0))
	for t in h.tempos + h.spirit_hall:
		h.tempo_serial = maxi(h.tempo_serial, t.uid)
	if int(d.get("tier_rules_version", 1)) < 2:
		GuildRules.migrate_legacy_rank(h)
	h._loading_equipment = false
	h.recover_unequipped_gear()
	h.check_promotions()
	return h

# ---- Potion belt (bh-011) ---------------------------------------------------------------------------------------

## The default binding of a belt slot: slot 0 the strongest health draught, slot 1 the strongest mana draught.
static func belt_default(slot: int) -> StringName:
	return BELT_AUTO_HEAL if slot == 0 else BELT_AUTO_MANA

static func belt_is_auto(id: StringName) -> bool:
	return id == BELT_AUTO_HEAL or id == BELT_AUTO_MANA

## Bind a belt slot. "" (or anything that is not a usable consumable) restores the slot's default.
func set_belt(slot: int, id: StringName) -> void:
	if slot < 0 or slot >= BELT_SIZE:
		return
	if not belt_is_auto(id):
		var base := DB.item_base(id) if id != &"" else null
		if base == null or not base.is_consumable():
			id = belt_default(slot)
	potion_belt[slot] = id

## The item base a belt slot would drink now (an auto slot: the strongest draught in the bag, or the plain draught when
## the bag has none, for its picture) and how many uses the bag holds for it.
func belt_preview(slot: int) -> Dictionary:
	var id: StringName = potion_belt[slot] if slot >= 0 and slot < BELT_SIZE else &""
	if belt_is_auto(id):
		var kind := &"heal" if id == BELT_AUTO_HEAL else &"mana"
		var n := 0
		var best: StringName = &""
		for bid in Player.POTION_ORDER[kind]:
			var c := inventory.count_of(bid)
			n += c
			if c > 0 and best == &"":
				best = bid
		if best == &"":
			best = &"health_potion" if kind == &"heal" else &"mana_potion"
		return {"base": best, "count": n, "auto": kind}
	return {"base": id, "count": inventory.count_of(id), "auto": &""}

## Plain words for a belt binding ("Strongest health draught", "Frost Flask").
static func belt_label(id: StringName) -> String:
	if id == BELT_AUTO_HEAL:
		return "Strongest health draught"
	if id == BELT_AUTO_MANA:
		return "Strongest mana draught"
	var base := DB.item_base(id)
	return base.display_name if base else String(id)
