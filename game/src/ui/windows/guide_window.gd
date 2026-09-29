class_name GuideWindow
extends UIWindow
## The Field Guide (H): every control with the key currently bound to it, how Tempos work (grades, the renowned
## spirits, where to bind and call them back), where a new hero should start, and how to play together with friends
## (Play Together: the same steps as docs/MULTIPLAYER_GUIDE.md). It can replay Tobren's introduction.

const CONTROLS := [
	["Moving and fighting", [
		[["move_up", "move_left", "move_down", "move_right"], "Move (you face the cursor)"],
		[["primary"], "Attack. Hold to keep the chain going; click an item on the ground to pick it up"],
		[["secondary"], "Heavy attack (hold to charge with a greatsword, spear or bow)"],
		[["attack_in_place"], "Hold to attack without moving"],
		[["dodge"], "Dodge roll: a moment where nothing can hit you"],
		[["guard"], "Guard with a shield"],
	]],
	["Skills and draughts", [
		[["skill_1", "skill_2", "skill_3", "skill_4", "skill_5", "skill_6"], "Skills on the skill bar"],
		[["potion_health"], "Potion belt 1 (health draught unless you change it in the Bag)"],
		[["potion_mana"], "Potion belt 2 (mana draught unless you change it in the Bag)"],
		[["interact"], "Talk, open doors, wake waypoints"],
		[["show_loot"], "Hold to show every item lying on the ground"],
		[["zoom_in", "zoom_out"], "Zoom the view"],
	]],
	["Windows", [
		[["inventory"], "Inventory: your bag and gear"],
		[["character"], "Character: attributes and every stat"],
		[["skills"], "Skills: spend skill points, fill the skill bar"],
		[["talents"], "Talents: spend talent points"],
		[["tempos"], "Tempos: your spirits' gear, stats and skills"],
		[["world_map"], "Map: waypoints, places, tracked routes"],
		[["guide"], "This Field Guide"],
		[["chat"], "Chat line"],
		[["pause"], "Close a window, or pause (Settings: rebind any key)"],
	]],
]

const STEPS := [
	["Speak to Elder Maelis", "She waits by the hearth, just down the Sanctuary Terrace, and has draughts for a new arrival."],
	["Stock up", "Anton at the market sells draughts, salts and scrolls. Brannoc's forge by the east yard sells and makes weapons and armour."],
	["Register as a hero", "The Swordfin Hall and the Lantern House register heroes. Your tier decides the finest gear you may wear; promotions need levels, fees and deeds."],
	["Bind a second Tempo", "Veyra Ashgrave at the Shrine of the Fallen, east of the terrace stair. You can carry two Tempos."],
	["Rest", "A night at the Salted Marlin restores you and your Tempos and leaves you Well Rested: more experience for a while."],
	["Travel", "Waypoint shrines carry you between the places you have woken them in. The Map can track a route to any known place; follow the directions on the right of the screen."],
	["If you fall", "You wake at the entrance of the place you fell, a little lighter in the purse, or at your checkpoint: rest at the bonfire of Wyman Outpost to set it. Your fallen Tempos stay fallen until Veyra calls them back."],
	["Craft", "Monsters drop parts and herbs grow by the roads. Use a forge, an alchemy table or a workbench (Brannoc's anvil, Angkol Les' table in Olivar, Wyman Outpost's camp) to turn them into draughts, bombs and fine gear, or salvage gear you do not need."],
	["Trade with Lape, store in the Vault", "Past Brannoc's smithy, Lape the Ancient appraises up to three of your items and offers one of three special-crafted, licensed pieces for them, or gold. The Hero's Vault beside him (and in Olivar and Wyman Outpost) keeps items for all of your heroes; a practice dummy stands near each vault for testing your damage."],
	["Clear stages, hunt champions", "Clear every camp of a place in one outing, or defeat a named champion, and Olivar's merchants put out new stock: advanced arms, jewels and draughts at a premium."],
	["Level up", "Each level brings skill points, talent points and attribute points. Spend them in the Skills, Talents and Character windows."],
]

var _tabs: TabBar
var _page := 0
var _content: VBoxContainer
var _scroll: ScrollContainer

func _init() -> void:
	super._init("Field Guide", Vector2(1500, 860))

func _build() -> void:
	var top := hbox(16)
	body.add_child(top)
	_tabs = TabBar.new()
	for t in ["Controls", "Tempos", "First steps", "Play Together", "Dungeons & Relics"]:
		_tabs.add_tab(t)
	_tabs.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_tabs.tab_changed.connect(func(i: int) -> void:
		_page = i
		refresh())
	top.add_child(_tabs)
	var replay := button("Hear %s's introduction again" % Dialogue.starter_name(Game.hero), _replay, &"", 360.0)
	top.add_child(replay)
	_scroll = ScrollContainer.new()
	_scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	body.add_child(_scroll)
	_content = vbox(12)
	_content.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_scroll.add_child(_content)

