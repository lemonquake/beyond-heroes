extends Node
## bh-041: replays the official trade's data path on real saves, without a server or a second machine.
##   godot --headless --path game res://tests/tools/trade_roundtrip_probe.tscn -- --a=<save.json> --b=<save.json> --out=<dir>
## For each pair of heroes (A offers up to 3 tradable bag items and some gold, B the same) it checks what the official
## trade compares: the live item against the confirmed save, A's wire against B's view of it, and writes the payloads
## each side would send (out/<side>_prepare.json) so server/test_service.py-style validation can run on them.

var args := {}

func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
	var out := String(args.get("out", "user://trade_roundtrip"))
	DirAccess.make_dir_recursive_absolute(out)
	var a := _load(String(args.get("a", "")))
	var b := _load(String(args.get("b", "")))
	if a.is_empty() or b.is_empty():
		print("ROUNDTRIP FAIL could not read the saves")
		get_tree().quit(1)
		return
	var ha := HeroData.from_dict(a.hero)
	var hb := HeroData.from_dict(b.hero)
	if args.has("fresh"):
		_fresh_items(ha)
		_fresh_items(hb)
	var offer_a := _offer(ha, 3, 1000)
	var offer_b := _offer(hb, 3, 500)
	print("ROUNDTRIP A offers %s, B offers %s" % [TradeRules.describe(offer_a), TradeRules.describe(offer_b)])
	var idem := 0
	for h in [ha, hb]:
		for c in h.inventory.cells:
			if c != null and not _same(c.to_dict(), ItemInstance.from_dict(c.to_dict()).to_dict()):
				idem += 1
				if idem <= 4:
					print("ROUNDTRIP not idempotent: %s\n  live %s\n  back %s" % [c.base.id, JSON.stringify(c.to_dict(), "", true), JSON.stringify(ItemInstance.from_dict(c.to_dict()).to_dict(), "", true)])
	print("ROUNDTRIP items whose to_dict changes after from_dict: %d" % idem)
	var sides := [["a", ha, offer_a, offer_b], ["b", hb, offer_b, offer_a]]
	for s in sides:
		var hero: HeroData = s[1]
		var mine: Dictionary = s[2]
		var other: Dictionary = s[3]
		# what the client would have as its confirmed save after flush (binary copy of the hero it just sent)
		var confirmed: Dictionary = bytes_to_var(var_to_bytes({"version": SaveSystem.CURRENT_VERSION, "hero": hero.to_dict()}))
		var stored := JSON.stringify(confirmed)
		var mine_wire := TradeRules.to_wire(mine)
		# the other machine's view of my offer, as it arrives over the network and is read back
		var seen_by_other := TradeRules.to_wire(TradeRules.read_incoming(bytes_to_var(var_to_bytes(TradeRules.to_wire(other)))))
		var theirs_wire := seen_by_other
		var trial := HeroData.from_dict(confirmed.hero)
		var miss := 0
		var used := {}
		for raw: Dictionary in mine_wire.items:
			var found := false
			for i in trial.inventory.cells.size():
				var it: ItemInstance = trial.inventory.cells[i]
				if it and not used.has(i) and it.to_dict() == raw:
					used[i] = true
					found = true
					break
			if not found:
				miss += 1
		print("ROUNDTRIP side %s: offered items not found in the confirmed save by to_dict(): %d of %d" % [s[0], miss, mine_wire.items.size()])
		var wire_same := JSON.stringify(TradeRules.to_wire(other), "", true) == JSON.stringify(seen_by_other, "", true)
		print("ROUNDTRIP side %s: the other's offer reads back identically: %s" % [s[0], wire_same])
		var f := FileAccess.open(out.path_join("%s_case.json" % s[0]), FileAccess.WRITE)
		f.store_string(JSON.stringify({"stored": JSON.parse_string(stored), "mine": mine_wire, "theirs": theirs_wire,
			"other_mine": TradeRules.to_wire(other)}))
		f.close()
	get_tree().quit(0)

func _load(path: String) -> Dictionary:
	var t := FileAccess.get_file_as_string(path)
	var d = JSON.parse_string(t)
	return d if d is Dictionary and d.has("hero") else {}

## Replace the bag's front with items made this session (drops, Ascendant drops, Lape crafts, socketed), as a live hero
## carries them before any reload.
func _fresh_items(h: HeroData) -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = 41
	var made := []
	for r in range(BH.Rarity.BASIC, BH.Rarity.AETHER + 1):
		var b := ItemGenerator.random_base(rng, 60, [&"weapon", &"armor", &"helm", &"gloves", &"accessory"], &"", 1.0)
		if b:
			var it := ItemGenerator.generate(b, 60, r, rng)
			if it.sockets > 0:
				for g in DB.item_bases.values():
					if DataCrystals.is_crystal(g.id):
						it.gems[0] = String(g.id)
						break
			made.append(it)
	for r in [BH.Rarity.COSMIC, BH.Rarity.PRIMORDIAL]:
		var it = DataAscendant.roll_drop(110, false, &"knight", 0.0, rng, r)
		if it:
			made.append(it)
	var lape := LapeTrade.make_offers(h, BH.Rarity.LEGENDARY, 60, rng)
	made.append_array(lape)
	for i in made.size():
		h.inventory.cells[i] = made[i]
	print("ROUNDTRIP fresh items placed: %d" % made.size())

func _offer(h: HeroData, n: int, gold: int) -> Dictionary:
	var items := []
	for i in h.inventory.bag_capacity:
		var it: ItemInstance = h.inventory.cells[i]
		if it != null and TradeRules.item_error(it) == "" and it.is_equipment():
			items.append(it)
			if items.size() >= n:
				break
	return {"gold": mini(gold, h.inventory.gold), "items": items}

func _same(x: Dictionary, y: Dictionary) -> bool:
	return JSON.stringify(x, "", true) == JSON.stringify(y, "", true) and x == y
