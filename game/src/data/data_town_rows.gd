class_name DataTownRows
## The trade quarter of every safe town (bh-018 redesign of bh-017's rows): Malasugue's Merchant Quarter, Olivar's Market
## Row and Wyman's Quartermaster Row. Every shopkeeper works from their own purpose-built stand — a provisioner's stall,
## a mystic's pavilion, a smithy with its forge, a stranger's wagon, a lapidary's booth, a jeweller's canopy, a field
## smith's campaign forge ... (tools/blender/environment/assets_market_*.py) — placed around a square rather than in a
## grid, fronts turned toward the street and the camera. The goods on each stand are its sign: no lettered boards, no
## sign-poles. Maps build their quarter from this table (TownRowBuilder) and NPCs read where to stand from it.
##
## Stand keys: id, kind (shop | station | shrine), npc (NpcDef id), station (crafting station id), label, model (environment
## kit asset), pos (map-local, y ignored), yaw (degrees, 0 = the stand's front faces +Z), npc_at / cust_at (the stand's
## `npc` / `customer` sockets in its own frame, x and z), title, sub (what the stand is, for lists and the world map), col.

const SHOP := "shop"
const STATION := "station"
const SHRINE := "shrine"
const VAULT := "vault"         # bh-019: the Hero's Vault (stand_vault + VaultPoint at its `use` socket)
const DUMMY := "dummy"         # bh-019: a practice dummy (PracticeDummy)
const TRADER := "trader"       # bh-019: an NPC with a stand but no shop (Lape the Ancient)

const C_GOODS := Color(0.42, 0.85, 0.45)
const C_ARMS := Color(0.95, 0.42, 0.34)
const C_ARCANA := Color(0.72, 0.5, 1.0)
const C_RARE := Color(1.0, 0.82, 0.3)
const C_JEWEL := Color(1.0, 0.55, 0.75)
const C_ALCHEMY := Color(0.4, 0.95, 0.78)
const C_BENCH := Color(0.95, 0.75, 0.42)
const C_FORGE := Color(1.0, 0.58, 0.25)
const C_SPIRIT := Color(0.55, 0.92, 1.0)
const C_CRYSTAL := Color(0.62, 0.86, 1.0)
const C_RELIC := Color(0.78, 0.62, 1.0)
const C_VAULT := Color(1.0, 0.86, 0.5)
const C_TRAIN := Color(0.95, 0.62, 0.42)