func open_on(page: int) -> void:
	_page = page
	Game.ui_root.open(&"guide")
	_tabs.current_tab = page

func refresh() -> void:
	if _content == null:
		return
	for c in _content.get_children():
		c.queue_free()
	match _page:
		0: _controls()
		1: _tempos()
		3: _together()
		4: _dungeons()
		_: _steps()
	_scroll.scroll_vertical = 0

## bh-012/13: the twenty dungeons, their seals, bosses and raid recovery, Relic Caches, gacha gear and Tempo summoning.
func _dungeons() -> void:
	var hero := Game.hero
	_heading("The dungeons of Salmonan")
	_para("Twenty dungeons lie under the island, from a smugglers' cellar for new heroes to the Maw Beneath at level 58. Each has two to five floors and a difficulty from Easy to Mythic. Every floor is sealed: defeat its Seal Keepers (an elite pack) to open the portal down; on the last sealed floor the dungeon's champion holds the seal, and the deepest floor is the lair of its lord. A broken seal stays broken, and the gate on the surface takes you straight to any floor you have opened. Every gate is on the map (M); the Underground view lists them all.")
	_para("Raids: when a dungeon's lord falls the dungeon is raided. Its halls stay empty for 30 minutes to 2 hours (longer for harder dungeons), then its monsters return. Its lord never comes back, but a Usurper, a named champion, claims the empty sanctum, and the champions keep returning.")
	for id in DataDungeons.order():
		var d := DataDungeons.get_def(id)
		var gate := DataIsland.place(String(d.surface.place))
		var lr := DataDungeons.level_range(id)
		var boss := DB.enemy(d.boss)
		var gone := DataDungeons.boss_gone(hero, id)
		_para("%s  %s (%s) — levels %d–%d, %d floors. Gate: %s (%s). Lord: %s. %s" % [DataDungeons.tier_stars(id), d.name, DataDungeons.tier_name(id),
			lr.x, lr.y, DataDungeons.floor_count(id), gate.get("name", "?"), DB.map_def(StringName(d.surface.map)).display_name,
			boss.display_name if boss else "?", DataDungeons.status_text(hero, id)], UITheme.GOLD if gone else UITheme.TEXT)
	_heading("Relic Caches and named gear")
	_para("Chests, champions and dungeon lords drop Relic Caches — Worn, Gilded and Radiant. Open one from your bag and its gear is revealed card by card. Every Licensed-or-better piece carries a name of its own and an epithet (no two alike), and stars from ★ to ★★★★★ for how close its rolls came to perfect. Some carry a relic passive: gold, experience, regeneration, life on kill, potions, thorns, damage to champions, Soul Embers or stronger Tempos.")
	_heading("Summoning Tempos")
	_para("Monsters (far more in the dungeons), champions and chests drop Soul Embers. At the Shrine of the Fallen, Veyra Ashgrave burns %d Embers to call one spirit, %d to call ten. ★★★ spirits are the plain dead of your grade, ★★★★ are honoured veterans one grade higher with an extra skill, ★★★★★ are renowned spirits — half of them today's featured spirit. You always get a ★★★★ or better within %d calls and a ★★★★★ by call %d. Call a renowned spirit you already have and it grows stronger (Resonance, up to V). Summoned spirits wait in the Spirit Hall; bind or swap them for free." % [
		TempoGacha.COST_ONE, TempoGacha.COST_TEN, TempoGacha.FOUR_PITY, TempoGacha.HARD_PITY])

