extends Node
## Two-machine probe for bh-016's player trade. Run two copies on one PC (hidden save slots only):
##   godot --path game --resolution 1280x720 res://tests/tools/net_probe_trade.tscn -- --role=host --class=knight --slot=94 --map=sanctuary --out=<dir>
##   godot --path game --resolution 1280x720 res://tests/tools/net_probe_trade.tscn -- --role=join --class=ranger --slot=93 --map=sanctuary --out=<dir>
## Checks (TRADE[role] ok/FAIL lines):
##   clicking an ally picks them (the ray through their screen position finds the avatar); the Trade Request prompt names them;
##   the request reaches them and Accept opens the trade table on both machines; offers show on the other side; changing
##   an offer clears an acceptance; both accept -> gold and items swap on both heroes and both windows close;
##   a declined request opens nothing; a trade cancelled from one side closes on the other.

var args := {}
var role := "host"
var out := ""
var fails: Array = []

const HOST_GOLD := 500
const JOIN_GOLD := 100

var _mine: ItemInstance

func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
	role = String(args.get("role", "host"))
	out = String(args.get("out", ProjectSettings.globalize_path("res://").path_join("../work/probe/trade")))
	DirAccess.make_dir_recursive_absolute(out)
	add_child(load("res://src/main.tscn").instantiate())
	_run.call_deferred()

func _check(label: String, ok: bool) -> void:
	print("TRADE[%s] %s %s" % [role, "ok  " if ok else "FAIL", label])
	if not ok:
		fails.append(label)

func _wait(sec: float) -> void:
	await get_tree().create_timer(sec).timeout

func _shot(label: String) -> void:
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(out.path_join("%s_%s.png" % [role, label]))

## Wait (up to `limit` s) for a condition.
func _until(cond: Callable, limit := 30.0) -> bool:
	var t := 0.0
	while t < limit:
		if cond.call():
			return true
		await _wait(0.1)
		t += 0.1
	return false

func _run() -> void:
	for i in 400:
		if Game.in_session and Game.player is Player and not Game.travelling:
			break
		await _wait(0.1)
	await _wait(1.0)
	Game.god_mode = true
	# a known bag and purse: one unique tradable item each
	var h := Game.hero
	h.inventory.cells.fill(null)
	h.inventory.gold = HOST_GOLD if role == "host" else JOIN_GOLD
	var mine := DB.make_item(&"health_potion" if role == "host" else &"mana_potion", BH.Rarity.COMMON, 1, 11)
	mine.count = 3
	h.inventory.add(mine)
	_mine = mine
	h.inventory.changed.emit()
	if role == "host":
		await _host()
	else:
		await _client()
	print("TRADE[%s] %s" % [role, "PASS" if fails.is_empty() else "FAIL (%d)" % fails.size()])
	get_tree().quit(0 if fails.is_empty() else 1)

func _client_id() -> int:
	for id in Net.peers:
		if int(id) != 1:
			return int(id)
	return 0

func _auto_answer(go: bool) -> bool:
	# the prompt on the receiving machine: answer it like a click on Accept / Decline
	var got := await _until(func() -> bool: return not Net._trade_incoming.is_empty() and Game.ui_root.request_box.visible, 20.0)
	if not got:
		return false
	await _shot("request_prompt")
	if go:
		Game.ui_root.request_box._confirm()
	else:
		Game.ui_root.request_box.cancel()
	return true

