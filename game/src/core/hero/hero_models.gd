class_name HeroModels
extends RefCounted
## Optional class outfits from Warriors of Aether. Missing/legacy look keys keep
## the fully editable hero and its fitted equipment.

const DIR := "res://assets/characters/roles/"
const HUNTER := DIR + "hunter.tscn"
const MODELS := {&"knight": DIR + "emelrich.glb", &"mage": DIR + "azrin.glb",
	&"ranger": HUNTER, &"shadowblade": DIR + "caziel.glb"}
static var _bow_paths := {}

static func model_for(class_id: StringName, look: Dictionary) -> String:
	if String(look.get("body", "custom")) == "class" and MODELS.has(class_id):
		return MODELS[class_id]
	return HeroLook.MODEL

static func is_role(path: String) -> bool:
	return MODELS.values().has(path)

static func fits(path: String) -> bool:
	return is_role(path) or path == HeroLook.MODEL or path in ["res://assets/characters/knight.glb",
		"res://assets/characters/mage.glb", "res://assets/characters/ranger.glb", "res://assets/characters/shadowblade.glb"]

## The Blood Ranger holds the bow in her left hand and draws with her right.
## Resolve every actual equipped bow, including uniques, without changing the
## appearance wire format or substituting a cosmetic weapon.
static func weapon_bone(hand: StringName, path: String) -> String:
	if hand != &"main":
		return "weapon.L"
	if _bow_paths.is_empty():
		_bow_paths["res://assets/weapons/bow.glb"] = true
		_bow_paths["res://assets/weapons/bow_aether.glb"] = true
		for base: ItemBaseDef in DB.item_bases.values():
			if base.weapon_type == &"bow":
				_bow_paths[base.model_path()] = true
	return "weapon.L" if _bow_paths.has(path) else "weapon.R"

## The source Blood Ranger's fixed cosmetic outfit. Its body is byte-identical
## to HeroLook.MODEL (manifest.json); only this presentation changes.
static func blood_ranger(v: CharacterVisual) -> HeroBody:
	var body := HeroBody.new(v)
	if not body.ok():
		return null
	var look := HeroLook.preset("huntress")
	look.merge({"hair": "long", "hair_color": "861620", "hair_length": 1.0,
		"skin": "e8c2a8", "eye": "cat", "eye_color": "e0202c", "eye_glow": 0.55,
		"lip_color": "8a2028", "marking": "none", "build": -0.35, "show_helm": false}, true)
	body.apply(look)
	body.dyes = {"armor": {"cloth": "8a1018", "leather": "3a1c16", "trim": "c8a060", "metal": "6a5a50"},
		"leggings": {"cloth": "2e1414", "leather": "2a1610"},
		"boots_1": {"leather": "2a1610"}, "boots_2": {"leather": "2a1610"},
		"inner_garment": {"cloth": "5a1016"},
		"gloves_1": {"cloth": "3a1012", "leather": "2a1610"}, "gloves_2": {"cloth": "3a1012", "leather": "2a1610"}}
	body.merge_key = "blood_ranger"
	var equipment := Equipment.new()
	for pair in [[&"inner_garment", &"silk_undershirt"], [&"armor", &"tc_trackers_leathers"],
		[&"leggings", &"trackers_breeches"], [&"boots_1", &"wayfarer_boot"], [&"boots_2", &"wayfarer_boot"],
		[&"gloves_1", &"silk_glove"], [&"gloves_2", &"silk_glove"], [&"accessory_1", &"tc_bloodmoon_signet"]]:
		var item := ItemInstance.new()
		item.base = DB.item_base(pair[1])
		equipment.slots[pair[0]] = item
	body.dress(equipment)
	return body
