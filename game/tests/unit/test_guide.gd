extends TestCase
## The new-game guide (bh-005): Tobren's introduction (DataGuide) — graph integrity, live key names, both ways through
## it, the one-time trigger on a new game — and the Field Guide window (H).

func _init() -> void:
	strict = true

## Every node the guide can reach, every {key:action} it quotes.
func test_graph_is_consistent() -> void:
	var def := DataGuide.intro()
	eq(def.id, DataGuide.ID, "guide id")
	eq(def.display_name, String(DataTempos.STARTER.name), "spoken by the starter Tempo")
	ok(ResourceLoader.exists(def.portrait), "portrait exists (%s)" % def.portrait)
	var nodes: Dictionary = def.graph.nodes
	for e in def.graph.entries:
		ok(nodes.has(e[1]), "entry %s exists" % e[1])
	var ends_with_flag := 0
	var keys := {}
	for id in nodes:
		var n: Dictionary = nodes[id]
		var targets := []
		if n.has("next"):
			targets.append(n.next)
		for c in n.get("choices", []):
			targets.append(c.next)
			for a in c.get("actions", []):
				if a.get("set_flag", "") == String(DataGuide.DONE_FLAG):
					ends_with_flag += 1
		for t in targets:
			ok(t == "end" or nodes.has(t), "%s -> %s resolves" % [id, t])
		var lines = n.get("text", [])
		for line in (lines if lines is Array else [lines]):
			var at := String(line).find("{key:")
			while at >= 0:
				var close := String(line).find("}", at)
				keys[String(line).substr(at + 5, close - at - 5)] = true
				at = String(line).find("{key:", close)
	eq(ends_with_flag, 2, "both ways through end by marking the guide as heard")
	for k in keys:
		ok(InputMap.has_action(StringName(k)), "{key:%s} is a real input action" % k)
		ok(Settings.binding_text(StringName(k)) != "", "{key:%s} is bound" % k)
	for must in ["tempos", "primary", "dodge", "skill_1", "potion_health", "interact", "inventory", "world_map", "guide"]:
		ok(keys.has(must), "the guide teaches {key:%s}" % must)
	ok(InputMap.has_action(&"guide"), "input action 'guide' exists")
	var hk := InputMap.action_get_events(&"guide").filter(func(e): return e is InputEventKey).map(func(e): return e.physical_keycode)
	ok(hk.has(KEY_H), "H opens the Field Guide")
	ok(UIRoot.HOTKEYS.has(&"guide"), "the UI routes the hotkey")
	done()

## {key:x} always quotes the live binding.
func test_key_placeholders_follow_rebinding() -> void:
	var before := Dialogue.fill_keys("Press {key:tempos} for Tempos")
	eq(before, "Press %s for Tempos" % Settings.binding_text(&"tempos"), "filled with the current key")
	ok(not "{" in before, "no placeholder left")
	var saved := InputMap.action_get_events(&"tempos")
	InputMap.action_erase_events(&"tempos")
	var k := InputEventKey.new()
	k.physical_keycode = KEY_P
	InputMap.action_add_event(&"tempos", k)
	eq(Dialogue.fill_keys("{key:tempos}"), Settings.binding_text(&"tempos"), "rebinding changes the text")
	ok(Dialogue.fill_keys("{key:tempos}") != before.get_slice(" ", 1), "and it is the new key")
	InputMap.action_erase_events(&"tempos")
	for e in saved:
		InputMap.action_add_event(&"tempos", e)
	eq(Dialogue.fill_keys("{key:no_such_action}"), "No Such Action", "an unknown action degrades to its name")
	var h := Game.new_hero(&"knight", "Keys")
	ok(not "{" in Dialogue.fill("{hero} presses {key:dodge}", h), "fill() handles keys and hero placeholders together")
	done()

func _walk(s: DialogueSession, picks: Array) -> Array:
	var seen := []
	s.line_shown.connect(func(_sp, _p, bb, _i, _c): seen.append(bb))
	s.begin()
	var guard := 0
	while not s.finished and guard < 200:
		guard += 1
		if not s.choices.is_empty() and s.line_index >= s.lines.size() - 1:
			s.choose(picks.pop_front() if not picks.is_empty() else 0)
		else:
			s.advance()
	return seen

func test_full_walkthrough() -> void:
	var h := Game.new_hero(&"knight", "Newcomer")
	TempoRules.grant_starter(h)
	var s := DialogueSession.start(DataGuide.intro(), h)
	var seen := _walk(s, [0, 0])
	ok(s.finished, "the conversation ends")
	ok(bool(h.world_flags.get(DataGuide.DONE_FLAG, false)), "the guide is marked as heard")
	var all := "\n".join(seen)
	ok(all.contains("Newcomer"), "addresses the hero by name")
	for word in ["Tempo", "Veyra Ashgrave", "Shrine of the Fallen", "grades", "renowned", "two", "Field Guide", "Elder Maelis"]:
		ok(all.contains(word), "explains: %s" % word)
	ok(not all.contains("{"), "no raw placeholder reaches the screen")
	ok(seen.size() >= 14, "the long way covers every lesson (%d lines)" % seen.size())
	done()

func test_short_walkthrough() -> void:
	var h := Game.new_hero(&"mage", "Veteran")
	var s := DialogueSession.start(DataGuide.intro(), h)
	var seen := _walk(s, [1, 0])
	ok(s.finished and bool(h.world_flags.get(DataGuide.DONE_FLAG, false)), "the short way ends and marks the guide as heard")
	ok(seen.size() <= 6, "and is short (%d lines)" % seen.size())
	var all := "\n".join(seen)
	for word in ["Veyra Ashgrave", "Field Guide", Settings.binding_text(&"dodge")]:
		ok(all.contains(word), "still mentions %s" % word)
	done()

## A new game opens the guide once; a hero who has heard it never gets it again.
func test_opens_once_per_hero() -> void:
	var saved_hero := Game.hero
	var saved_ui = Game.ui_root
	var ui := UIRoot.new()
	host.add_child(ui)
	var saved_session := Game.in_session
	Game.hero = Game.new_hero(&"knight", "Once")
	TempoRules.grant_starter(Game.hero)
	Game.open_intro()
	ok(ui.dialogue.visible, "the guide opens for a new hero")
	ok(ui.dialogue.session != null and ui.dialogue.session.npc.id == DataGuide.ID, "it is Tobren's introduction")
	eq(ui.dialogue._name.text, String(DataTempos.STARTER.name), "spoken by Tobren")
	ui.dialogue.close()
	ok(not ui.dialogue.visible, "closed")
	Game.hero.world_flags[DataGuide.DONE_FLAG] = true
	Game.open_intro()
	ok(not ui.dialogue.visible, "not again once heard")
	# the Field Guide can replay it and shows every control
	var gw := ui.window(&"guide") as GuideWindow
	ok(gw != null, "the Field Guide window exists")
	ui.open(&"guide")
	ok(gw.visible, "it opens")
	for p in 3:
		gw._tabs.current_tab = p
		ok(gw._content.get_child_count() > 0, "page %d has content" % p)
	gw._replay()
	for i in 40:
		await host.get_tree().process_frame
	ok(ui.dialogue.visible, "it replays the introduction")
	ok(not gw.visible, "and gets out of the way")
	ui.dialogue.close()
	for group in GuideWindow.CONTROLS:
		for row in group[1]:
			for a in row[0]:
				ok(InputMap.has_action(StringName(a)), "Field Guide action %s exists" % a)
	Game.ui_root = saved_ui
	Game.hero = saved_hero
	Game.in_session = saved_session
	ui.free()
	done()