func _host() -> void:
	var err := Net.host_game(int(args.get("port", Net.PORT)))
	_check("hosted (%s)" % err, err == "")
	await _until(func() -> bool: return Net.player_count() >= 2 and Net.avatars().size() > 0, 40.0)
	var cid := _client_id()
	_check("the client joined", cid != 0)
	await _wait(4.0)
	# 1. clicking the ally picks them
	var av := Net.avatar(cid)
	_check("the client's avatar is here", av != null)
	if av:
		var p := Game.player as Player
		var cam := p.camera
		var sp := cam.unproject_position(av.center())
		var vp := get_viewport().get_visible_rect().size
		_check("the avatar is on screen at %s" % sp, Rect2(Vector2.ZERO, vp).has_point(sp))
		var from := cam.project_ray_origin(sp)
		var dir := cam.project_ray_normal(sp)
		var hit = p._ally_under_cursor(from, dir)
		_check("a click on the ally picks the ally", hit == av)
		var far := cam.unproject_position(av.center() + Vector3(6, 0, 0))
		_check("a click beside them picks nobody", p._ally_under_cursor(cam.project_ray_origin(far), cam.project_ray_normal(far)) == null)
	# 2. the prompt
	Net.trade_prompt(cid)
	var asked := await _until(func() -> bool: return Game.ui_root.confirm.visible and Game.ui_root.confirm._title.text == "Trade", 5.0)
	_check("clicking an ally asks 'Send a Trade Request?': '%s'" % (Game.ui_root.confirm._text.text if asked else ""), asked)
	await _shot("send_prompt")
	Game.ui_root.confirm._confirm()
	_check("the request is out", Net.in_trade() and Net.trade.phase == "asking")
	# the client declines the first request
	var closed := await _until(func() -> bool: return not Net.in_trade(), 25.0)
	_check("a declined request opens nothing", closed and not Game.ui_root.window(&"trade").visible)
	await _wait(3.5)
	# 3. a second request, accepted
	Net.trade_prompt(cid)
	await _wait(0.3)
	Game.ui_root.confirm._confirm()
	var opened := await _until(func() -> bool: return Net.in_trade() and Net.trade.phase == "open" and Game.ui_root.window(&"trade").visible, 25.0)
	_check("accepted: the trade table is open", opened)
	await _wait(1.0)
	# potions fill the belt first since the belt got its own cells (bh-030), so take the stack wherever it went
	var bag_item: ItemInstance = Game.hero.inventory.cells[Game.hero.inventory.index_of(_mine)]
	_check("offer 100 gold and the potions", Net.trade_set_offer(100, [bag_item]) == "")
	await _wait(0.5)
	await _shot("host_offer")
	# the client has offered by now
	var theirs := await _until(func() -> bool: return int(Net.trade.theirs.gold) == 30 and Net.trade.theirs.items.size() == 1, 25.0)
	_check("the client's offer (30 gold + a stack) shows here", theirs)
	Net.trade_accept(true)
	_check("accepted here: waiting for them", Net.trade.my_ok and not Net.trade.their_ok)
	# the client changes its mind (adds 5 gold): our acceptance clears
	var cleared := await _until(func() -> bool: return int(Net.trade.theirs.gold) == 35 and not Net.trade.my_ok, 25.0)
	_check("a changed offer clears our acceptance", cleared)
	await _shot("host_offer_changed")
	Net.trade_accept(true)
	var done := await _until(func() -> bool: return not Net.in_trade(), 25.0)
	_check("both accepted: the trade closed", done)
	await _wait(1.0)
	var hh := Game.hero
	_check("gold: %d -> %d gave 100 got 35" % [HOST_GOLD, hh.inventory.gold], hh.inventory.gold == HOST_GOLD - 100 + 35)
	_check("the potions left, the client's mana potions arrived (%d / %d)" % [hh.inventory.count_of(&"health_potion"), hh.inventory.count_of(&"mana_potion")],
		hh.inventory.count_of(&"health_potion") == 0 and hh.inventory.count_of(&"mana_potion") == 3)
	_check("the trade window closed", not Game.ui_root.window(&"trade").visible)
	await _shot("host_after")
	# 4. cancel from the client's side closes here too
	Net.trade_prompt(cid)
	await _wait(0.3)
	Game.ui_root.confirm._confirm()
	var open2 := await _until(func() -> bool: return Net.in_trade() and Net.trade.phase == "open", 25.0)
	_check("a third trade opens", open2)
	var gone := await _until(func() -> bool: return not Net.in_trade(), 30.0)
	await _wait(0.5)
	_check("the client cancelled: it closed here too", gone and not Game.ui_root.window(&"trade").visible)
	await _wait(3.0)
	Net.leave()

func _client() -> void:
	await _wait(3.0)
	var err := Net.join_game("127.0.0.1", int(args.get("port", Net.PORT)))
	_check("join sent (%s)" % err, err == "")
	await _until(func() -> bool: return Net.is_client() and not Net.connecting and not Net.following and not Game.travelling, 40.0)
	await _wait(5.0)
	# 1. decline the first request
	var got := await _auto_answer(false)
	_check("the first request arrived and was declined", got)
	await _wait(1.0)
	_check("nothing open after declining", not Net.in_trade())
	# 2. accept the second
	var got2 := await _auto_answer(true)
	_check("the second request arrived and was accepted", got2)
	var opened := await _until(func() -> bool: return Net.in_trade() and Net.trade.phase == "open" and Game.ui_root.window(&"trade").visible, 15.0)
	_check("the trade table is open here too", opened)
	# wait for the host's offer, then answer with ours
	var seen := await _until(func() -> bool: return int(Net.trade.theirs.gold) == 100 and Net.trade.theirs.items.size() == 1, 25.0)
	_check("the host's offer (100 gold + a stack) shows here", seen)
	var bag_item: ItemInstance = Game.hero.inventory.cells[Game.hero.inventory.index_of(_mine)]
	_check("offer 30 gold and the mana potions", Net.trade_set_offer(30, [bag_item]) == "")
	await _wait(1.0)
	await _shot("client_table")
	# the host accepts, then we change our mind by 5 gold; both acceptances clear
	var host_ok := await _until(func() -> bool: return Net.trade.their_ok, 25.0)
	_check("the host accepted", host_ok)
	_check("raise our gold offer by 5", Net.trade_set_offer(35, [bag_item]) == "")
	_check("both acceptances cleared", not Net.trade.my_ok and not Net.trade.their_ok)
	await _wait(0.5)
	Net.trade_accept(true)
	var done := await _until(func() -> bool: return not Net.in_trade(), 30.0)
	_check("both accepted: the trade closed", done)
	await _wait(1.0)
	var hh := Game.hero
	_check("gold: %d -> %d gave 35 got 100" % [JOIN_GOLD, hh.inventory.gold], hh.inventory.gold == JOIN_GOLD - 35 + 100)
	_check("the mana potions left, the host's health potions arrived (%d / %d)" % [hh.inventory.count_of(&"mana_potion"), hh.inventory.count_of(&"health_potion")],
		hh.inventory.count_of(&"mana_potion") == 0 and hh.inventory.count_of(&"health_potion") == 3)
	# 3. a third trade: accept it, then cancel
	var got3 := await _auto_answer(true)
	_check("the third request arrived", got3)
	await _until(func() -> bool: return Net.in_trade() and Net.trade.phase == "open", 15.0)
	await _wait(1.5)
	Game.ui_root.window(&"trade").close_window()
	await _wait(1.0)
	_check("closing the window cancelled the trade", not Net.in_trade())
	await _wait(4.0)
