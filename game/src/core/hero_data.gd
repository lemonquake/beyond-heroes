class_name HeroData
extends RefCounted
## Complete persistent state of a hero (everything the save file stores except settings).
## Pure model: no nodes. Emits `stats_dirty` when anything affecting derived stats changes.

signal stats_dirty
signal inventory_changed
signal skills_changed

const SKILL_BAR_SIZE := 6

var cls: ClassDef
var hero_name := "Hero"
var progress := HeroProgress.new()
var equipment := Equipment.new()
var inventory := Inventory.new()
var skill_tree: TreeState
var talent_tree: TreeState
var skill_bar: Array = []                 # skill ids (StringName) or &""
var discovered_maps := {}                 # map id -> true
var unlocked_teleporters := {}            # teleporter id -> true
var world_flags := {}                     # e.g. &"boss_warden_defeated"
var current_map: StringName = &"sanctuary"
var current_spawn: StringName = &"start"
var play_time := 0.0
var potion_belt := [&"health_potion", &"mana_potion"]
var difficulty := 1
## Per-NPC memory: npc id -> {"visited": {node_id: true}, "rel": int}. Relationship is reputation-ready (-100..100).
var dialogue := {}
## Free-form NPC state (met, gifts given, services used ...): npc id -> Dictionary.
var npc_state := {}
## Merchant state that must survive saving (stock, refresh clock, sold specials): shop id -> Shop.to_dict().
var shops := {}

func setup(p_cls: ClassDef, p_name: String) -> void:
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
	stats_dirty.emit()

func _inv_changed() -> void:
	inventory_changed.emit()

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
	discovered_maps[&"sanctuary"] = true

## All persistent stat modifiers: equipment + talents.
func persistent_modifiers() -> Array:
	var mods := equipment.modifiers()
	mods.append_array(talent_tree.modifiers())
	return mods

## Derived stats. `runtime_mods` are temporary (buffs/debuffs/class resource states) supplied by the actor.
func compute_stats(runtime_mods: Array = []) -> DerivedStats:
	var mods := persistent_modifiers()
	mods.append_array(runtime_mods)
	return StatCalculator.compute(cls, progress.level, progress.base_attributes(), mods, equipment.loadout())

# ---- Skills -----------------------------------------------------------------------------------------------

func skill_rank(skill_id: StringName) -> int:
	return skill_tree.rank(skill_id)

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
		var r := skill_tree.rank(n.id)
		if r <= 0:
			continue
		var p: Dictionary = n.get("params", {})
		for k in p:
			out[k] = float(out.get(k, 0.0)) + float(p[k]) * r
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
	if idx >= 0:
		inventory.cells[idx] = null
	var res := equipment.equip(item, slot, progress.level, progress.base_attributes())
	for d in res.displaced:
		if idx >= 0 and inventory.cells[idx] == null:
			inventory.cells[idx] = d
		else:
			inventory.add(d)
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
	equipment.unequip(slot)
	inventory.add(it)
	var orphan := equipment.orphaned_sub()
	if orphan != null:
		equipment.unequip(&"sub_weapon")
		inventory.add(orphan)
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
		"flags": _flags_out(), "map": String(current_map), "spawn": String(current_spawn), "play_time": play_time,
		"difficulty": difficulty, "dialogue": _dialogue_out(), "npcs": _keyed_out(npc_state), "shops": _keyed_out(shops),
	}

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
	h.progress.from_dict(d.get("progress", {}))
	h.equipment.from_dict(d.get("equipment", {}))
	h.inventory.from_array(d.get("inventory", []))
	h.inventory.gold = int(d.get("gold", 0))
	h.skill_tree.from_dict(d.get("skills", {}))
	h.talent_tree.from_dict(d.get("talents", {}))
	var bar: Array = d.get("skill_bar", [])
	for i in SKILL_BAR_SIZE:
		h.skill_bar[i] = StringName(bar[i]) if i < bar.size() else &""
	for m in d.get("discovered_maps", []):
		h.discovered_maps[StringName(m)] = true
	for t in d.get("teleporters", []):
		h.unlocked_teleporters[StringName(t)] = true
	var fl: Dictionary = d.get("flags", {})
	for k in fl:
		h.world_flags[StringName(k)] = fl[k]
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
		# through the Shop model so numbers come back with their real types (JSON makes every number a float)
		var shop := Shop.new()
		shop.def = DB.shop(StringName(k))
		shop.from_dict(sh[k])
		h.shops[StringName(k)] = shop.to_dict()
	return h
