extends TestCase
## The chat box (Enter) and its cheat codes: lemonq (+5000 gold), azrin (+3 levels), azrael (full HP and mana).

var _holder: Node3D
var _saved := {}
var _player: Player

func _init() -> void:
	strict = true

func _begin() -> void:
	_saved = {"parent": Game.world_parent, "player": Game.player, "map": Game.current_map, "map_id": Game.current_map_id,
		"hero": Game.hero, "fx_world": FX.world if is_instance_valid(FX.world) else null}
	_holder = Node3D.new()
	_holder.name = "ChatTestWorld"
	host.add_child(_holder)
	Game.world_parent = _holder
	Game.current_map = null
	Game.hero = Game.new_hero(&"knight", "Chatter")
	_player = Player.new()
	_player.name = "Player"
	Game.player = _player
	Game.load_map(&"sanctuary", &"waypoint")
	_player.bind(Game.hero)
	await host.get_tree().physics_frame

func _end() -> void:
	for t in TempoParty.actors(host.get_tree()):
		t.free()
	if Game.current_map and is_instance_valid(Game.current_map):
		Game.current_map.free()
	if is_instance_valid(_holder):
		_holder.free()
	Game.world_parent = _saved.parent
	Game.player = _saved.player
	Game.current_map = _saved.map
	Game.current_map_id = _saved.map_id
	Game.hero = _saved.hero
	FX.world = _saved.fx_world if is_instance_valid(_saved.fx_world) else null

# ------------------------------------------------------------------------------------------------------------

func test_enter_opens_chat() -> void:
	ok(InputMap.has_action(&"chat"), "input action 'chat' exists")
	var keys := InputMap.action_get_events(&"chat").filter(func(e): return e is InputEventKey).map(func(e): return e.physical_keycode)
	ok(keys.has(KEY_ENTER), "Enter opens the chat")
	done()

func test_codes_are_recognised() -> void:
	for c in ["lemonq", "LEMONQ", "  azrin ", "Azrael", "taicho", "Greg"]:
		ok(Cheats.is_code(c), "'%s' is a code" % c)
	for c in ["", "lemon", "lemonqq", "azrin now", "hello"]:
		ok(not Cheats.is_code(c), "'%s' is not a code" % c)
	eq(Cheats.apply("hello", Game.new_hero(&"knight", "X")), "", "plain text does nothing")
	done()

func test_lemonq_gives_gold() -> void:
	var h := Game.new_hero(&"mage", "Gold")
	var g0 := h.inventory.gold
	ok(Cheats.apply("lemonq", h).begins_with("Cheat:"), "reports the cheat")
	eq(h.inventory.gold, g0 + 5000, "+5000 gold")
	Cheats.apply("LemonQ", h)
	eq(h.inventory.gold, g0 + 10000, "works again, any case")
	done()

func test_taicho_and_greg_give_1000_gold() -> void:
	var h := Game.new_hero(&"mage", "Gold")
	var g0 := h.inventory.gold
	ok(Cheats.apply("taicho", h).begins_with("Cheat:"), "taicho reports the cheat")
	eq(h.inventory.gold, g0 + 1000, "taicho: +1000 gold")
	Cheats.apply("GREG", h)
	eq(h.inventory.gold, g0 + 2000, "greg: +1000 gold, any case")
	done()

func test_new_hero_starts_with_five_town_portals() -> void:
	var h := Game.new_hero(&"knight", "Portal")
	eq(h.inventory.count_of(&"town_portal"), 5, "5 free Town Portals")
	done()

func test_azrin_levels_up_three() -> void:
	var h := Game.new_hero(&"knight", "Lvl")
	var pr := h.progress
	var fp := pr.free_points
	var sp := pr.skill_points
	Cheats.apply("azrin", h)
	eq(pr.level, 4, "level 1 -> 4")
	eq(pr.xp, 0, "starts the new level at 0 xp")
	eq(pr.free_points, fp + 3 * h.cls.free_points_per_level, "attribute points for three levels")
	eq(pr.skill_points, sp + 3 * h.cls.skill_points_per_level, "skill points for three levels")
	pr.add_xp(50)
	Cheats.apply("azrin", h)
	eq(pr.level, 7, "level 4 -> 7 even mid-level")
	# near and at the cap
	pr.add_xp(XpCurve.total_xp_for_level(BH.LEVEL_CAP - 1) - XpCurve.total_xp_for_level(pr.level) - pr.xp)
	eq(pr.level, BH.LEVEL_CAP - 1, "set up one below the cap")
	Cheats.apply("azrin", h)
	eq(pr.level, BH.LEVEL_CAP, "stops at the cap")
	ok(Cheats.apply("azrin", h).contains("cap"), "at the cap it says so")
	eq(pr.level, BH.LEVEL_CAP, "and changes nothing")
	done()

func test_azrael_restores_hp_and_mana() -> void:
	await _begin()
	_player.ensure_stats()
	_player.hp = 5.0
	_player.mana = 0.0
	ok(Cheats.apply("azrael", Game.hero, _player).begins_with("Cheat:"), "reports the cheat")
	near(_player.hp, _player.max_hp(), 0.01, "HP full")
	near(_player.mana, _player.max_mana(), 0.01, "mana full")
	_player.alive = false
	_player.hp = 0.0
	Cheats.apply("azrael", Game.hero, _player)
	eq(_player.hp, 0.0, "does not raise the dead")
	_player.alive = true
	_end()
	done()

func test_chat_box_says_and_cheats() -> void:
	await _begin()
	var chat := ChatBox.new()
	host.add_child(chat)
	ok(not chat.is_open(), "starts closed")
	chat.open()
	ok(chat.is_open(), "opens")
	chat.submit("Hello, Malasugue!")
	eq(chat.lines()[-1], "[Chatter] Hello, Malasugue!", "a message is said under the hero's name")
	var g0 := Game.hero.inventory.gold
	chat.submit("lemonq")
	eq(Game.hero.inventory.gold, g0 + 5000, "the chat applies cheat codes")
	ok(chat.lines()[-1].begins_with("Cheat:") and not chat.lines()[-1].contains("lemonq"), "the code is not echoed")
	var lvl := Game.hero.progress.level
	chat.submit("azrin")
	eq(Game.hero.progress.level, lvl + 3, "azrin through the chat")
	_player.hp = 1.0
	chat.submit("azrael")
	near(_player.hp, _player.max_hp(), 0.01, "azrael through the chat")
	var n := chat.lines().size()
	chat.submit("   ")
	eq(chat.lines().size(), n, "blank messages are ignored")
	for i in 20:
		chat.submit("line %d" % i)
	eq(chat.lines().size(), ChatBox.MAX_LINES, "the log keeps the last %d lines" % ChatBox.MAX_LINES)
	chat.close()
	ok(not chat.is_open(), "closes")
	chat.free()
	_end()
	done()
