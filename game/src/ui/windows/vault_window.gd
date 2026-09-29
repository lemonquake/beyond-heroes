class_name VaultWindow
extends UIWindow
## bh-019: the Hero's Vault (HeroVault) — storage shared by all of your heroes. Left: the vault; right: your bag.
## Click an item to move it across (or drag it; drag within the vault to rearrange). The footer enlarges the vault
## (64 slots for 2,500 gold, 128 for 8,000). Every change saves the vault and this hero together a moment later, and
## again when the window closes, so an item can never be lost or doubled between the two files.

const VAULT_PX := 60.0
const BAG_PX := 56.0

var hero: HeroData
var vault: HeroVault
var _vgrid: GridContainer
var _bgrid: GridContainer
var _vhead: Label
var _msg: Label
var _gold: Label
var _up_btn: Button
var _save_timer: Timer
var _dirty := false

func _init() -> void:
	super._init("The Hero's Vault", Vector2(1560, 940))

func _ready() -> void:
	super._ready()
	_save_timer = Timer.new()
	_save_timer.one_shot = true
	_save_timer.wait_time = 0.6
	_save_timer.timeout.connect(_persist)
	add_child(_save_timer)
	closed.connect(_persist)

func _build() -> void:
	var cols := hbox(24)
	cols.size_flags_vertical = Control.SIZE_EXPAND_FILL
	body.add_child(cols)
	var left := vbox(8)
	left.custom_minimum_size = Vector2(620, 0)
	left.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	cols.add_child(left)
	_vhead = UITheme.title("", 20, UITheme.GOLD)
	left.add_child(_vhead)
	left.add_child(HSeparator.new())
	var note := UITheme.label("Shared by every hero you play on this device. Click an item to take it out.", 15, UITheme.TEXT_DIM, UITheme.body_font())
	note.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	left.add_child(note)
	var vw := inset()
	vw.size_flags_vertical = Control.SIZE_EXPAND_FILL
	left.add_child(vw)
	var vs := ScrollContainer.new()
	vs.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	vw.add_child(vs)
	_vgrid = GridContainer.new()
	_vgrid.columns = 10
	_vgrid.add_theme_constant_override("h_separation", 6)
	_vgrid.add_theme_constant_override("v_separation", 6)
	vs.add_child(_vgrid)
	var right := vbox(8)
	right.custom_minimum_size = Vector2(640, 0)
	cols.add_child(right)
	right.add_child(section("Your Bag"))
	var bn := UITheme.label("Click an item to put it in the vault.", 15, UITheme.TEXT_DIM, UITheme.body_font())
	right.add_child(bn)
	var bw := inset()
	bw.size_flags_vertical = Control.SIZE_EXPAND_FILL
	right.add_child(bw)
	var bs := ScrollContainer.new()
	bs.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	bw.add_child(bs)
	_bgrid = GridContainer.new()
	_bgrid.columns = 10
	_bgrid.add_theme_constant_override("h_separation", 6)
	_bgrid.add_theme_constant_override("v_separation", 6)
	bs.add_child(_bgrid)
	var foot := hbox(12)
	body.add_child(foot)
	foot.add_child(button("Sort the Vault", func() -> void:
		vault.sort()
		_changed(), &"", 200.0))
	_up_btn = button("", _upgrade, &"PrimaryButton", 380.0)
	foot.add_child(_up_btn)
	_msg = UITheme.label("", 17, UITheme.GOOD, UITheme.body_font())
	_msg.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_msg.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	foot.add_child(_msg)
	_gold = UITheme.label("", 20, UITheme.GOLD, UITheme.number_font())
	foot.add_child(_gold)

