class_name Tips
## Tooltip content builders: items (with side-by-side "Equipped" comparison and the stat diff), skills, derived stats
## (value + where it comes from), statuses, and plain text. Everything reads the live game data.

const W := 360.0
const AFFIX := Color(0.56, 0.72, 1.0)
const LICENSE := Color(0.35, 0.88, 0.8)
const POWER := Color(1.0, 0.62, 0.25)
const AETHER := Color(0.6, 0.98, 1.0)
const SET_ON := Color(0.5, 0.95, 0.45)
const SET_OFF := Color(0.45, 0.43, 0.4)

static func frame(min_w := W) -> Array:
	var pc := PanelContainer.new()
	pc.theme_type_variation = &"TooltipFrame"
	pc.custom_minimum_size = Vector2(min_w, 0)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 4)
	pc.add_child(v)
	return [pc, v]

static func lbl(text: String, size := 16, color := UITheme.TEXT, font: Font = null, wrap := true) -> Label:
	var l := UITheme.label(text, size, color, font)
	if wrap:
		l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		l.custom_minimum_size = Vector2(W - 36.0, 0)
	return l

static func rich(bbcode: String, size := 16) -> RichTextLabel:
	var r := RichTextLabel.new()
	r.bbcode_enabled = true
	r.fit_content = true
	r.scroll_active = false
	r.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	r.custom_minimum_size = Vector2(W - 36.0, 0)
	r.add_theme_font_size_override("normal_font_size", size)
	r.add_theme_font_size_override("bold_font_size", size)
	r.text = bbcode
	return r

static func rule(c := UITheme.BRONZE_DIM) -> Control:
	var r := ColorRect.new()
	r.color = Color(c, 0.6)
	r.custom_minimum_size = Vector2(0, 1)
	return r

static func gap(h := 4.0) -> Control:
	var c := Control.new()
	c.custom_minimum_size = Vector2(0, h)
	return c

static func text(t: String, title := "") -> Control:
	var f := frame(280.0)
	if title != "":
		f[1].add_child(lbl(title, 18, UITheme.GOLD, UITheme.title_font()))
	f[1].add_child(lbl(t, 16))
	return f[0]

# ---- Items ----------------------------------------------------------------------------------------------------------

## opts: {"hero": HeroData, "compare": bool (default true for equipment not equipped), "price": int, "sell": int,
##        "hint": String, "equipped": bool}
static func item(it: ItemInstance, opts := {}) -> Control:
	var hero: HeroData = opts.get("hero", Game.hero)
	var card := _item_card(it, hero, opts)
	var want_compare: bool = opts.get("compare", true) and hero != null and it.is_equipment() and not opts.get("equipped", false)
	if not want_compare:
		return card
	var current := ItemCompare.equipped_for(hero, it)
	var pv := ItemCompare.preview(hero, it)
	var box := HBoxContainer.new()
	box.add_theme_constant_override("separation", 8)
	box.alignment = BoxContainer.ALIGNMENT_BEGIN
	var v := card.get_child(0) as VBoxContainer
	v.add_child(gap(2))
	v.add_child(rule(UITheme.BRONZE))
	v.add_child(lbl("If equipped%s:" % ("" if current == null else " (replaces %s)" % current.display_name()), 15, UITheme.TEXT_DIM, UITheme.body_bold()))
	if pv.rows.is_empty():
		v.add_child(lbl("No change to your statistics.", 15, UITheme.TEXT_MUTED))
	for r in pv.rows.slice(0, 12):
		v.add_child(_diff_row(r))
	box.add_child(card)
	if current != null:
		var eq := _item_card(current, hero, {"equipped": true})
		var tag := lbl("EQUIPPED", 13, UITheme.TEXT_DIM, UITheme.title_font(), false)
		(eq.get_child(0) as VBoxContainer).add_child(tag)
		(eq.get_child(0) as VBoxContainer).move_child(tag, 0)
		eq.modulate = Color(0.92, 0.92, 0.92)
		box.add_child(eq)
	return box

static func _wt(w: float) -> String:
	return ("%.2f" % w) if w < 1.0 else ("%.1f" % w)

static func _diff_row(r: Dictionary) -> Control:
	var h := HBoxContainer.new()
	var n := lbl(r.name, 15, UITheme.TEXT, null, false)
	n.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	h.add_child(n)
	var col := UITheme.GOOD if r.better else UITheme.BAD
	var arrow := "▲" if r.better else "▼"
	h.add_child(lbl("%s → " % r.text_before, 15, UITheme.TEXT_DIM, UITheme.number_font(), false))
	h.add_child(lbl("%s %s" % [r.text_after, arrow], 15, col, UITheme.number_font(), false))
	return h