const ROWS := {
	&"sanctuary": {
		"name": "Merchant Quarter", "col": Color(1.0, 0.82, 0.45),
		"rect": Rect2(6.4, 10.5, 23.6, 23.0),
		"stands": [
			# the north side, on the edge of the plaza, fronts to the square and the camera
			{"id": &"goods", "kind": SHOP, "npc": &"tovin", "model": "stand_provisions", "pos": Vector3(9.9, 0, 13.9), "yaw": 4.0,
				"npc_at": Vector2(-0.7, -0.35), "cust_at": Vector2(-0.4, 2.2),
				"title": "Anton's Provisions", "sub": "Draughts · Scrolls · Supplies", "col": C_GOODS},
			{"id": &"arcana", "kind": SHOP, "npc": &"seris", "model": "stand_arcana", "pos": Vector3(15.9, 0, 13.6), "yaw": -8.0,
				"npc_at": Vector2(0.0, 1.3), "cust_at": Vector2(0.0, 3.0),
				"title": "Seris' Arcana", "sub": "Rings · Charms · Staves", "col": C_ARCANA},
			{"id": &"lapidary", "kind": SHOP, "npc": &"ysolde", "model": "stand_lapidary", "pos": Vector3(21.3, 0, 15.0), "yaw": -38.0,
				"npc_at": Vector2(0.3, -0.35), "cust_at": Vector2(0.2, 2.1),
				"title": "Marr's Lapidary", "sub": "Sockets · Crystals", "col": C_CRYSTAL},
			# the east side: Brannoc's smithy with the town forge
			{"id": &"arms", "kind": SHOP, "npc": &"brannoc", "model": "stand_smithy", "pos": Vector3(21.2, 0, 22.4), "yaw": -90.0,
				"npc_at": Vector2(1.6, 0.9), "cust_at": Vector2(1.2, 2.8),
				"title": "Brannoc's Smithy", "sub": "Weapons · Armour · Shields · Forge", "col": C_ARMS,
				"station": &"forge", "label": "Brannoc's Anvil (Fore-Tech)"},
			# the west side: the stranger's wagon, and the Shrine of the Fallen at the quiet end
			{"id": &"rare", "kind": SHOP, "npc": &"stranger", "model": "stand_wagon", "pos": Vector3(8.7, 0, 21.2), "yaw": 90.0,
				"npc_at": Vector2(0.9, 1.2), "cust_at": Vector2(0.4, 2.7),
				"title": "The Stranger's Wagon", "sub": "Rare wares, after the Catacombs", "col": C_RARE},
			{"id": &"shrine", "kind": SHRINE, "npc": &"veyra", "model": "", "pos": Vector3(8.9, 0, 28.8), "yaw": 70.0,
				"npc_at": Vector2(1.4, 1.55), "cust_at": Vector2(-0.9, 2.1),
				"title": "Shrine of the Fallen", "sub": "Bind fallen spirits", "col": C_SPIRIT},
			# the south end: the Alchemy Table and the Workbench, facing the square
			{"id": &"alchemy", "kind": STATION, "station": &"alchemy", "label": "Alchemy Table (Enchanting)", "model": "station_alchemy",
				"pos": Vector3(20.2, 0, 29.4), "yaw": -55.0, "cust_at": Vector2(0.0, 1.5),
				"title": "Alchemy Table", "sub": "Brew · Enchant weapons", "col": C_ALCHEMY},
			{"id": &"bench", "kind": STATION, "station": &"workbench", "label": "Workbench", "model": "station_workbench",
				"pos": Vector3(14.6, 0, 30.4), "yaw": -8.0, "cust_at": Vector2(0.0, 1.4),
				"title": "Workbench", "sub": "Bombs · Scrolls · Charms", "col": C_BENCH},
			# bh-019: past the smithy, on the east green: Lape the Ancient's reliquary, the Hero's Vault, a practice dummy
			{"id": &"lape", "kind": TRADER, "npc": &"lape", "model": "stand_lape", "pos": Vector3(27.6, 0, 15.6), "yaw": -60.0,
				"npc_at": Vector2(0.0, -0.4), "cust_at": Vector2(0.0, 1.9), "bh019": true,
				"title": "Lape's Reliquary", "sub": "Appraisal · Special-crafted trades", "col": C_RELIC},
			{"id": &"vault", "kind": VAULT, "model": "stand_vault", "pos": Vector3(28.0, 0, 22.6), "yaw": -75.0,
				"cust_at": Vector2(0.0, 1.6), "bh019": true,
				"title": "The Hero's Vault", "sub": "Storage shared by all your heroes", "col": C_VAULT},
			{"id": &"dummy", "kind": DUMMY, "model": "practice_dummy", "pos": Vector3(25.2, 0, 27.2), "yaw": -40.0,
				"cust_at": Vector2(0.0, 1.8), "bh019": true,
				"title": "Practice Dummy", "sub": "Try your damage", "col": C_TRAIN},
		],
	},
	&"olivar": {
		"name": "Market Row", "col": Color(1.0, 0.82, 0.45),
		"rect": Rect2(-19.6, 14.0, 22.2, 17.0),
		"stands": [
			{"id": &"jewels", "kind": SHOP, "npc": &"elsbeth", "model": "stand_jeweller", "pos": Vector3(-11.4, 0, 17.2), "yaw": 72.0,
				"npc_at": Vector2(-0.4, -0.3), "cust_at": Vector2(-0.2, 1.9),
				"title": "Crane's Fine Settings", "sub": "Rings · Amulets · Charms", "col": C_JEWEL},
			{"id": &"apothecary", "kind": SHOP, "npc": &"aldous", "model": "stand_apothecary", "pos": Vector3(-11.6, 0, 23.4), "yaw": 90.0,
				"npc_at": Vector2(0.6, -0.4), "cust_at": Vector2(0.4, 2.2),
				"title": "Angkol Les' Apothecary", "sub": "Herbs · Draughts · Recipes", "col": C_GOODS},
			{"id": &"alchemy", "kind": STATION, "station": &"alchemy", "label": "Angkol Les' Alchemy Table (Enchanting)", "model": "station_alchemy",
				"pos": Vector3(-10.9, 0, 29.0), "yaw": 55.0, "cust_at": Vector2(0.0, 1.5),
				"title": "Alchemy Table", "sub": "Brew · Enchant weapons", "col": C_ALCHEMY},
			# the open gem-cutter's kiosk closes the south end of the row, the square in front of it
			{"id": &"gemcutter", "kind": SHOP, "npc": &"anselm", "model": "stand_gemcutter", "pos": Vector3(-5.0, 0, 28.4), "yaw": 0.0,
				"npc_at": Vector2(0.0, 0.2), "cust_at": Vector2(0.0, 2.5),
				"title": "Cray's Cutting Room", "sub": "Sockets · Crystals", "col": C_CRYSTAL},
			{"id": &"bench", "kind": STATION, "station": &"workbench", "label": "Workbench", "model": "station_workbench",
				"pos": Vector3(0.4, 0, 15.4), "yaw": -58.0, "cust_at": Vector2(0.0, 1.4),
				"title": "Workbench", "sub": "Bombs · Scrolls · Charms", "col": C_BENCH},
			{"id": &"arms", "kind": SHOP, "npc": &"corvin", "model": "stand_armsbroker", "pos": Vector3(0.4, 0, 20.2), "yaw": -82.0,
				"npc_at": Vector2(0.6, -0.3), "cust_at": Vector2(0.4, 2.3),
				"title": "Taicho's Arms Exchange", "sub": "Advanced weapons & armour", "col": C_ARMS},
			{"id": &"forge", "kind": STATION, "station": &"forge", "label": "Trader's Forge (Fore-Tech)", "model": "station_forge",
				"pos": Vector3(0.6, 0, 26.6), "yaw": -100.0, "cust_at": Vector2(0.0, 1.6),
				"title": "Forge", "sub": "Smith · Salvage · Fore-Tech", "col": C_FORGE},
			# bh-019: on the west green by the waypoint shrine
			{"id": &"vault", "kind": VAULT, "model": "stand_vault", "pos": Vector3(-17.4, 0, 29.2), "yaw": 90.0,
				"cust_at": Vector2(0.0, 1.6), "bh019": true,
				"title": "The Hero's Vault", "sub": "Storage shared by all your heroes", "col": C_VAULT},
			{"id": &"dummy", "kind": DUMMY, "model": "practice_dummy", "pos": Vector3(-17.0, 0, 17.2), "yaw": 60.0,
				"cust_at": Vector2(0.0, 1.8), "bh019": true,
				"title": "Practice Dummy", "sub": "Try your damage", "col": C_TRAIN},
		],
	},
	&"wyman_outpost": {
		"name": "Quartermaster Row", "col": Color(1.0, 0.82, 0.45),
		"rect": Rect2(-3.0, 12.0, 20.0, 15.0),
		"stands": [
			{"id": &"supplies", "kind": SHOP, "npc": &"hobb", "model": "stand_quartermaster", "pos": Vector3(-0.6, 0, 15.6), "yaw": 78.0,
				"npc_at": Vector2(0.4, 0.2), "cust_at": Vector2(0.3, 2.5),
				"title": "Wyman Quartermaster", "sub": "Draughts · Scrolls · Materials", "col": C_GOODS},
			{"id": &"outfitter", "kind": SHOP, "npc": &"greta", "model": "stand_fieldsmith", "pos": Vector3(-0.4, 0, 22.4), "yaw": 96.0,
				"npc_at": Vector2(1.3, 0.8), "cust_at": Vector2(1.0, 2.6),
				"title": "Stonehand's Field Kit", "sub": "Weapons · Armour · Field Forge", "col": C_ARMS,
				"station": &"forge", "label": "Field Forge (Fore-Tech)"},
			{"id": &"prospector", "kind": SHOP, "npc": &"dagna", "model": "stand_crystal_cart", "pos": Vector3(8.4, 0, 15.2), "yaw": -65.0,
				"npc_at": Vector2(-0.6, -0.1), "cust_at": Vector2(-0.4, 2.0),
				"title": "Flint's Crystal Cart", "sub": "Sockets · Crystals", "col": C_CRYSTAL},
			{"id": &"kettle", "kind": STATION, "station": &"alchemy", "label": "Camp Kettle (Enchanting)", "model": "station_alchemy",
				"pos": Vector3(8.8, 0, 21.4), "yaw": -90.0, "cust_at": Vector2(0.0, 1.5),
				"title": "Camp Kettle", "sub": "Brew · Enchant weapons", "col": C_ALCHEMY},
			{"id": &"bench", "kind": STATION, "station": &"workbench", "label": "Camp Workbench", "model": "station_workbench",
				"pos": Vector3(4.6, 0, 25.6), "yaw": -10.0, "cust_at": Vector2(0.0, 1.4),
				"title": "Camp Workbench", "sub": "Bombs · Scrolls · Charms", "col": C_BENCH},
			# bh-019: on the east side of the camp
			{"id": &"vault", "kind": VAULT, "model": "stand_vault", "pos": Vector3(14.4, 0, 15.2), "yaw": -90.0,
				"cust_at": Vector2(0.0, 1.6), "bh019": true,
				"title": "The Hero's Vault", "sub": "Storage shared by all your heroes", "col": C_VAULT},
			{"id": &"dummy", "kind": DUMMY, "model": "practice_dummy", "pos": Vector3(14.2, 0, 22.2), "yaw": -60.0,
				"cust_at": Vector2(0.0, 1.8), "bh019": true,
				"title": "Practice Dummy", "sub": "Try your damage", "col": C_TRAIN},
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

## Unit vector from the stand toward its customers.
static func front(s: Dictionary) -> Vector3:
	return Vector3(0, 0, 1).rotated(Vector3.UP, deg_to_rad(float(s.yaw)))

## Unit vector along the stand's front (its local +X).
static func side(s: Dictionary) -> Vector3:
	return Vector3(1, 0, 0).rotated(Vector3.UP, deg_to_rad(float(s.yaw)))

## A point given in the stand's own frame (x across the front, z toward the customers) in map coordinates.
static func local_to_map(s: Dictionary, at: Vector2) -> Vector3:
	var p: Vector3 = s.pos + side(s) * at.x + front(s) * at.y
	return Vector3(p.x, 0, p.z)

## Where the NPC stands (at their counter, anvil, pavilion door ...) and which way it faces.
static func npc_spot(npc_id: StringName) -> Dictionary:
	var s := stand_of_npc(npc_id)
	if s.is_empty():
		return {}
	return {"position": local_to_map(s, s.get("npc_at", Vector2(0, 1))), "yaw": float(s.yaw)}

## Where a customer stands to trade at (or use) a stand.
static func customer_spot(s: Dictionary) -> Vector3:
	return local_to_map(s, s.get("cust_at", Vector2(0, 2.0)))

## Distance in metres from (x, z) to the quarter's paved rectangle (0 inside), for the terrain splat; 99 when the map has none.
static func paved_dist(map_id: StringName, x: float, z: float) -> float:
	var r: Dictionary = ROWS.get(map_id, {})
	if r.is_empty():
		return 99.0
	var rc: Rect2 = r.rect
	var dx := maxf(maxf(rc.position.x - x, x - rc.end.x), 0.0)
	var dz := maxf(maxf(rc.position.y - z, z - rc.end.y), 0.0)
	return Vector2(dx, dz).length()

## 0..1 cobble weight of the quarter at (x, z): full on the square, fading over two metres.
static func paved(map_id: StringName, x: float, z: float) -> float:
	return 1.0 - clampf((paved_dist(map_id, x, z) - 0.4) / 1.8, 0.0, 1.0)