func refresh() -> void:
	hero = Game.hero
	vault = HeroVault.shared()
	if hero == null or _vgrid == null:
		return
	_vhead.text = "The Vault  ·  %d / %d slots" % [vault.used(), vault.capacity()]
	_fill(_vgrid, vault.cells, true)
	_fill(_bgrid, hero.inventory.cells, false)
	if vault.next_cost() > 0:
		_up_btn.text = "Enlarge to %d slots  (%s gold)" % [vault.next_size(), SocketWindow._thousands(vault.next_cost())]
		_up_btn.disabled = hero.inventory.gold < vault.next_cost()
	else:
		_up_btn.text = "The vault is at its largest (%d slots)" % vault.capacity()
		_up_btn.disabled = true
	_gold.text = "%s gold" % SocketWindow._thousands(hero.inventory.gold)

func _fill(grid: GridContainer, cells: Array, in_vault: bool) -> void:
	for c in grid.get_children():
		grid.remove_child(c)
		c.queue_free()
	for i in cells.size():
		var it: ItemInstance = cells[i]
		var s := ItemSlot.new(ItemSlot.Kind.DISPLAY if in_vault else ItemSlot.Kind.INVENTORY, VAULT_PX if in_vault else BAG_PX)
		s.index = i
		s.drag_enabled = it != null
		s.set_item(it)
		s.set_meta(&"vault", in_vault)
		if it != null and not in_vault and HeroVault.refuse_reason(it) != "":
			s.dim = true
		s.clicked.connect(func(sl: ItemSlot, b: int, _s: bool, _c: bool) -> void:
			if sl.item == null or b != MOUSE_BUTTON_LEFT:
				return
			if in_vault:
				_take(sl.index)
			else:
				_put(sl.item, -1))
		s.dropped.connect(_on_drop)
		s.hovered.connect(_on_hover)
		grid.add_child(s)

func _on_drop(from: ItemSlot, to: ItemSlot) -> void:
	var from_vault: bool = from.get_meta(&"vault", false)
	var to_vault: bool = to.get_meta(&"vault", false)
	if from_vault and to_vault:
		vault.move(from.index, to.index)
		_changed()
	elif not from_vault and to_vault and from.item:
		_put(from.item, to.index)
	elif from_vault and not to_vault:
		_take(from.index)

func _put(it: ItemInstance, at: int) -> void:
	var err := vault.deposit(hero, it, at)
	if err != "":
		_show(err, false)
		return
	_show("Stored in the vault.", true)
	_changed()

func _take(idx: int) -> void:
	var err := vault.withdraw(hero, idx)
	if err != "":
		_show(err, false)
		_changed()
		return
	_show("Taken from the vault.", true)
	_changed()

func _upgrade() -> void:
	var cost := vault.next_cost()
	var n_slots := vault.next_size()
	Game.ui_root.ask("Enlarge the Vault", "Pay %s gold to enlarge the vault to %d slots?\nEvery one of your heroes shares it." % [SocketWindow._thousands(cost), n_slots], func() -> void:
		var err := vault.upgrade(hero)
		if err != "":
			_show(err, false)
		else:
			_show("The vault now holds %d items." % vault.capacity(), true)
			Audio.play_ui(&"ui_buy" if Audio.has_sound(&"ui_buy") else &"ui_click")
		_changed(), "Pay %s gold" % SocketWindow._thousands(cost))

func _changed() -> void:
	_dirty = true
	if _save_timer:
		_save_timer.start()
	refresh()

## Save the vault and the hero together (never one without the other).
func _persist() -> void:
	if not _dirty or vault == null:
		return
	_dirty = false
	vault.save()
	if Game.hero:
		TempoParty.sync_all()
		SaveSystem.save_hero(Game.hero, Game.save_slot)

func _show(t: String, ok: bool) -> void:
	_msg.text = t
	_msg.add_theme_color_override("font_color", UITheme.GOOD if ok else UITheme.BAD)
	if not ok:
		Audio.play_ui(&"ui_error")

func _on_hover(s: ItemSlot, inside: bool) -> void:
	if not inside or s.item == null:
		TooltipLayer.hide_for(s)
		return
	var it := s.item
	var h := hero
	TooltipLayer.show_for(s, func() -> Control: return Tips.item(it, {"hero": h}))