static func _item_card(it: ItemInstance, hero: HeroData, opts: Dictionary) -> PanelContainer:
	var f := frame()
	var pc: PanelContainer = f[0]
	var v: VBoxContainer = f[1]
	var col := it.color()
	# header: icon + name + tier/type
	var head := HBoxContainer.new()
	head.add_theme_constant_override("separation", 10)
	var icon := ItemSlot.new(ItemSlot.Kind.DISPLAY, 60.0)
	icon.set_item(it)
	icon.drag_enabled = false
	head.add_child(icon)
	var hv := VBoxContainer.new()
	hv.add_theme_constant_override("separation", 0)
	hv.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var name_l := lbl(it.display_name(), 21, col, UITheme.title_font())
	name_l.custom_minimum_size = Vector2(W - 110.0, 0)
	name_l.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.9))
	name_l.add_theme_constant_override("outline_size", 4)
	hv.add_child(name_l)
	hv.add_child(lbl(_type_line(it), 15, UITheme.TEXT_DIM, null, false))
	head.add_child(hv)
	v.add_child(head)
	var band := ColorRect.new()
	band.color = Color(col, 0.8)
	band.custom_minimum_size = Vector2(0, 2)
	v.add_child(band)
	# core numbers
	if it.base.is_weapon():
		var wt := DB.weapon_type(it.base.weapon_type)
		var dr := it.damage_range()
		v.add_child(_big_line("%d – %d" % [roundi(dr.x), roundi(dr.y)], "Damage", UITheme.PARCHMENT))
		if it.base.element != Elements.PHYSICAL and it.base.element_share > 0.0:
			v.add_child(lbl("%d%% as %s" % [roundi(it.base.element_share * 100.0), Elements.NAMES[it.base.element]], 15, Elements.color(it.base.element)))
		if wt:
			v.add_child(lbl("%.2f attacks per second · %s%% critical chance · %.1f m reach" % [it.base.weapon_aps(), StatDefs._num(wt.crit_chance * 100.0), wt.reach], 15, UITheme.TEXT))
			if wt.two_handed:
				v.add_child(lbl("Two-handed", 14, UITheme.TEXT_DIM))
	elif it.base.category == &"shield":
		v.add_child(_big_line(str(roundi(it.defense_value())), "Defense", UITheme.PARCHMENT))
		v.add_child(lbl("%d%% block chance · %d%% block strength" % [roundi(it.base.block_chance * 100.0), roundi(it.base.block_strength * 100.0)], 15))
	elif it.is_equipment() and it.defense_value() > 0.0:
		v.add_child(_big_line(str(roundi(it.defense_value())), "Defense", UITheme.PARCHMENT))
	if it.quality > 0.0 and it.is_equipment():
		v.add_child(lbl("Quality +%d%%%s" % [roundi(it.quality * 100.0), " · Crafted" if it.crafted else ""], 14, UITheme.TEXT_DIM))
	elif it.crafted:
		v.add_child(lbl("Crafted", 14, UITheme.TEXT_DIM))
	for m in it.base.implicit:
		v.add_child(lbl(StatDefs.format_modifier(m.stat, m.op, m.value), 15, UITheme.PARCHMENT))
	# consumables
	if it.base.is_consumable() or it.base.category == &"material" or it.base.is_quest():
		if it.base.flavor != "":
			v.add_child(lbl(it.base.flavor, 15, UITheme.TEXT))
		if it.base.category == &"material":
			var uses := Tips.material_uses(it.base.id)
			if uses != "":
				v.add_child(lbl(uses, 14, UITheme.TEXT_DIM))
	# enchantments
	var aff := it.affix_lines()
	if not aff.is_empty():
		v.add_child(gap(2))
		for line in aff:
			v.add_child(lbl(line, 15, AFFIX))
	for m in it.base.fixed_mods:
		v.add_child(lbl(StatModifier_text(m), 15, AFFIX))
	if it.license != &"":
		var lic: Dictionary = DB.licenses.get(it.license, {})
		v.add_child(gap(2))
		v.add_child(lbl("%s license" % lic.get("name", ""), 15, LICENSE, UITheme.body_bold()))
		for m in it.license_modifiers():
			v.add_child(lbl(StatDefs.format_modifier(m.stat, m.op, m.value), 15, LICENSE))
	for pid in it.powers:
		var p := DB.power(StringName(pid))
		if p == null:
			continue
		v.add_child(gap(2))
		var pc_col := AETHER if p.tier == &"aether" else (Color(0.86, 0.55, 1.0) if p.tier == &"mythical" else POWER)
		v.add_child(lbl(p.display_name, 16, pc_col, UITheme.body_bold()))
		v.add_child(lbl(p.description, 15, Color(pc_col, 0.9)))
	# set
	var sd := it.set_def()
	if sd:
		v.add_child(gap(2))
		var owned: int = hero.equipment.set_counts().get(sd.id, 0) if hero else 0
		v.add_child(lbl("%s (%d/%d)" % [sd.display_name, owned, sd.pieces.size()], 16, UITheme.GOLD, UITheme.body_bold()))
		for pid in sd.pieces:
			var b := DB.item_base(StringName(pid))
			var have := false
			if hero:
				for e in hero.equipment.equipped_items():
					if e.base.id == StringName(pid):
						have = true
			v.add_child(lbl("  " + (b.display_name if b else String(pid)), 14, SET_ON if have else SET_OFF))
		for n in sd.thresholds():
			var active: bool = owned >= int(n)
			v.add_child(lbl("(%d) %s" % [n, sd.bonuses[n].get("desc", "")], 15, SET_ON if active else SET_OFF))
	# requirements
	if it.is_equipment() and hero:
		var reqs := []
		if it.base.level_req > 1:
			reqs.append(["Requires Level %d" % it.base.level_req, hero.progress.level >= it.base.level_req])
		var attrs := hero.progress.base_attributes()
		for a in it.base.requirements:
			reqs.append(["Requires %d %s" % [it.base.requirements[a], BH.ATTRIBUTE_NAMES[a]], int(attrs.get(a, 0)) >= int(it.base.requirements[a])])
		if not reqs.is_empty():
			v.add_child(gap(2))
			for r in reqs:
				v.add_child(lbl(r[0], 14, UITheme.TEXT_DIM if r[1] else UITheme.BAD))
	var lore := it.base.lore if it.base.lore != "" else (it.base.flavor if it.is_equipment() else "")
	if lore != "":
		v.add_child(gap(2))
		var ll := lbl(lore, 14, Color(0.72, 0.64, 0.5))
		ll.add_theme_font_override("font", UITheme.body_font())
		v.add_child(ll)
	# footer
	v.add_child(gap(2))
	v.add_child(rule())
	var foot := HBoxContainer.new()
	var left := lbl("Item level %d" % it.ilvl if it.is_equipment() else ("Stack of %d" % it.count if it.count > 1 else ""), 14, UITheme.TEXT_MUTED, null, false)
	# carried weight (bh-006): equipment is heavy, the rest is light
	var wtxt := "Weight %s" % _wt(it.base.weight)
	if it.count > 1:
		wtxt = "Weight %s each · %s" % [_wt(it.base.weight), _wt(it.weight())]
	var wl := lbl(wtxt, 14, UITheme.TEXT_DIM, UITheme.number_font(), false)
	wl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	foot.add_child(wl)
	left.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	foot.add_child(left)
	var price: int = opts.get("price", -1)
	var sell: int = opts.get("sell", it.sell_value())
	if price >= 0:
		foot.add_child(_gold(price, "Price", hero == null or hero.inventory.gold >= price))
	elif sell > 0:
		foot.add_child(_gold(sell, "Sells for", true))
	elif not it.base.sellable:
		foot.add_child(lbl("Cannot be sold", 14, UITheme.TEXT_MUTED, null, false))
	v.add_child(foot)
	var flags := []
	if it.locked:
		flags.append("Locked")
	if it.favorite:
		flags.append("Favorite")
	if it.junk:
		flags.append("Marked to sell")
	if not flags.is_empty():
		v.add_child(lbl(" · ".join(flags), 13, UITheme.GOLD))
	var hint := touch_hint(String(opts.get("hint", "")))
	if hint != "":
		v.add_child(lbl(hint, 13, UITheme.TEXT_MUTED))
	return pc

