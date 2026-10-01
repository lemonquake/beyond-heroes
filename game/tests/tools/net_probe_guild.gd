extends Node
## Two-machine probe for bh-027's guilds over the network. Run two copies on one PC (hidden save slots only):
##   godot --headless --path game res://tests/tools/net_probe_guild.tscn -- --role=host --class=knight --slot=94 --map=sanctuary
##   godot --headless --path game res://tests/tools/net_probe_guild.tscn -- --role=join --class=mage --slot=93 --map=sanctuary
## Checks (GUILD[role] ok/FAIL lines): the host's guild and banner reach the client's profile list; an invitation is
## accepted and the client becomes a Sworn Hero with the guild's banner and passives; a passive the Guildmaster trains
## reaches the member; a whisper arrives privately; a Showcase opens on both machines with both heroes' gear; a Call to
## Arms fighter is seen on the other machine under the guild's name; a dismissed member leaves the guild.

var args := {}
var role := "host"
var fails: Array = []

func _ready() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
	role = String(args.get("role", "host"))
	add_child(load("res://src/main.tscn").instantiate())
	_run.call_deferred()

func _check(label: String, ok: bool) -> void:
	print("GUILD[%s] %s %s" % [role, "ok  " if ok else "FAIL", label])
	if not ok:
		fails.append(label)

func _wait(sec: float) -> void:
	await get_tree().create_timer(sec).timeout

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
	var h := Game.hero
	h.progress.add_xp(XpCurve.total_xp_for_level(20))
	h.inventory.gold = 200000
	h.guild = &""
	h.own_guild = {}
	h.remote_guild = {}
	if role == "host":
		await _host()
	else:
		await _client()
	print("GUILD[%s] %s" % [role, "PASS" if fails.is_empty() else "FAIL (%d)" % fails.size()])
	get_tree().quit(0 if fails.is_empty() else 1)

func _client_id() -> int:
	for id in Net.peers:
		if int(id) != 1:
			return int(id)
	return 0

func _yes_when(title: String, limit := 25.0) -> bool:
	var got := await _until(func() -> bool: return Game.ui_root.confirm.visible and Game.ui_root.confirm._title.text == title, limit)
	if got:
		Game.ui_root.confirm._confirm()
	return got

func _host() -> void:
	var h := Game.hero
	_check("founded a guild", OwnGuild.found(h, "The Golden Keys", "One shield, many hands.", "Open to every hero.", {"crest": "key", "field": "804d14"}) == "")
	var img := GuildBannerArt.paint({"crest": "key", "field": "804d14", "metal": 0, "division": "pale"})
	_check("uploaded a banner picture", GuildRules.set_banner(h, img) == "")
	for i in 2:
		OwnGuild.recruit(h)
	_check("hosted (%s)" % Net.host_game(), Net.is_host())
	await _until(func() -> bool: return Net.player_count() >= 2, 40.0)
	var cid := _client_id()
	_check("the client joined", cid != 0)
	await _wait(4.0)
	_check("invite error is empty: '%s'" % Net.guild_invite_error(cid), Net.guild_invite_error(cid) == "")
	Net.guild_invite(cid)
	var joined := await _until(func() -> bool: return OwnGuild.has_player_member(h, String(Net.peers.get(cid, {}).get("name", ""))), 25.0)
	_check("the client accepted and is a Sworn Hero here", joined)
	var prof := await _until(func() -> bool: return String(Net.peers.get(cid, {}).get("guild", {}).get("key", "")) == OwnGuild.key(h), 15.0)
	_check("the client's profile now carries our guild", prof)
	await _wait(1.0)
	OwnGuild.add_renown(h, 2000.0)
	_check("trained Sharpened Steel", OwnGuild.upgrade(h, &"sharpened_steel") == "")
	await _wait(3.0)
	Net.whisper(cid, "psst, the board has a champion hunt")
	# the client asks for a Showcase: say yes
	var asked := await _yes_when("Showcase", 30.0)
	_check("a Showcase request arrived and was accepted", asked)
	var shown := await _until(func() -> bool: return Game.ui_root.window(&"showcase").visible, 15.0)
	_check("the Showcase opened here", shown)
	var sw := Game.ui_root.window(&"showcase") as ShowcaseWindow
	_check("it shows the client's guild", String(sw._theirs.get("guild", {}).get("name", "")) == "The Golden Keys")
	Game.ui_root.close_all()
	# Call to Arms: the client should see the fighter
	var res := GuildSummons.call_to_arms(h, Game.player as Node3D)
	_check("Call to Arms (%s)" % res.text, res.ok)
	await _wait(8.0)
	# dismiss the client
	for m in OwnGuild.members(h):
		if String(m.kind) == "player":
			_check("dismissed the client", OwnGuild.kick(h, int(m.id)) == "")
	await _wait(8.0)
	Net.leave()

func _client() -> void:
	var h := Game.hero
	await _wait(3.0)
	Net.join_game(NetCodec.room_code("127.0.0.1", Net.PORT, Net.PORT))
	await _until(func() -> bool: return Net.is_client() and not Net.connecting and not Net.following and not Game.travelling, 40.0)
	await _wait(2.0)
	var host_guild := await _until(func() -> bool: return String(Net.peers.get(1, {}).get("guild", {}).get("name", "")) == "The Golden Keys", 20.0)
	_check("the host's guild is in their profile", host_guild)
	var banner := await _until(func() -> bool: return Net.guild_banners.size() > 0, 20.0)
	_check("the host's banner picture arrived", banner)
	var invited := await _yes_when("Guild Invitation", 30.0)
	_check("the invitation arrived and was accepted", invited)
	var joined := await _until(func() -> bool: return h.guild == GuildRegistry.REMOTE, 20.0)
	_check("joined: a member of %s" % GuildRules.display_name(h), joined and GuildRules.display_name(h) == "The Golden Keys")
	_check("with the guild's banner", not (h.remote_guild.get("banner", PackedByteArray()) as PackedByteArray).is_empty())
	_check("and its info", String(h.remote_guild.get("info", "")) == "Open to every hero.")
	var synced := await _until(func() -> bool: return int(GuildRules.passive_ranks(h).get("sharpened_steel", 0)) == 1, 25.0)
	_check("the Guildmaster's new passive reached us", synced)
	_check("and applies to us", GuildRules.modifiers(h).any(func(m): return m.source == "Golden Keys"))
	var whispered := await _until(func() -> bool: return Array(Game.ui_root.chat.lines()).any(func(l): return String(l).begins_with("[From ") and String(l).contains("champion hunt")), 20.0)
	_check("the whisper arrived", whispered)
	await _wait(1.0)
	Net.request_showcase(1)
	var shown := await _until(func() -> bool: return Game.ui_root.window(&"showcase").visible, 30.0)
	_check("the Showcase opened here", shown)
	var sw := Game.ui_root.window(&"showcase") as ShowcaseWindow
	_check("with the host's gear", (sw._theirs.get("equipment", {}) as Dictionary).has("main_weapon") and String(sw._theirs.get("name", "")) != "")
	Game.ui_root.close_all()
	var fighter := await _until(func() -> bool: return Net.avatars().any(func(a): return (a as NetAvatar).guild_tag != ""), 30.0)
	_check("the host's Call to Arms fighter is here, under the guild's name", fighter)
	var kicked := await _until(func() -> bool: return h.guild == &"", 30.0)
	_check("dismissed: no longer in the guild", kicked)
	await _wait(3.0)
