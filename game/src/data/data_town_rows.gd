class_name DataTownRows
## bh-017: every safe town gathers its trade in one signed street — Malasugue's Merchant Row, Olivar's Market Row and
## Wyman's Quartermaster Row: a gateway with a sign, then a stand for each merchant (their trade painted big on a sign,
## a coloured pennant, a stall with the merchant behind the counter), with the rare dealer, the crafting stations and the
## Tempo-Caller close by. Maps build their row from this table and NPCs read where to stand from it.
##
## Stand keys: id, kind (shop | station | shrine | stash), npc (NpcDef id behind the counter), station (crafting station id),
## label, pos (map-local, y ignored), yaw (degrees, 0 faces +Z: the customer side), title, sub (sign lines), col.

const SHOP := "shop"
const STATION := "station"
const SHRINE := "shrine"

const C_GOODS := Color(0.42, 0.85, 0.45)
const C_ARMS := Color(0.95, 0.42, 0.34)
const C_ARCANA := Color(0.72, 0.5, 1.0)
const C_RARE := Color(1.0, 0.82, 0.3)
const C_JEWEL := Color(1.0, 0.55, 0.75)
const C_ALCHEMY := Color(0.4, 0.95, 0.78)
const C_BENCH := Color(0.95, 0.75, 0.42)
const C_FORGE := Color(1.0, 0.58, 0.25)
const C_SPIRIT := Color(0.55, 0.92, 1.0)

## Where a merchant stands: just outside the awning (too low to stand under), at the right end of the counter, facing the street.
const BESIDE := 1.4
const FORWARD := 1.55