static func StatModifier_text(m: StatModifier) -> String:
	return StatDefs.format_modifier(m.stat, m.op, m.value)

static func _type_line(it: ItemInstance) -> String:
	var kind := ""
	if it.base.is_weapon():
		var wt := DB.weapon_type(it.base.weapon_type)
		kind = wt.display_name if wt else "Weapon"
	else:
		kind = {&"shield": "Shield", &"helm": "Helm", &"armor": "Armor", &"inner_garment": "Inner Garment", &"gloves": "Gloves",
			&"boots": "Boots", &"accessory": "Accessory", &"consumable": "Consumable", &"material": "Material", &"quest": "Quest Item"}.get(it.base.category, "Item")
	if it.is_equipment():
		return "%s %s" % [it.rarity_name(), kind]
	return kind

static func _big_line(value: String, what: String, col: Color) -> Control:
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", 8)
	h.add_child(lbl(value, 24, col, UITheme.number_font(), false))
	var w := lbl(what, 15, UITheme.TEXT_DIM, null, false)
	w.size_flags_vertical = Control.SIZE_SHRINK_END
	h.add_child(w)
	return h

static func _gold(n: int, what: String, ok: bool) -> Control:
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", 4)
	h.add_child(lbl(what, 14, UITheme.TEXT_MUTED, null, false))
	var t := TextureRect.new()
	t.texture = UIArt.ui_icon("gold")
	t.custom_minimum_size = Vector2(16, 16)
	t.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	t.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	t.modulate = UITheme.GOLD
	h.add_child(t)
	h.add_child(lbl(str(n), 15, UITheme.GOLD if ok else UITheme.BAD, UITheme.number_font(), false))
	return h

