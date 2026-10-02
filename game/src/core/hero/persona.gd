class_name Persona
extends RefCounted
## bh-031: a character drawn on the hero's own body (HeroLook.MODEL): every townsperson, every humanoid monster and
## every Tempo is the player's model with its own look (face, figure, skin, hair), its own clothes (the worn models of
## real item bases, recoloured) and its own weapons. Pure data plus apply(); the people live in DataPersonas.
##
## A persona Dictionary:
##   look  HeroLook overrides (missing keys are the plain hero's)       f      true: a woman (HeroLook.feminize first)
##   wear  item base ids worn (gloves and boots go on both sides)        dye    {cloth, trim, leather, metal, gold: hex}
##   set   a boss collection id worn whole (BossSetVisuals regalia)       main / off  item base ids held in the hands
##   size  overall scale against the 1.8 m hero (the look's height slider multiplies it)
##   stance  the idle stance clip (else from the main weapon)

const MODEL := HeroLook.MODEL

## Off only for measurements (tests/tools/bench_bh031): everyone falls back to their own old model.
static var enabled := true

static func available() -> bool:
	return enabled and ResourceLoader.exists(MODEL)

## The complete look of a persona.
static func look_of(p: Dictionary) -> Dictionary:
	var d := HeroLook.defaults()
	if bool(p.get("f", false)):
		HeroLook.feminize(d)
	d.merge(p.get("look", {}), true)
	return HeroLook.sanitize(d)

## The worn items of a persona as an Equipment (presentation only: bare ItemInstances, no rolls).
static func equipment_of(p: Dictionary) -> Equipment:
	var eq := Equipment.new()
	var sid := String(p.get("set", ""))
	if sid != "":
		for slot in BH.SLOTS:
			if slot == &"main_weapon" or slot == &"sub_weapon":
				continue
			_put(eq, slot, StringName("boss_%s_%s" % [sid, slot]))
	for id in p.get("wear", []):
		var base := DB.item_base(StringName(id))
		if base == null:
			continue
		var slots: Array = base.equipment_slots()
		if base.category == &"gloves" or base.category == &"boots":
			for s in slots:
				_put(eq, s, base.id)
		elif base.category == &"accessory":
			for s in slots:
				if eq.slots.get(s) == null:
					_put(eq, s, base.id)
					break
		elif not slots.is_empty():
			_put(eq, slots[0], base.id)
	return eq

static func _put(eq: Equipment, slot: StringName, id: StringName) -> void:
	var base := DB.item_base(id)
	if base == null:
		return
	var it := ItemInstance.new()
	it.base = base
	eq.slots[slot] = it

## Dress a CharacterVisual that was set up with MODEL. Returns the Equipment worn (or null on another model).
static func apply(v: CharacterVisual, p: Dictionary) -> Equipment:
	if v == null or v.hero == null:
		return null
	v.set_look(look_of(p))
	v.set_dyes(p.get("dye", {}))
	v.hero.merge_key = "persona"
	v.hero._wear_sig = "-"
	var eq := equipment_of(p)
	v.dress_equipment(eq)
	for pair in [[&"main", "main"], [&"off", "off"]]:
		var id := String(p.get(pair[1], ""))
		if id == "":
			v.detach_weapon(pair[0])
			continue
		var base := DB.item_base(StringName(id))
		if base and base.model_path() != "":
			v.attach_weapon(pair[0], base.model_path())
		elif id.begins_with("res://"):
			v.attach_weapon(pair[0], id)
	var stance := StringName(p.get("stance", ""))
	if stance == &"":
		stance = stance_for(String(p.get("main", "")), String(p.get("off", "")))
	if v.has_anim(stance):
		v.set_stance(stance)
	return eq

## The idle stance for what is held.
static func stance_for(main: String, off: String) -> StringName:
	if main == "":
		return &"idle"
	var b := DB.item_base(StringName(main))
	if b == null:
		return &"idle"
	var ob := DB.item_base(StringName(off)) if off != "" else null
	if ob and ob.category == &"shield":
		return &"idle_shield"
	return {&"staff": &"idle_staff", &"wand": &"idle_wand", &"bow": &"idle_bow", &"crossbow": &"idle_bow", &"spear": &"idle_spear",
		&"javelin": &"idle_spear", &"greatsword": &"idle_2h", &"greataxe": &"idle_2h", &"dagger": &"idle_dagger",
		&"claw": &"idle_dagger", &"knuckles": &"idle_dagger"}.get(b.weapon_type, &"idle_1h")

# ---- Who is drawn this way ---------------------------------------------------------------------------------------

static func for_npc(def: NpcDef) -> Dictionary:
	if def == null or not available():
		return {}
	return DataPersonas.npc(def.id)

static func for_enemy(def: EnemyDef) -> Dictionary:
	if def == null or not available():
		return {}
	return DataPersonas.enemy(def)

## A Tempo: its look comes from its own uid (stable for life), its clothes from its gear.
static func tempo_look(uid: int, class_id: StringName, tint: Color) -> Dictionary:
	var rng := RandomNumberGenerator.new()
	rng.seed = hash("tempo:%d" % uid)
	var lk := HeroLook.random(rng, 0.0)
	# a spirit: paler, the eyes lit in the class colour
	var c := Color(String(lk["skin"]))
	lk["skin"] = c.lerp(Color(0.78, 0.82, 0.9), 0.35).to_html(false)
	lk["eye"] = "glowing"
	lk["eye_glow"] = 0.6
	lk["eye_color"] = tint.lightened(0.4).to_html(false)
	return lk

## What a Tempo of each class wears where its own gear leaves a slot empty (a spirit is never drawn bare).
const TEMPO_GARB := {
	&"swordsman": ["padded_gambeson", "iron_hauberk", "mail_chausses", "wayfarer_boot"],
	&"archer": ["silk_undershirt", "traveler_coat", "hide_leggings", "wayfarer_boot"],
	&"thief": ["silk_undershirt", "brigandine", "cutpurse_trousers", "soft_boot", "linen_hood"],
	&"mystic": ["silk_undershirt", "apprentice_robe", "linen_trousers", "soft_boot"],
	&"warden": ["padded_gambeson", "warden_plate", "iron_cuisses", "warden_greave"],
}
const TEMPO_DYE := {"cloth": "8fa6c4", "trim": "34405a", "leather": "4a5468", "metal": "c8d8f0"}

## The Tempo's own equipment with its class garb in the empty body slots.
static func tempo_equipment(own: Equipment, class_id: StringName) -> Equipment:
	var eq := equipment_of({"wear": TEMPO_GARB.get(class_id, TEMPO_GARB[&"swordsman"])})
	if own:
		for s in own.slots:
			if own.slots[s] != null:
				eq.slots[s] = own.slots[s]
	return eq

## Set a Tempo's visual up on the hero body: its own face (from its uid) and class garb. False on old models.
static func setup_tempo(v: CharacterVisual, uid: int, class_id: StringName, tint: Color, glow: Color, rig: StringName) -> bool:
	if not available():
		return false
	v.setup(MODEL, 1.0, tint, rig)
	v.set_look(tempo_look(uid, class_id, glow))
	v.set_dyes(TEMPO_DYE)
	return true