const ROWS := {
	&"sanctuary": {
		"name": "Merchant Row", "gate": Vector3(14.8, 0, 11.4), "gate_yaw": 0.0, "gate_text": "MERCHANT ROW",
		"gate_sub": "Goods · Arms · Arcana · Rare wares · Crafting · Tempos", "col": Color(1.0, 0.82, 0.45),
		"rect": Rect2(6.4, 10.5, 17.0, 23.0),
		"stands": [
			{"id": &"goods", "kind": SHOP, "npc": &"tovin", "pos": Vector3(8.2, 0, 15.0), "yaw": 90.0,
				"title": "GENERAL GOODS", "sign": "item:health_potion", "sign_size": 0.8, "sub": "Potions · Scrolls · Supplies", "col": C_GOODS},
			{"id": &"arcana", "kind": SHOP, "npc": &"seris", "pos": Vector3(8.2, 0, 20.0), "yaw": 90.0,
				"title": "ARCANA & JEWELS", "sign": "item:silver_ring", "sign_size": 0.7, "sub": "Rings · Charms · Staves", "col": C_ARCANA},
			{"id": &"arms", "kind": SHOP, "npc": &"brannoc", "pos": Vector3(8.2, 0, 25.0), "yaw": 90.0,
				"title": "ARMS & ARMOR", "sign": "item:warden_kite_shield", "sign_size": 1.1, "sub": "Weapons · Plate · Shields", "col": C_ARMS},
			{"id": &"shrine", "kind": SHRINE, "npc": &"veyra", "pos": Vector3(8.2, 0, 30.0), "yaw": 90.0,
				"title": "TEMPO SHRINE", "sign": "item:aether_shard", "sign_size": 0.8, "sub": "Bind fallen spirits", "col": C_SPIRIT},
			{"id": &"rare", "kind": SHOP, "npc": &"stranger", "pos": Vector3(21.4, 0, 15.0), "yaw": -90.0,
				"title": "RARE WARES", "sign": "item:sigil_ring", "sign_size": 0.7, "sub": "The dealer comes after the Catacombs", "col": C_RARE},
			{"id": &"alchemy", "kind": STATION, "station": &"alchemy", "label": "Alchemy Table (Enchanting)", "pos": Vector3(21.4, 0, 20.0), "yaw": -90.0,
				"title": "ALCHEMY", "sign": "item:mana_potion", "sign_size": 0.8, "sub": "Brew · Enchant weapons", "col": C_ALCHEMY},
			{"id": &"bench", "kind": STATION, "station": &"workbench", "label": "Workbench", "pos": Vector3(21.4, 0, 25.0), "yaw": -90.0,
				"title": "WORKBENCH", "sign": "item:town_portal", "sign_size": 0.9, "sub": "Bombs · Scrolls · Charms", "col": C_BENCH},
			{"id": &"forge", "kind": STATION, "station": &"forge", "label": "Brannoc's Anvil (Fore-Tech)", "pos": Vector3(21.4, 0, 30.0), "yaw": -90.0,
				"title": "FORGE", "sign": "kit:anvil", "sign_size": 0.9, "sub": "Smith · Salvage · Fore-Tech", "col": C_FORGE},
		],
	},
	&"olivar": {
		"name": "Market Row", "gate": Vector3(-5.2, 0, 14.6), "gate_yaw": 0.0, "gate_text": "MARKET ROW",
		"gate_sub": "Arms · Jewels · Apothecary · Crafting", "col": Color(1.0, 0.82, 0.45),
		"rect": Rect2(-14.4, 14.0, 17.0, 17.0),
		"stands": [
			{"id": &"jewels", "kind": SHOP, "npc": &"elsbeth", "pos": Vector3(-11.6, 0, 18.5), "yaw": 90.0,
				"title": "FINE SETTINGS", "sign": "item:copper_ring", "sign_size": 0.7, "sub": "Rings · Amulets · Charms", "col": C_JEWEL},
			{"id": &"apothecary", "kind": SHOP, "npc": &"aldous", "pos": Vector3(-11.6, 0, 23.5), "yaw": 90.0,
				"title": "APOTHECARY", "sign": "item:health_potion", "sign_size": 0.8, "sub": "Herbs · Draughts · Recipes", "col": C_GOODS},
			{"id": &"alchemy", "kind": STATION, "station": &"alchemy", "label": "Pell's Alchemy Table (Enchanting)", "pos": Vector3(-11.6, 0, 28.5), "yaw": 90.0,
				"title": "ALCHEMY", "sign": "item:mana_potion", "sign_size": 0.8, "sub": "Brew · Enchant weapons", "col": C_ALCHEMY},
			{"id": &"arms", "kind": SHOP, "npc": &"corvin", "pos": Vector3(1.2, 0, 18.5), "yaw": -90.0,
				"title": "ARMS EXCHANGE", "sign": "item:warden_kite_shield", "sign_size": 1.1, "sub": "Advanced weapons & armor", "col": C_ARMS},
			{"id": &"bench", "kind": STATION, "station": &"workbench", "label": "Workbench", "pos": Vector3(1.2, 0, 23.5), "yaw": -90.0,
				"title": "WORKBENCH", "sign": "item:town_portal", "sign_size": 0.9, "sub": "Bombs · Scrolls · Charms", "col": C_BENCH},
			{"id": &"forge", "kind": STATION, "station": &"forge", "label": "Trader's Forge (Fore-Tech)", "pos": Vector3(1.2, 0, 28.5), "yaw": -90.0,
				"title": "FORGE", "sign": "kit:anvil", "sign_size": 0.9, "sub": "Smith · Salvage · Fore-Tech", "col": C_FORGE},
		],
	},
	&"wyman_outpost": {
		"name": "Quartermaster Row", "gate": Vector3(4.0, 0, 12.2), "gate_yaw": 0.0, "gate_text": "QUARTERMASTER ROW",
		"gate_sub": "Supplies · Field kit · Crafting", "col": Color(1.0, 0.82, 0.45),
		"rect": Rect2(-3.0, 12.0, 14.0, 15.0),
		"stands": [
			{"id": &"supplies", "kind": SHOP, "npc": &"hobb", "pos": Vector3(-0.6, 0, 16.0), "yaw": 90.0,
				"title": "SUPPLIES", "sign": "item:health_potion", "sign_size": 0.8, "sub": "Potions · Tonics · Scrolls", "col": C_GOODS},
			{"id": &"outfitter", "kind": SHOP, "npc": &"greta", "pos": Vector3(-0.6, 0, 21.0), "yaw": 90.0,
				"title": "FIELD KIT", "sign": "item:warden_kite_shield", "sign_size": 1.1, "sub": "Weapons · Armor · Shields", "col": C_ARMS},
			{"id": &"forge", "kind": STATION, "station": &"forge", "label": "Field Forge (Fore-Tech)", "pos": Vector3(-0.6, 0, 26.0), "yaw": 90.0,
				"title": "FIELD FORGE", "sign": "kit:anvil", "sign_size": 0.9, "sub": "Smith · Salvage · Fore-Tech", "col": C_FORGE},
			{"id": &"kettle", "kind": STATION, "station": &"alchemy", "label": "Camp Kettle (Enchanting)", "pos": Vector3(9.0, 0, 16.0), "yaw": -90.0,
				"title": "CAMP KETTLE", "sign": "item:mana_potion", "sign_size": 0.8, "sub": "Brew · Enchant weapons", "col": C_ALCHEMY},
			{"id": &"bench", "kind": STATION, "station": &"workbench", "label": "Camp Workbench", "pos": Vector3(9.0, 0, 21.0), "yaw": -90.0,
				"title": "WORKBENCH", "sign": "item:town_portal", "sign_size": 0.9, "sub": "Bombs · Scrolls · Charms", "col": C_BENCH},
		],
	},
}