# ---- Skills ---------------------------------------------------------------------------------------------------------

## Fills {param} placeholders with the resolved rank values.
static func skill_text(s: SkillDef, params: Dictionary) -> String:
	var t := s.description
	for k in params:
		var v = params[k]
		var txt := str(v)
		if v is float:
			txt = str(roundi(v)) if absf(v - roundf(v)) < 0.01 else ("%.1f" % v)
		t = t.replace("{%s}" % k, txt)
	return t

static func skill(sid: StringName, hero: HeroData, player: Player = null, next_rank := false) -> Control:
	var s := DB.skill(sid)
	if s == null:
		return null
	var rank := hero.skill_rank(sid) if hero else 0
	var f := frame(380.0)
	var v: VBoxContainer = f[1]
	var head := HBoxContainer.new()
	head.add_theme_constant_override("separation", 10)
	var ic := TextureRect.new()
	ic.texture = UIArt.skill_icon(sid)
	ic.custom_minimum_size = Vector2(52, 52)
	ic.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	head.add_child(ic)
	var hv := VBoxContainer.new()
	hv.add_theme_constant_override("separation", 0)
	hv.add_child(lbl(s.display_name, 21, UITheme.GOLD, UITheme.title_font(), false))
	var kind := "Weapon Skill" if s.kind == DamageRequest.Kind.ATTACK else "Spell"
	hv.add_child(lbl("%s · Rank %d / %d" % [kind, rank, s.max_rank] if rank > 0 else "%s · Not learned" % kind, 15, UITheme.TEXT_DIM, null, false))
	head.add_child(hv)
	v.add_child(head)
	v.add_child(rule(UITheme.BRONZE))
	var costs := HBoxContainer.new()
	costs.add_theme_constant_override("separation", 16)
	var mc := player.mana_cost(sid) if player else s.mana_at(maxi(rank, 1))
	costs.add_child(lbl("%d Mana" % roundi(mc), 16, Color(0.45, 0.65, 1.0), UITheme.body_bold(), false))
	if s.valor_cost > 0.0:
		costs.add_child(lbl("%d Valor" % roundi(s.valor_cost), 16, UITheme.EMBER, UITheme.body_bold(), false))
	var cd := player.skill_cooldown(sid) if player else s.cooldown
	costs.add_child(lbl("%.1f s cooldown" % cd if cd > 0.0 else "No cooldown", 16, UITheme.TEXT, null, false))
	v.add_child(costs)
	var el := s.element
	if not s.conversion.is_empty():
		var parts := []
		for e in s.conversion:
			parts.append("%d%% %s" % [roundi(float(s.conversion[e]) * 100.0), Elements.NAMES[e]])
		v.add_child(lbl("Element: " + ", ".join(parts), 15, Elements.color(s.conversion.keys()[0])))
	elif el != Elements.PHYSICAL:
		v.add_child(lbl("Element: %s" % Elements.NAMES[el], 15, Elements.color(el)))
	var params := hero.resolved_skill(sid) if hero and rank > 0 else s.resolve(1)
	v.add_child(gap(2))
	v.add_child(lbl(skill_text(s, params), 16, UITheme.TEXT))
	var extra := []
	if params.has("damage_min") and params.has("damage_max"):
		extra.append("Base damage %d – %d (scales with %s)" % [roundi(params.damage_min), roundi(params.damage_max),
			"Intelligence" if s.kind == DamageRequest.Kind.SPELL else "your weapon"])
	if params.has("range"):
		extra.append("Range %s m" % StatDefs._num(float(params.range)))
	if params.has("radius"):
		extra.append("Radius %s m" % StatDefs._num(float(params.radius)))
	if s.requires == &"melee":
		extra.append("Requires a melee weapon")
	elif s.requires == &"shield":
		extra.append("Requires a shield")
	for e in extra:
		v.add_child(lbl(e, 14, UITheme.TEXT_DIM))
	if player and rank > 0:
		var why := player.skill_block_reason(sid)
		if why != "" and why != "Cooldown":
			v.add_child(lbl(why, 15, UITheme.BAD, UITheme.body_bold()))
	if next_rank or (hero and rank > 0 and rank < s.max_rank):
		var np := s.resolve(rank + 1, hero.skill_upgrades(sid) if hero else {})
		var changes := []
		for k in s.per_rank:
			changes.append("%s %s → %s" % [String(k).replace("_", " ").capitalize(), StatDefs._num(float(params.get(k, 0.0))), StatDefs._num(float(np.get(k, 0.0)))])
		if not changes.is_empty():
			v.add_child(gap(2))
			v.add_child(lbl("Next rank:", 14, UITheme.GOLD, UITheme.body_bold()))
			for c in changes:
				v.add_child(lbl("  " + c, 14, UITheme.GOOD))
	return f[0]

