extends Node
## Game database: loads every data definition once and offers typed lookups (autoload `DB`).

var classes := {}
var weapon_types := {}
var item_bases := {}
var affix_defs := {}
var power_defs := {}
var item_sets := {}
var licenses := {}
var skills := {}
var trees := {}
var enemies := {}
var elite_mods := {}
var maps := {}
var anim_meta := {}
var npcs := {}
var shops := {}

func _init() -> void:
	for c in DataClasses.build():
		classes[c.id] = c
	for w in DataWeapons.build():
		weapon_types[w.id] = w
	for b in DataItems.bases():
		item_bases[b.id] = b
	for a in DataItems.affixes() + DataRelics.affixes():
		affix_defs[a.id] = a
	for p in DataItems.powers() + DataRelics.powers():
		power_defs[p.id] = p
	for st in DataItems.sets():
		item_sets[st.id] = st
	licenses = DataItems.licenses()
	for s in DataSkills.skills():
		skills[s.id] = s
	for t in [DataSkills.knight_tree(), DataSkills.mage_tree(), DataTalents.knight(), DataTalents.mage(),
			DataSkillsExt.ranger_tree(), DataSkillsExt.shadowblade_tree(), DataTalentsExt.ranger(), DataTalentsExt.shadowblade()]:
		trees[t.id] = t
	for e in DataEnemies.build():
		enemies[e.id] = e
	elite_mods = DataEnemies.elite_mods()
	for m in DataMaps.build():
		maps[m.id] = m
	for n in DataNpcs.build() + DataNpcsTown.build() + DataNpcsOlivar.build() + DataNpcsWyman.build():
		npcs[n.id] = n
	for sh in DataShops.build():
		shops[sh.id] = sh
	_load_anim_meta()

func _load_anim_meta() -> void:
	var path := "res://assets/characters/anim_meta.json"
	if not FileAccess.file_exists(path):
		return
	var txt := FileAccess.get_file_as_string(path)
	var parsed = JSON.parse_string(txt)
	if parsed is Dictionary:
		anim_meta = parsed.get("animations", {})
	# non-humanoid creature clips (dire wolf ...): same schema, never overrides the humanoid library
	var cpath := "res://assets/characters/creature_meta.json"
	if FileAccess.file_exists(cpath):
		var c = JSON.parse_string(FileAccess.get_file_as_string(cpath))
		if c is Dictionary:
			var ca: Dictionary = c.get("animations", {})
			for k in ca:
				if not anim_meta.has(k):
					anim_meta[k] = ca[k]

func class_def(id: StringName) -> ClassDef:
	return classes.get(id)

func weapon_type(id: StringName) -> WeaponTypeDef:
	return weapon_types.get(id)

func item_base(id: StringName) -> ItemBaseDef:
	return item_bases.get(id)

func affix(id: StringName) -> AffixDef:
	return affix_defs.get(id)

func power(id: StringName) -> LegendaryPowerDef:
	return power_defs.get(id)

func item_set(id: StringName) -> SetDef:
	return item_sets.get(id)

func skill(id: StringName) -> SkillDef:
	return skills.get(id)

func tree(id: StringName) -> TreeDef:
	return trees.get(id)

func enemy(id: StringName) -> EnemyDef:
	return enemies.get(id)

func map_def(id: StringName) -> MapDef:
	return maps.get(id)

func npc(id: StringName) -> NpcDef:
	return npcs.get(id)

func shop(id: StringName) -> ShopDef:
	return shops.get(id)

func affixes_for(category: StringName) -> Array:
	var out := []
	for a in affix_defs.values():
		if a.allows(category):
			out.append(a)
	out.sort_custom(func(x, y): return String(x.id) < String(y.id))
	return out

func powers_for(category: StringName) -> Array:
	var out := []
	for p in power_defs.values():
		if p.categories.is_empty() or p.categories.has(category):
			out.append(p)
	out.sort_custom(func(x, y): return String(x.id) < String(y.id))
	return out

## Animation timing metadata; falls back to AnimDefaults when an animation is missing from the sidecar.
func anim(name: StringName) -> Dictionary:
	var m: Dictionary = anim_meta.get(String(name), {})
	if m.is_empty():
		if not _anim_default_cache.has(name):
			_anim_default_cache[name] = AnimDefaults.meta(name)
		return _anim_default_cache[name]
	return m

var _anim_default_cache := {}

func make_item(base_id: StringName, rarity := BH.Rarity.COMMON, ilvl := 1, seed_value := 0) -> ItemInstance:
	var b := item_base(base_id)
	if b == null:
		push_error("Unknown item base %s" % base_id)
		return null
	var rng := RandomNumberGenerator.new()
	rng.seed = seed_value if seed_value != 0 else hash(String(base_id) + str(Time.get_ticks_usec()))
	return ItemGenerator.generate(b, ilvl, rarity, rng)