static func row(map_id: StringName) -> Dictionary:
	return ROWS.get(map_id, {})

## The stand of an NPC (by NpcDef id) or {} when it has none.
static func stand_of_npc(npc_id: StringName) -> Dictionary:
	for m in ROWS:
		for s in ROWS[m].stands:
			if s.get("npc", &"") == npc_id:
				var d: Dictionary = (s as Dictionary).duplicate()
				d["map"] = m
				return d
	return {}

## Unit vector from the stall towards its customers.
static func front(s: Dictionary) -> Vector3:
	return Vector3(0, 0, 1).rotated(Vector3.UP, deg_to_rad(float(s.yaw)))

## Where the NPC stands (behind the counter) and which way it faces.
static func npc_spot(npc_id: StringName) -> Dictionary:
	var s := stand_of_npc(npc_id)
	if s.is_empty():
		return {}
	var p: Vector3 = s.pos + side(s) * BESIDE + front(s) * FORWARD
	return {"position": Vector3(p.x, 0, p.z), "yaw": float(s.yaw)}

## Unit vector along the stall's front (to the merchant's side).
static func side(s: Dictionary) -> Vector3:
	return front(s).cross(Vector3.UP)

## Where a customer stands to trade at a stand.
static func customer_spot(s: Dictionary) -> Vector3:
	var p: Vector3 = s.pos + front(s) * 2.1 - side(s) * 0.9
	return Vector3(p.x, 0, p.z)

## Distance in metres from (x, z) to the row's paved rectangle (0 inside), for the terrain splat; 99 when the map has none.
static func paved_dist(map_id: StringName, x: float, z: float) -> float:
	var r: Dictionary = ROWS.get(map_id, {})
	if r.is_empty():
		return 99.0
	var rc: Rect2 = r.rect
	var dx := maxf(maxf(rc.position.x - x, x - rc.end.x), 0.0)
	var dz := maxf(maxf(rc.position.y - z, z - rc.end.y), 0.0)
	return Vector2(dx, dz).length()

## 0..1 cobble weight of the row at (x, z): full on the street, fading over two metres.
static func paved(map_id: StringName, x: float, z: float) -> float:
	return 1.0 - clampf((paved_dist(map_id, x, z) - 0.4) / 1.8, 0.0, 1.0)