# ---- Stats ----------------------------------------------------------------------------------------------------------

static func stat(key: StringName, d: DerivedStats, value_text := "") -> Control:
	var f := frame(360.0)
	var v: VBoxContainer = f[1]
	var head := HBoxContainer.new()
	var n := lbl(StatDefs.name_of(key), 19, UITheme.GOLD, UITheme.title_font(), false)
	n.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	head.add_child(n)
	head.add_child(lbl(value_text if value_text != "" else StatDefs.format_value(key, d.get_stat(key)), 19, UITheme.PARCHMENT, UITheme.number_font(), false))
	v.add_child(head)
	var desc := StatDefs.desc_of(key)
	if desc != "":
		v.add_child(lbl(desc, 15, UITheme.TEXT_DIM))
	var lines: PackedStringArray = d.explain.get(key, PackedStringArray())
	if not lines.is_empty():
		v.add_child(rule())
		v.add_child(lbl("Sources", 14, UITheme.TEXT_MUTED, UITheme.body_bold()))
		for line in lines:
			v.add_child(lbl(line, 15, UITheme.TEXT))
	return f[0]

# ---- Statuses -------------------------------------------------------------------------------------------------------

static func status(inst: Variant) -> Control:
	var id: StringName = inst.id
	var f := frame(300.0)
	var v: VBoxContainer = f[1]
	var bad := StatusRules.is_debuff(id)
	var head := lbl(StatusRules.name_of(id) + (" x%d" % inst.stacks if int(inst.stacks) > 1 else ""), 19, UITheme.BAD if bad else UITheme.GOOD, UITheme.title_font())
	v.add_child(head)
	v.add_child(lbl(StatusRules.desc_of(id), 15, UITheme.TEXT))
	if inst.infinite:
		v.add_child(lbl("Lasts while its source remains", 14, UITheme.TEXT_DIM))
	else:
		v.add_child(lbl("%.1f s remaining" % inst.remaining, 14, UITheme.TEXT_DIM))
	if inst.source_name != "":
		v.add_child(lbl("From %s" % inst.source_name, 14, UITheme.TEXT_MUTED))
	return f[0]

## Crafting uses of a material for its tooltip ("Used in: Health Draught, Steel Ingot and 2 more").
static func material_uses(base_id: StringName) -> String:
	var names := []
	for r in DataCrafting.all():
		for inp in r.inputs:
			if inp[0] == base_id:
				names.append(String(r.name))
				break
	if names.is_empty():
		return ""
	names.sort()
	if names.size() > 4:
		return "Used in: %s and %d more" % [", ".join(names.slice(0, 4)), names.size() - 4]
	return "Used in: %s" % ", ".join(names)

## Keyboard + mouse hints read as touch gestures in touch play: a long press is the right-click (TouchControls).
static func touch_hint(t: String) -> String:
	if not Settings.touch_mode or t == "":
		return t
	return t.replace("Right-click", "Hold").replace("right-click", "hold").replace("Double-click", "Double-tap").replace(" · Shift+click to choose quantity", "").replace("Click", "Tap").replace("click", "tap")
