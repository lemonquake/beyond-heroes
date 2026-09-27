class_name NpcDef
extends RefCounted
## A townsperson: who they are, where they stand, what they offer, and their conversation graph (see Dialogue).

var id: StringName
var display_name := ""
var title := ""                        # shown under the name ("Blacksmith")
var portrait := ""                     # res:// path of the dialogue portrait
var map: StringName = &"sanctuary"
var position := Vector3.ZERO           # map-local position (y is added on top of the ground)
var yaw := 0.0                         # degrees; 0 faces +Z
var model := "res://assets/characters/knight.glb"
var model_scale := 1.0
var tint := Color(1, 1, 1)
var shop: StringName = &""             # ShopDef id opened by "open_shop"
var services: Array = []               # heal, respec
var presence: Array = []               # Dialogue conditions that must hold for the NPC to be in the world
var idle_anims: Array = [&"idle", &"idle_look"]
var greeting_sound: StringName = &""   # voice-ready: bark played when the conversation opens
var graph := {}
## bh-007 — heroes in a camp: their level, tier (DataGuilds rank), guild and class show on the name plate and in the
## hero register (HeroRosterWindow). weapon / offhand: item base ids held in hand. activity: "" (stand), "spar"
## (swing at a training dummy in front), "cast" (practise spells), "pace" (walk to pace_to and back), "watch".
var hero_level := 0
var hero_tier := 0
var hero_guild: StringName = &""
var hero_class: StringName = &""
var hero_note := ""
var weapon: StringName = &""
var offhand: StringName = &""
var activity: StringName = &""
var pace_to := Vector3.ZERO

func is_hero() -> bool:
	return hero_level > 0

static func make(p_id: StringName, p_name: String, d: Dictionary) -> NpcDef:
	var n := NpcDef.new()
	n.id = p_id
	n.display_name = p_name
	for k in d:
		n.set(k, d[k])
	return n
