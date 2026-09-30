extends TestCase

func _init() -> void:
	strict = true

func test_points_rank_bounds_and_save() -> void:
	var h := Game.new_hero(&"knight", "Ranks")
	var skills := h.progress.skill_points
	var stats := h.progress.free_points
	Cheats.apply("qwe", h)
	Cheats.apply("asd", h)
	eq(h.progress.skill_points, skills + 30, "30 skill points")
	eq(h.progress.free_points, stats + 30, "30 stat points")
	ok(not Cheats.is_code("lol"), "lol is ordinary chat")
	for i in DataGuilds.MAX_RANK + 2:
		Cheats.apply("qqq", h)
	eq(h.tier, DataGuilds.MAX_RANK, "upper rank bound")
	eq(h.equipment.tier_rank, h.tier, "equipment requirements updated")
	eq(HeroData.from_dict(h.to_dict()).tier, h.tier, "rank persists without a guild")
	Cheats.apply("www", h)
	eq(h.tier, DataGuilds.MAX_RANK - 1, "exactly one lower")
	for i in DataGuilds.MAX_RANK + 2:
		Cheats.apply("www", h)
	eq(h.tier, 0, "lower rank bound")
	h.guild = &"swordfin"
	Cheats.apply("qqq", h)
	Cheats.apply("www", h)
	h.check_promotions()
	eq(h.tier, 0, "lower rank does not immediately auto-promote")
	eq(HeroData.from_dict(h.to_dict()).tier, 0, "lower rank survives loading")
	done()

func test_equipment_and_orbital_gifts_are_atomic_and_saved() -> void:
	for cls in [&"knight", &"mage", &"ranger", &"shadowblade"]:
		var h := Game.new_hero(cls, "Gifts")
		h.inventory = Inventory.new(5)
		ok(Cheats.apply("zzz", h).begins_with("Cheat: +"), "custom gift for " + String(cls))
		eq(h.inventory.free_cells(), 0, "five pieces")
		for it: ItemInstance in h.inventory.cells:
			ok(it.crafted and it.license != &"" and not it.powers.is_empty(), "crafted, licensed special effects")
			ok(it.display_name() != "", "named equipment")
			ok(ItemGenerator.class_fit(it.base, cls), "fits class")
			var copy := ItemInstance.from_dict(it.to_dict())
			eq(copy.powers, it.powers, "special effects survive save")
		var before := h.inventory.to_array()
		ok(Cheats.apply("zzz", h).contains("nothing added"), "full equipment gift rejected")
		eq(h.inventory.to_array(), before, "no partial gifts")
	var h := Game.new_hero(&"mage", "Orbs")
	h.inventory = Inventory.new(10)
	Cheats.apply("orb", h)
	var total := 0
	for it: ItemInstance in h.inventory.cells:
		if it:
			eq(DataCrystals.grade_of(it.base.id), 3, "Orbital grade")
			total += it.count
	eq(total, 10, "ten total orbitals")
	ok(h.inventory.count_of(&"bloodrift_orbital") >= 5, "five guaranteed Bloodrift")
	h.inventory = Inventory.new(1)
	var blocker := DB.make_item(&"health_potion", BH.Rarity.COMMON, 1, 1)
	h.inventory.add(blocker)
	var before := h.inventory.to_array()
	ok(Cheats.apply("orb", h).contains("nothing added"), "no orbital room")
	eq(h.inventory.to_array(), before, "no partial orbitals")
	done()

