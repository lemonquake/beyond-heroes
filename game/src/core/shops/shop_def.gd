class_name ShopDef
extends RefCounted
## A merchant's catalogue rules (data only). Stock is generated from these rules by Shop.
##
## fixed:    always in stock — [{"base": id, "rarity": r, "level_min": n, "infinite": bool}]  (infinite = never sells out)
## pools:    random stock rolled at each refresh — [{"categories": [...], "count": n, "class_hint": bool}]
## specials: hand-placed one-of-a-kind items; once bought they never return —
##           [{"id": key, "base": id, "rarity": r, "level_min": n, "flag": world flag required (optional)}]
## rare_chance: chance per refresh that one pool item is upgraded to a rare tier (the "occasional rare stock").

var id: StringName
var display_name := ""
var npc: StringName
var kind := &"general"                 # weapons, armor, magic, consumables, crafting, accessories, rare
var specialties: Array = []            # item categories this merchant specializes in (better prices both ways)
var markup := 1.0                      # buy-price multiplier on top of the item's value
var sell_rate := 1.0                   # multiplier on what the merchant pays you
var fixed: Array = []
var pools: Array = []
var specials: Array = []
var rare_chance := 0.15
var rarity_floor := BH.Rarity.COMMON
var refresh_minutes := 12.0            # stock rerolls after this much play time (and when the hero outlevels it)
var buyback_size := 12

static func make(p_id: StringName, p_name: String, d: Dictionary) -> ShopDef:
	var s := ShopDef.new()
	s.id = p_id
	s.display_name = p_name
	for k in d:
		s.set(k, d[k])
	return s

func is_specialty(item: ItemInstance) -> bool:
	return specialties.has(item.base.category)