## Multiplayer, explained simply enough for a young player (docs/MULTIPLAYER_GUIDE.md has the full version).
func _together() -> void:
	var touch := Settings.touch_mode
	var menu := "tap Menu at the top" if touch else "press %s" % Settings.binding_text(&"pause")
	_heading("Two jobs: Host and Friend")
	_para("One player is the Host. You arrive at the Host's side, then everyone explores on their own: on the Host's map you fight the Host's monsters together, anywhere else the world is yours. Everyone else is a Friend and brings their own hero, gear and bag. Up to 4 heroes, on PCs and phones together.")
	_heading("Before you start")
	_para("1.  Everyone has the same version of the game.
2.  Everyone starts or continues their own hero and walks into the world.
3.  For the easy way, everyone is on the same Wi-Fi.")
	_heading("The Host")
	_para("1.  %s, then Multiplayer.
2.  Press Host Game.
3.  Big gold letters show your room code, like K7QM-2XF. Read it out to your friends.
4.  The first time, Windows may ask \"Allow access?\" Ask a grown-up to click Allow." % menu.capitalize())
	_heading("A Friend")
	_para("1.  %s, then Multiplayer.
2.  Find the Host's world in the Join list and press Join.
3.  Not in the list? Type the room code under \"Join with a Room Code\" and press Join." % menu.capitalize())
	_heading("Far away, in different houses")
	_para("Ask a grown-up to install the same LAN VPN program on every computer (for example Radmin VPN) and join the same network in it. Then the Host tells everyone the code on the line that starts with \"VPN\". (Or the Host forwards port %d, UDP, on the router.)" % Net.PORT)
	_heading("Playing together")
	_para("Take any door or waypoint you like. Nearby allies on any map share combat and get personal, class-aware loot. A Knight's aura also helps friends standing close. Press %s to chat. In the Multiplayer window every player shows a ping: small numbers are good, red means slow." % ("Chat" if touch else Settings.binding_text(&"chat")))
	_para("Team Portal (%s) takes members to the leader; the leader chooses a member to visit. Stand still for the cast; movement or damage interrupts it. Its cooldown is 10 seconds. Summon Party in Multiplayer invites allies, who can choose Go or Stay. The minimap shows your friends as arrows in their colour, on its rim with the distance when they are out of sight; the Map shows where everyone is. A fallen friend: stand beside them and press %s to revive them. %s puts a marker on the ground that everyone sees. Your friends' boxes (health, distance, ping) sit on the left of the screen." % [
		"the portal button" if touch else Settings.binding_text(&"summon_party"), "Interact" if touch else Settings.binding_text(&"interact"),
		"The ! button" if touch else Settings.binding_text(&"ping")])
	_heading("Stopping")
	_para("A Friend presses Leave in the Multiplayer window and goes back to their own world. The Host presses Close World and everyone goes home. Each hero is saved on their own game.")
	var open_mp := button("Open Multiplayer", func() -> void:
		close_window()
		if Game.ui_root and Game.ui_root.has_method(&"open"):
			Game.ui_root.open(&"multiplayer"), &"PrimaryButton", 300.0)
	open_mp.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	_content.add_child(open_mp)

func _replay() -> void:
	close_window()
	if Game.ui_root and Game.ui_root.has_method(&"start_intro"):
		Game.ui_root.start_intro()

## "W / A / S / D" for a group of actions (each action's current binding).
static func keys_text(actions: Array) -> String:
	var parts := PackedStringArray()
	for a in actions:
		var k := Settings.binding_text(StringName(a))
		parts.append(k if k != "" else "—")
	return " / ".join(parts)

func _heading(text: String) -> void:
	_content.add_child(UITheme.title(text, 24, UITheme.GOLD))

func _para(text: String, color := UITheme.TEXT, size := 17) -> Label:
	var l := UITheme.label(text, size, color, UITheme.body_font())
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.custom_minimum_size = Vector2(1380, 0)
	_content.add_child(l)
	return l

func _controls() -> void:
	var cols := hbox(28)
	_content.add_child(cols)
	for group in CONTROLS:
		var v := vbox(8)
		v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		v.custom_minimum_size = Vector2(440, 0)
		cols.add_child(v)
		v.add_child(UITheme.title(group[0], 22, UITheme.GOLD))
		v.add_child(Tips.rule())
		for row in group[1]:
			var r := hbox(12)
			var key := PanelContainer.new()
			key.theme_type_variation = &"InsetPanel"
			key.custom_minimum_size = Vector2(150, 0)
			var kl := UITheme.label(keys_text(row[0]), 17, UITheme.PARCHMENT, UITheme.body_bold())
			kl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
			key.add_child(kl)
			r.add_child(key)
			var dl := UITheme.label(String(row[1]), 16, UITheme.TEXT, UITheme.body_font())
			dl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			dl.custom_minimum_size = Vector2(270, 0)
			dl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			dl.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
			r.add_child(dl)
			v.add_child(r)
	_content.add_child(Tips.rule())
	_para("In a conversation: Space or a click shows the next line, 1–9 picks an answer, Tab skips ahead. Every key can be changed in Settings (%s, then Settings)." % Settings.binding_text(&"pause"), UITheme.TEXT_DIM, 16)

func _tempos() -> void:
	var hero := Game.hero
	_heading("What a Tempo is")
	_para("Tempos are the spirits of warriors who died fighting the monsters of Jre. Bound to you, a Tempo fights at your side with a share of your own strength (half, for the plainest spirits), grows as you grow, heals you if it knows a mend, and falls back to tend itself when badly hurt. You can carry two at a time. Your first, %s, came through the waypoint with you." % Dialogue.starter_name(Game.hero))
	_para("Press %s for the Tempo window: give them gear from your bag (one rarity tier below what you may wear, and only their class's weapons) and look at their skills. If a Tempo falls, its token goes cold in your pack; Veyra Ashgrave can call it back for gold." % Settings.binding_text(&"tempos"))
	_heading("Binding more: the Shrine of the Fallen")
	_para("Veyra Ashgrave, the Tempo-Caller, keeps the Shrine of the Fallen east of the terrace stair in Malasugue. A few spirits answer her call at a time, and new ones answer every %d minutes. Binding one costs gold." % roundi(DataTempos.ROSTER_REFRESH / 60.0))
	_heading("Grades: stronger spirits as you grow")
	var g := TempoRules.current_grade(hero) if hero else 1
	var nxt := TempoRules.next_grade(hero) if hero else {}
	var now := "Spirits answering you now: %s grade." % DataTempos.grade_def(g).name
	if not nxt.is_empty():
		now += "  %s spirits answer when you %s." % [nxt.name, nxt.text]
	_para(now, UITheme.GOLD)
	var grid := GridContainer.new()
	grid.columns = 5
	grid.add_theme_constant_override("h_separation", 26)
	grid.add_theme_constant_override("v_separation", 6)
	for h in ["Grade", "Answers when you", "Strength", "Skills", ""]:
		grid.add_child(UITheme.label(h, 15, UITheme.TEXT_DIM, UITheme.body_bold()))
	for i in DataTempos.max_grade():
		var gd := DataTempos.grade_def(i + 1)
		var here := i + 1 == g
		grid.add_child(UITheme.label(("▶ " if here else "") + String(gd.name), 17, gd.color, UITheme.body_bold()))
		var how := "start" if i == 0 else "reach level %d" % int(gd.level)
		if String(gd.deed) != "":
			how += " or %s" % gd.deed
		grid.add_child(UITheme.label(how, 16, UITheme.TEXT, UITheme.body_font()))
		grid.add_child(UITheme.label("%d%% of yours" % roundi(float(gd.mirror) * 100.0), 16, UITheme.PARCHMENT, UITheme.number_font()))
		var ex: Array = gd.extra
		var n := "%d" % (1 + int(ex[0])) if int(ex[0]) == int(ex[1]) else "%d–%d" % [1 + int(ex[0]), 1 + int(ex[1])]
		grid.add_child(UITheme.label(n, 16, UITheme.PARCHMENT, UITheme.number_font()))
		var dl := UITheme.label(String(gd.desc), 15, UITheme.TEXT_DIM, UITheme.body_font())
		dl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		dl.custom_minimum_size = Vector2(620, 0)
		grid.add_child(dl)
	_content.add_child(grid)
	_para("When your grade rises, the weaker spirits fade from the shrine and stronger ones answer at once. The Tempos you already carry keep the grade they were bound at.", UITheme.TEXT_DIM, 16)
	_heading("The renowned")
	_para("Five spirits whose names are still sung wait at the shrine for a hero strong enough to carry them. They cost a fortune, carry three quarters of your strength and fight with skills no other spirit has. Save for them before a hard raid.")
	for id in DataTempos.legend_ids():
		var lg := DataTempos.legend(id)
		var r := hbox(14)
		var ic := TextureRect.new()
		ic.texture = DataTempos.class_icon(lg["class"])
		ic.custom_minimum_size = Vector2(40, 40)
		ic.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		ic.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		r.add_child(ic)
		var nm := UITheme.label("%s, %s" % [lg.name, lg.title], 18, DataTempos.RENOWNED.color, UITheme.body_bold())
		nm.custom_minimum_size = Vector2(420, 0)
		r.add_child(nm)
		r.add_child(UITheme.label("%s  ·  level %d  ·  %s gold" % [DataTempos.tempo_class(lg["class"]).name, int(lg.level), _thousands(int(lg.price))],
			16, UITheme.PARCHMENT, UITheme.body_font()))
		if hero:
			var state := "walks with you" if TempoRules.legend_bound(hero, id) else ("can be bound" if hero.progress.level >= int(lg.level) else "not yet")
			r.add_child(UITheme.label("(%s)" % state, 15, UITheme.GOOD if state != "not yet" else UITheme.TEXT_MUTED, UITheme.body_font()))
		_content.add_child(r)

func _steps() -> void:
	_heading("Where to start")
	for s in STEPS:
		var r := vbox(2)
		r.add_child(UITheme.label(String(s[0]), 19, UITheme.GOLD, UITheme.body_bold()))
		var l := UITheme.label(String(s[1]), 16, UITheme.TEXT, UITheme.body_font())
		l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		l.custom_minimum_size = Vector2(1380, 0)
		r.add_child(l)
		_content.add_child(r)

static func _thousands(n: int) -> String:
	var s := str(n)
	var out := ""
	while s.length() > 3:
		out = "," + s.substr(s.length() - 3) + out
		s = s.substr(0, s.length() - 3)
	return s + out