func test_host_only_and_network_chat_filter() -> void:
	var mode := Net.mode
	var peers := Net.peers
	var received: Array = []
	var record := func(peer: int, text: String) -> void: received.append([peer, text])
	Net.chat_received.connect(record)
	Net.mode = Net.Mode.CLIENT
	Net.peers = {1: {"name": "Host"}, 8: {"name": "Client"}}
	var h := Game.new_hero(&"knight", "Client")
	var before := h.to_dict()
	for code in Cheats.CODES:
		ok(Cheats.apply(code, h).contains("Only the host"), "client cannot use " + code)
	eq(h.to_dict(), before, "client data unchanged")
	Net.receive_chat(8, "qwe")
	Net.receive_chat(1, "qqq")
	Net.receive_chat(999, "spoof")
	eq(received.size(), 0, "no cheats or unknown identities on wire")
	Net.receive_chat(8, "Hi @everyone 😀")
	eq(received, [[8, "Hi @everyone 😀"]], "valid message attributed to connected peer")
	Net.mode = Net.Mode.HOST
	var sp := h.progress.skill_points
	Cheats.apply("qwe", h)
	eq(h.progress.skill_points, sp + 30, "host can cheat")
	Net.chat_received.disconnect(record)
	Net.peers = peers
	Net.mode = mode
	done()

func test_mentions_completion_and_boundaries() -> void:
	var names := ["everyone", "Alice", "Alice Smith", "Bob"]
	var c := ChatText.completion("hello @ali", 10, names)
	eq(c.names, ["Alice", "Alice Smith"], "case insensitive prefix")
	eq(ChatText.completion("mail@ali", 8, names), {}, "not an email")
	eq(ChatText.completion("@Alice ", 7, names), {}, "a completed name is not changed into a longer name")
	eq(ChatText.mention("Alice Smith"), "@\"Alice Smith\"", "spaces quoted")
	ok(ChatText.has_mention("@Alice, hello", "Alice"), "punctuation boundary")
	ok(ChatText.has_mention("Hi @\"Alice Smith\"!", "Alice Smith"), "full name")
	ok(ChatText.has_mention("@EVERYONE hello", "everyone"), "everyone case insensitive")
	ok(not ChatText.has_mention("@Alicette", "Alice"), "no prefix ping")
	ok(not ChatText.has_mention("mail@Alice.com", "Alice"), "no email ping")
	eq(ChatText.clean("a\nb\tc"), "abc", "single-line messages")
	eq(ChatText.clean("a".repeat(200)).length(), 120, "network size limit")
	done()

func test_completion_keys_emoji_and_touch_submit() -> void:
	var mode := Net.mode
	var peers := Net.peers
	Net.mode = Net.Mode.HOST
	Net.peers = {1: {"name": "Alice Smith"}, 2: {"name": "Bob"}}
	var chat := ChatBox.new()
	host.add_child(chat)
	chat.open()
	await host.get_tree().process_frame
	for code in [KEY_RIGHT, KEY_SPACE, KEY_ENTER]:
		chat._line.text = "Hi @Ali"
		chat._line.caret_column = 7
		var event := InputEventKey.new()
		event.keycode = code
		event.physical_keycode = code
		event.pressed = true
		Input.parse_input_event(event)
		await host.get_tree().process_frame
		eq(chat._line.text, "Hi @\"Alice Smith\" ", "completion key " + str(code))
		ok(chat.is_open() and chat.lines().is_empty(), "completion does not send")
	chat._line.text = "@Bo"
	chat._line.caret_column = 3
	chat._on_submit(chat._line.text)
	eq(chat._line.text, "@Bob ", "phone keyboard submit completes")
	chat._insert_emoji("👍")
	eq(chat._line.text, "@Bob 👍", "emoji inserted at caret")
	chat.free()
	Net.peers = peers
	Net.mode = mode
	done()

func test_stat_all_respects_other_pending_allocations() -> void:
	var w := CharacterWindow.new()
	var old := Game.hero
	Game.hero = Game.new_hero(&"knight", "Stats")
	host.add_child(w)
	w.refresh()
	w.hero.progress.free_points = 30
	w._change(&"str", 4)
	w._allocate_all(&"dex")
	eq(w._pending[&"str"], 4, "existing choices preserved")
	eq(w._pending[&"dex"], 26, "all remaining assigned")
	w._commit()
	eq(w.hero.progress.free_points, 0, "exact pool spent")
	eq(w.hero.progress.allocated[&"dex"], 26, "allocation committed")
	w._allocate_all(&"str")
	eq(w.hero.progress.free_points, 0, "empty pool cannot overspend")
	w.free()
	Game.hero = old
	done()
