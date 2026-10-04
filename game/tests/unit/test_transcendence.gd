extends TestCase
## Class Transcendence, stage 1 and 3: the registry, eligibility, the advancement itself, granted free ranks, saves
## (old, corrupt, round trips), shared-tree safety, the class gate on skills, and the equipment requirement system
## with the thirty-six new pieces and their sources.

const FAMILIES := [&"knight", &"ranger", &"mage", &"shadowblade"]
const LEVELS := [1, 59, 60, 61, 119, 120, 121, 179, 180, 240, 300]

func _init() -> void:
	strict = true

func hero(cls: StringName, level := 1) -> HeroData:
	var h := Game.new_hero(cls, "Trans %s" % cls)
	h.progress.level = level
	h._apply_floors()
	return h

func first_of(fam: StringName) -> StringName:
	return DataTranscendence.children_of(fam)[0]

func roundtrip(h: HeroData, json := true) -> HeroData:
	var d := h.to_dict()
	if json:
		d = JSON.parse_string(JSON.stringify(d))
	return HeroData.from_dict(d)

# ---- Registry -------------------------------------------------------------------------------------------------------

func test_registry_has_sixteen_identities_with_full_content() -> void:
	eq(DataTranscendence.FAMILIES.size(), 4, "four starting classes")
	eq(DataTranscendence.CLASSES.size(), 12, "twelve advanced classes")
	eq(DataTranscendence.name_of(&"ranger"), "Hunter", "the ranger family is shown as Hunter")
	eq(DB.class_def(&"ranger").display_name, "Hunter", "the class definition reads Hunter; its id stays ranger")
	var seen := {}
	for id in DataTranscendence.CLASSES:
		var d: Dictionary = DataTranscendence.CLASSES[id]
		eq((d.skills as Array).size(), 3, "%s grants three skills" % id)
		eq((d.talents as Array).size(), 3, "%s grants three talents" % id)
		eq((d.gear as Array).size(), 3, "%s has three gear pieces" % id)
		for sid in d.skills:
			var s := DB.skill(sid)
			ok(s != null, "skill %s exists" % sid)
			if s:
				eq(s.class_id, id, "%s belongs to %s" % [sid, id])
				ok(s.description.length() > 40, "%s explains itself" % sid)
			ok(not seen.has(sid), "%s is unique" % sid)
			seen[sid] = true
			eq(DataTranscendence.owner_of(sid), id, "owner lookup %s" % sid)
		for tid in d.talents:
			ok(DataTranscendence.TALENTS.has(tid), "talent %s defined" % tid)
			ok(not seen.has(tid), "%s is unique" % tid)
			seen[tid] = true
		for gid in d.gear:
			ok(DB.item_base(gid) != null, "gear %s exists" % gid)
		var stage := DataTranscendence.stage_of(id)
		eq(DataTranscendence.ancestry(id).size(), stage + 1, "%s lineage length" % id)
		ok(DataTranscendence.is_family(DataTranscendence.ancestry(id)[0]), "%s descends from a family" % id)
	for fam in FAMILIES:
		eq(DataTranscendence.children_of(fam).size(), 1, "%s has one first transcendence" % fam)
		eq(DataTranscendence.children_of(first_of(fam)).size(), 2, "%s has two master choices" % fam)
		eq(DataTranscendence.family_members(fam).size(), 4, "%s family has four identities" % fam)
	# prefixes keep Void Sovereign apart from Arcanist / Archmage
	for sid in DataTranscendence.CLASSES[&"void_sovereign"].skills:
		ok(String(sid).begins_with("vs_"), "Void Sovereign ids use vs_")
	# distinct themes for all twelve
	var colours := {}
	for id in DataTranscendence.CLASSES:
		var th := ClassTranscendence.class_theme(id)
		var key := "%s|%s" % [(th.primary as Color).to_html(), (th.accent as Color).to_html()]
		ok(not colours.has(key), "%s has its own theme" % id)
		colours[key] = true
		ok(not th.has("glow"), "no class glow (%s)" % id)
	done()

func test_server_registry_matches_the_game() -> void:
	var text := FileAccess.get_file_as_string(ProjectSettings.globalize_path("res://").path_join("../server/service.py"))
	ok(text.find("PROTOCOL = %d" % Net.PROTOCOL) >= 0, "account service speaks the game's protocol")
	for id in DataTranscendence.CLASSES:
		var d: Dictionary = DataTranscendence.CLASSES[id]
		var want := "\"%s\": (\"%s\", %d, \"%s\")" % [id, d.family, d.stage, d.parent]
		ok(text.find(want) >= 0, "service.py knows %s" % want)
	done()

# ---- Eligibility ------------------------------------------------------------------------------------------------------

func test_eligibility_at_every_threshold_for_all_families() -> void:
	for fam in FAMILIES:
		for lvl in LEVELS:
			var h := hero(fam, lvl)
			var want := clampi(lvl / 60, 0, 2)
			eq(ClassTranscendence.eligible_steps(h), want, "%s L%d eligible steps" % [fam, lvl])
			eq(ClassTranscendence.available_steps(h), want, "%s L%d available steps" % [fam, lvl])
			var first := first_of(fam)
			eq(ClassTranscendence.can_transcend(h, first) == "", lvl >= 60, "%s L%d may take the first step" % [fam, lvl])
			for m in DataTranscendence.children_of(first):
				ok(ClassTranscendence.can_transcend(h, m) != "", "%s L%d cannot skip to %s" % [fam, lvl, m])
			if lvl < 60:
				eq(ClassTranscendence.can_transcend(h, first), "Requires level 60", "plain reason below 60")
	done()

func test_catch_up_both_steps_and_both_master_choices_per_family() -> void:
	for fam in FAMILIES:
		var first := first_of(fam)
		for m in DataTranscendence.children_of(first):
			var h := hero(fam, 121)
			h.progress.xp = 1234
			h.progress.free_points = 7
			h.progress.skill_points = 11
			h.progress.talent_points = 5
			h.progress.allocated[&"str"] = 9
			h.world_flags[&"some_story"] = true
			h.inventory.gold = 4321
			var gear := h.equipment.equipped_items().size()
			var bag := h.inventory.cells.filter(func(c): return c != null).size()
			var r1 := ClassTranscendence.transcend(h, first)
			ok(r1.ok, "%s: first step at 121" % fam)
			var r2 := ClassTranscendence.transcend(h, m)
			ok(r2.ok, "%s: master %s right after, same visit" % [fam, m])
			eq(ClassTranscendence.current_class_id(h), m, "current class %s" % m)
			eq(h.cls.id, fam, "the saved family never changes")
			eq(h.progress.level, 121, "level kept")
			eq(h.progress.xp, 1234, "xp kept")
			eq(h.progress.free_points, 7, "attribute points kept")
			eq(h.progress.skill_points, 11, "no skill point windfall")
			eq(h.progress.talent_points, 5, "no talent point windfall")
			eq(h.progress.allocated[&"str"], 9, "allocation kept")
			ok(h.world_flags.has(&"some_story"), "world progress kept")
			eq(h.inventory.gold, 4321, "gold kept")
			eq(h.equipment.equipped_items().size(), gear, "equipment kept")
			eq(h.inventory.cells.filter(func(c): return c != null).size(), bag, "bag kept")
			for sid in h.cls.starting_skills:
				ok(h.skill_rank(sid) > 0, "base skills kept")
			for id in [first, m]:
				for sid in DataTranscendence.info(id).skills:
					eq(h.skill_rank(sid), 1, "%s granted at rank 1" % sid)
				for tid in DataTranscendence.info(id).talents:
					eq(h.talent_tree.rank(tid), 1, "%s granted at rank 1" % tid)
			var other: StringName = DataTranscendence.children_of(first).filter(func(x): return x != m)[0]
			ok(ClassTranscendence.can_transcend(h, other) != "", "the sibling master stays closed")
			for sid in DataTranscendence.info(other).skills:
				eq(h.skill_rank(sid), 0, "sibling skill %s never learned" % sid)
			eq(ClassTranscendence.valid_next_choices(h).size(), 0, "no third advancement")
			var again := ClassTranscendence.transcend(h, m)
			ok(not again.ok, "repeating the advancement fails")
			eq(h.skill_tree.points_spent(), 1, "granted ranks are not paid points (only the starting skill)")
	done()

func test_master_needs_first_and_level_120() -> void:
	var h := hero(&"knight", 119)
	ok(ClassTranscendence.transcend(h, &"royal_guard").ok, "Royal Guard at 119")
	eq(ClassTranscendence.can_transcend(h, &"grand_paladin"), "Requires level 120 and Royal Guard", "master needs level 120")
	h.progress.level = 120
	eq(ClassTranscendence.can_transcend(h, &"grand_paladin"), "", "level 120 opens it")
	eq(ClassTranscendence.can_transcend(h, &"wildwarden").begins_with("Wildwarden is not a Knight class"), true, "other families refused")
	var h2 := hero(&"knight", 300)
	ok(ClassTranscendence.can_transcend(h2, &"dark_general").begins_with("Requires level 120 and Royal Guard"), "no skipping at 300")
	done()

# ---- Free ranks, respec, refunds ----------------------------------------------------------------------------------------

func test_granted_ranks_survive_respec_and_refund_only_paid() -> void:
	var h := hero(&"mage", 130)
	ClassTranscendence.transcend(h, &"arcanist")
	ClassTranscendence.transcend(h, &"void_sovereign")
	h.progress.skill_points = 10
	h.progress.talent_points = 6
	eq(h.spend_skill_point(&"vs_null_lance"), "", "buy rank 2 of a granted skill")
	eq(h.spend_skill_point(&"vs_null_lance"), "", "buy rank 3")
	eq(h.skill_rank(&"vs_null_lance"), 3, "rank 3 (1 granted + 2 bought)")
	eq(h.skill_tree.paid_rank(&"vs_null_lance"), 2, "two paid")
	eq(h.spend_talent_point(&"vs_entropy"), "", "buy a talent rank")
	eq(h.progress.skill_points, 8, "two points spent")
	eq(h.refund_skill_point(&"vs_null_lance"), "", "refund a paid rank")
	eq(h.progress.skill_points, 9, "one point back")
	eq(h.refund_skill_point(&"vs_null_lance"), "", "refund the other paid rank")
	ok(h.refund_skill_point(&"vs_null_lance").begins_with("Granted by Void Sovereign"), "the granted rank cannot be refunded")
	eq(h.skill_rank(&"vs_null_lance"), 1, "granted rank stays")
	eq(h.progress.skill_points, 10, "exactly the paid points came back")
	h.spend_skill_point(&"ar_aether_lance")
	var before_s := h.progress.skill_points + h.skill_tree.points_spent()
	var before_t := h.progress.talent_points + h.talent_tree.points_spent()
	eq(NpcServices.respec(h, false), "", "respec")
	eq(h.progress.skill_points + h.skill_tree.points_spent(), before_s, "respec returns paid skill points only")
	eq(h.progress.talent_points + h.talent_tree.points_spent(), before_t, "respec returns paid talent points only")
	for id in [&"arcanist", &"void_sovereign"]:
		for sid in DataTranscendence.info(id).skills:
			eq(h.skill_rank(sid), 1, "%s still granted after respec" % sid)
		for tid in DataTranscendence.info(id).talents:
			eq(h.talent_tree.rank(tid), 1, "%s still granted after respec" % tid)
	eq(ClassTranscendence.current_class_id(h), &"void_sovereign", "respec never changes the master class")
	eq(h.skill_tree.points_spent(), 1, "only the starting skill counts after respec")
	done()

func test_ranks_and_points_round_trip_through_save() -> void:
	var h := hero(&"shadowblade", 125)
	ClassTranscendence.transcend(h, &"nightstalker")
	ClassTranscendence.transcend(h, &"blood_sovereign")
	h.progress.skill_points = 5
	h.spend_skill_point(&"bs_crimson_rend")
	h.progress.talent_points = 2
	h.spend_talent_point(&"bs_hemomancy")
	var sp := h.progress.skill_points
	var tp := h.progress.talent_points
	for json in [false, true]:
		var b := roundtrip(h, json)
		eq(b.transcendence_path, h.transcendence_path, "path kept (json %s)" % json)
		eq(b.skill_rank(&"bs_crimson_rend"), 2, "granted + bought rank kept")
		eq(b.skill_tree.paid_rank(&"bs_crimson_rend"), 1, "the paid part stays paid")
		eq(b.talent_tree.rank(&"bs_hemomancy"), 2, "talent rank kept")
		eq(b.progress.skill_points, sp, "skill points identical")
		eq(b.progress.talent_points, tp, "talent points identical")
		eq(b.skill_rank(&"ns_umbral_lunge"), 1, "first-stage grant kept")
		eq(SaveSystem.legacy_identity(97, b), SaveSystem.legacy_identity(97, h), "import identity unchanged by advancement")
	var d := h.to_dict()
	eq(int(d.transcendence.schema), 1, "versioned optional field")
	eq(d.transcendence.path, ["nightstalker", "blood_sovereign"], "plain id strings")
	eq(String(d["class"]), "shadowblade", "saved class is the family")
	done()

func test_old_saves_load_unchanged_and_keep_eligibility() -> void:
	var h := hero(&"ranger", 121)
	var d := h.to_dict()
	ok(not d.has("transcendence"), "a hero who never advanced writes no new field")
	d.erase("transcendence")
	var b := HeroData.from_dict(d)
	eq(b.transcendence_path.size(), 0, "old save = starting class")
	eq(ClassTranscendence.current_class_name(b), "Hunter", "shown as Hunter")
	eq(ClassTranscendence.available_steps(b), 2, "level-121 old save may take both steps")
	ok(ClassTranscendence.transcend(b, &"tracker").ok and ClassTranscendence.transcend(b, &"starstrider").ok, "both steps at once")
	eq(b.transcend_note, "", "nothing to repair")
	done()

func test_corrupt_paths_recover_to_longest_valid_prefix() -> void:
	var cases := [
		[&"knight", 130, ["royal_guard", "dark_general", "grand_paladin"], ["royal_guard", "dark_general"]],
		[&"knight", 130, ["dark_general"], []],
		[&"knight", 130, ["tracker"], []],
		[&"knight", 100, ["royal_guard", "grand_paladin"], ["royal_guard"]],
		[&"knight", 50, ["royal_guard"], []],
		[&"mage", 200, ["arcanist", "bogus"], ["arcanist"]],
		[&"mage", 200, "arcanist", []],
		[&"mage", 200, [7, "arcanist"], []],
	]
	for c in cases:
		var res := ClassTranscendence.validate_path(c[0], c[1], c[2])
		eq((res.path as Array).map(func(x): return String(x)), c[3], "prefix of %s" % str(c[2]))
		ok(String(res.error) != "", "diagnostic for %s" % str(c[2]))
	# a loaded hero with a damaged record: sibling ranks dormant, never active, never refunded
	var h := hero(&"knight", 130)
	ClassTranscendence.transcend(h, &"royal_guard")
	ClassTranscendence.transcend(h, &"dark_general")
	h.progress.skill_points = 3
	h.spend_skill_point(&"dg_dread_cleave")
	var d := h.to_dict()
	d.transcendence.path = ["royal_guard", "grand_paladin"]
	d.progress.level = 100
	var sp_before := h.progress.skill_points
	var b := HeroData.from_dict(d)
	eq(b.transcendence_path, [&"royal_guard"] as Array[StringName], "only the valid prefix")
	ok(b.transcend_note != "", "explained")
	eq(b.skill_rank(&"dg_dread_cleave"), 0, "a dropped master's skill is not active")
	eq(b.skill_rank(&"rg_bastion_rush"), 1, "the valid first step keeps its grant")
	eq(b.progress.skill_points, sp_before, "no points minted from the dropped ranks")
	ok(b.dormant_ranks.get("skills", {}).has("dg_dread_cleave"), "the dropped ranks wait, kept")
	# schema mismatch / non-dictionary
	var d2 := h.to_dict()
	d2.transcendence = {"schema": 99, "path": ["royal_guard"]}
	eq(HeroData.from_dict(d2).transcendence_path.size(), 0, "unknown schema = starting class")
	d2.transcendence = "royal_guard"
	eq(HeroData.from_dict(d2).transcendence_path.size(), 0, "garbage = starting class")
	done()

func test_trees_are_per_identity_and_never_leak() -> void:
	var base_count := DB.tree(&"knight_skills").nodes.size()
	var base_talents := DB.tree(&"knight_talents").nodes.size()
	var a := hero(&"knight", 130)
	var b := hero(&"knight", 130)
	ClassTranscendence.transcend(a, &"royal_guard")
	ClassTranscendence.transcend(a, &"grand_paladin")
	eq(DB.tree(&"knight_skills").nodes.size(), base_count, "the shared skill tree is untouched")
	eq(DB.tree(&"knight_talents").nodes.size(), base_talents, "the shared talent tree is untouched")
	ok(b.skill_tree.tree.node(&"rg_bastion_rush").is_empty(), "another Knight never sees Royal Guard nodes")
	ok(a.skill_tree.tree.node(&"dg_dread_cleave").is_empty(), "a Grand Paladin's tree has no Dark General nodes")
	eq(a.skill_tree.tree.nodes.size(), base_count + 6, "six added skill nodes")
	eq(a.talent_tree.tree.nodes.size(), base_talents + 6, "six added talent nodes")
	eq(a.skill_tree.tree.page_count(), DB.tree(&"knight_skills").page_count() + 2, "a page per advancement")
	eq(a.talent_tree.tree.page_count(), 3, "talents: base page plus two")
	ok(ClassTranscendence.compose_tree(DB.tree(&"knight_skills"), [&"royal_guard"], false) == ClassTranscendence.compose_tree(DB.tree(&"knight_skills"), [&"royal_guard"], false),
		"one cached tree per identity")
	for n in a.skill_tree.tree.nodes:
		if n.has("granted_by"):
			eq(int(n.max_rank), TreeDef.LEVEL_MAX, "granted skills rise to 25")
	done()

func test_forged_sibling_ranks_cannot_grant_content() -> void:
	var h := hero(&"knight", 130)
	ClassTranscendence.transcend(h, &"royal_guard")
	ClassTranscendence.transcend(h, &"grand_paladin")
	h.skill_tree.ranks[&"dg_dread_cleave"] = 5
	eq(h.skill_rank(&"dg_dread_cleave"), 0, "forged sibling rank reads 0")
	ok(not h.learned_skills().has(&"dg_dread_cleave"), "never listed as learned")
	ok(not ClassTranscendence.skill_allowed(h, &"vs_null_lance"), "another family's skill is never allowed")
	var mods := h.talent_tree.modifiers()
	h.talent_tree.ranks[&"dg_dreadsteel"] = 10
	eq(h.talent_tree.modifiers().size(), mods.size(), "forged sibling talent ranks add nothing")
	done()

# ---- Equipment requirements --------------------------------------------------------------------------------------------

func test_every_equipment_base_has_a_valid_readable_requirement() -> void:
	var n := 0
	for b: ItemBaseDef in DB.item_bases.values():
		if not BH.CATEGORY_SLOTS.has(b.category):
			continue
		n += 1
		var req := ClassRequirements.of(b)
		eq(ClassRequirements.validate(req), "", "%s requirement valid" % b.id)
		ok(ClassRequirements.text(b).begins_with("For "), "%s says who may wear it" % b.id)
	ok(n > 400, "audited %d bases" % n)
	var m := ClassRequirements.manifest()
	eq(m.size(), n, "manifest covers every equipment base")
	done()

func test_thirty_six_pieces_bands_and_rules() -> void:
	var count := 0
	for id in DataTranscendence.CLASSES:
		var stage := DataTranscendence.stage_of(id)
		for gid in DataTranscendence.info(id).gear:
			var b := DB.item_base(gid)
			count += 1
			eq(b.level_req, 60 if stage == 1 else 120, "%s level" % gid)
			eq(b.drop_level, b.level_req, "%s drop band" % gid)
			eq(String(ClassRequirements.of(b).kind), "lineage" if stage == 1 else "exact", "%s rule kind" % gid)
			eq(b.class_hint, DataTranscendence.family_of(id), "%s loot preference is the family" % gid)
			ok(not DataTranscendenceGear.sources(gid).is_empty(), "%s has sources" % gid)
	eq(count, 36, "thirty-six pieces")
	eq(ClassRequirements.text(DB.item_base(&"tc_crownward_longsword")), "For Royal Guard and its master classes", "lineage text")
	eq(ClassRequirements.text(DB.item_base(&"tc_dawnstar_longsword")), "For Grand Paladin only", "exact text")
	eq(ClassRequirements.detail(DB.item_base(&"tc_crownward_longsword")), "Includes Dark General and Grand Paladin", "lineage detail")
	eq(ClassRequirements.text_of({"kind": "family", "ids": [&"knight"]}), "For Knight class", "family text")
	eq(ClassRequirements.text_of({"kind": "alternatives", "ids": [&"ranger", &"shadowblade"]}), "For Hunter or Shadowblade classes", "alternatives text")
	eq(ClassRequirements.text_of({"kind": "any", "ids": []}), "For any class", "any text")
	done()

func test_requirement_matrix_for_all_sixteen_identities() -> void:
	var identities: Array = DataTranscendence.FAMILIES.keys() + DataTranscendence.CLASSES.keys()
	for owner in DataTranscendence.CLASSES:
		for gid in DataTranscendence.info(owner).gear:
			var b := DB.item_base(gid)
			for who in identities:
				var line := DataTranscendence.ancestry(who)
				var want: bool = line.has(owner) if DataTranscendence.stage_of(owner) == 1 else who == owner
				eq(ClassRequirements.allows_line(ClassRequirements.of(b), line), want, "%s wearing %s" % [who, gid])
	# family rule: the whole family, nobody else
	var fam := {"kind": "family", "ids": [&"knight"]}
	for who in identities:
		eq(ClassRequirements.allows_line(fam, DataTranscendence.ancestry(who)), DataTranscendence.family_of(who) == &"knight", "family rule for %s" % who)
	# unknown ids never open a rule
	ok(not ClassRequirements.allows_line({"kind": "lineage", "ids": [&"no_such_class"]}, [&"knight", &"royal_guard"]), "unknown id closes")
	ok(ClassRequirements.validate({"kind": "family", "ids": [&"royal_guard"]}) != "", "family must name a family")
	ok(ClassRequirements.validate({"kind": "weird", "ids": []}) != "", "unknown kind reported")
	done()

func test_equip_checks_unbound_tempos_and_load_repair() -> void:
	var h := hero(&"knight", 130)
	h.tier = DataGuilds.MAX_RANK
	h.equipment.tier_rank = h.tier
	h.progress.allocated[&"str"] = 300
	var gp := DB.make_item(&"tc_dawnstar_longsword", BH.Rarity.ELITE, 120, 5)
	h.inventory.add(gp)
	eq(h.equip_from_inventory(gp), "For Grand Paladin only", "a base Knight cannot wield a Grand Paladin sword")
	ClassTranscendence.transcend(h, &"royal_guard")
	ClassTranscendence.transcend(h, &"dark_general")
	eq(h.equip_from_inventory(gp), "For Grand Paladin only", "a Dark General cannot either")
	var unbound := DataSpecialWeapons.unbound(&"tc_dawnstar_longsword", 130)
	if unbound:
		h.inventory.add(unbound)
		eq(h.equip_from_inventory(unbound), "For Grand Paladin only", "Unbound skips level and attributes, never the class")
	var rg := DB.make_item(&"tc_crownward_longsword", BH.Rarity.ELITE, 60, 6)
	h.inventory.add(rg)
	eq(h.equip_from_inventory(rg), "", "Royal Guard gear stays valid for its master classes")
	var dg := DB.make_item(&"tc_dreadmarshal_greatsword", BH.Rarity.ELITE, 120, 7)
	h.inventory.add(dg)
	eq(h.equip_from_inventory(dg), "", "Dark General gear for the Dark General")
	# Tempos: the transcendence pieces are not theirs
	var t := TempoData.new()
	t.class_id = &"swordsman"
	ok(TempoRules.equip_error(h, t, rg, &"main_weapon").contains("not for Tempos"), "Tempos refuse transcendence gear")
	# load repair: a forced illegal piece is taken off and kept (bag full: the recovery queue)
	# only the forced piece is a Dawnstar: drop the bag copies first
	for i in h.inventory.cells.size():
		var c: ItemInstance = h.inventory.cells[i]
		if c != null and c.base.id == &"tc_dawnstar_longsword":
			h.inventory.cells[i] = null
	var d := h.to_dict()
	d.equipment["main_weapon"] = gp.to_dict()
	var cells: Array = d.inventory
	for i in cells.size():
		if cells[i] == null:
			cells[i] = DB.make_item(&"iron_shard", BH.Rarity.COMMON, 1, 100 + i).to_dict()
	d.inventory = cells
	var b := HeroData.from_dict(d)
	eq(b.equipment.get_item(&"main_weapon"), null, "the illegal piece is not worn")
	ok(b.gear_note.contains("did not fit your class"), "the player is told (%s)" % b.gear_note)
	var held := b.equipment.recovered_items.filter(func(it): return it.base.id == &"tc_dawnstar_longsword").size() \
		+ b.inventory.cells.filter(func(c): return c != null and c.base.id == &"tc_dawnstar_longsword").size()
	eq(held, 1, "kept exactly once (recovery or bag), never deleted or duplicated")
	var b2 := roundtrip(b)
	var held2 := b2.equipment.recovered_items.filter(func(it): return it.base.id == &"tc_dawnstar_longsword").size() \
		+ b2.inventory.cells.filter(func(c): return c != null and c.base.id == &"tc_dawnstar_longsword").size()
	eq(held2, 1, "the recovered piece survives another save")
	done()

func test_class_sets_and_class_powers_are_family_gear() -> void:
	var sets := 0
	for b: ItemBaseDef in DB.item_bases.values():
		if b.set_id != &"" and b.class_hint != &"" and b.category != &"accessory" and BH.CATEGORY_SLOTS.has(b.category) and b.class_req.is_empty():
			eq(String(ClassRequirements.of(b).kind), "family", "%s is its family's" % b.id)
			sets += 1
	ok(sets > 20, "class set pieces audited (%d)" % sets)
	eq(String(ClassRequirements.of(DB.item_base(&"iron_longsword")).kind), "any", "ordinary gear stays shared")
	eq(String(ClassRequirements.of(DB.item_base(&"ashwood_staff")).kind), "any", "a plain staff stays shared (class_hint is only a preference)")
	done()

func test_armory_and_loot_reach_the_new_gear_at_the_right_levels() -> void:
	var def := DB.shop(&"grand_master_armory")
	ok(def != null, "the Grand Master's armory exists")
	var h := hero(&"ranger", 121)
	var s := Shop.open(def, h)
	eq(s.stock.size(), 0, "a Hunter who has not advanced sees nothing they cannot wear")
	ClassTranscendence.transcend(h, &"tracker")
	h.shops.erase(&"grand_master_armory")
	s = Shop.open(def, h)
	var ids := s.stock.map(func(e): return String(e.item.base.id))
	ids.sort()
	eq(ids, ["tc_quarry_compass", "tc_trackers_leathers", "tc_trailkeeper_bow"], "a Tracker sees the Tracker pieces")
	ClassTranscendence.transcend(h, &"wildwarden")
	s = Shop.open(def, h)       # an existing stock gains the newly wearable pieces without a reroll
	ids = s.stock.map(func(e): return String(e.item.base.id))
	ok(ids.has("tc_briarheart_bow") and not ids.has("tc_starfall_crossbow"), "a Wildwarden gets Wildwarden pieces, never Starstrider ones")
	# loot: never below the band; a hero's own class pieces turn up in their class-fit rolls
	var r := rng(42)
	var seen := {}
	var low_ok := true
	for i in 4000:
		var b := ItemGenerator.random_base(r, 59, [], &"tracker")
		if b != null and String(b.id).begins_with("tc_"):
			low_ok = false
	ok(low_ok, "nothing transcendent below level 60")
	for i in 6000:
		var b := ItemGenerator.random_base(r, 125, [], &"wildwarden")
		if b and String(b.id).begins_with("tc_"):
			seen[String(b.id)] = true
	ok(seen.has("tc_briarheart_bow") or seen.has("tc_livingwood_leathers"), "Wildwarden pieces drop for a Wildwarden (%s)" % str(seen.keys()))
	ok(ItemGenerator.class_fit(DB.item_base(&"tc_briarheart_bow"), &"wildwarden"), "class fit knows the master class")
	ok(not ItemGenerator.class_fit(DB.item_base(&"tc_starfall_crossbow"), &"wildwarden"), "the sibling's piece is not class fit")
	ok(not ItemGenerator.class_fit(DB.item_base(&"tc_trailkeeper_bow"), &"ranger"), "a Hunter who has not advanced is not offered Tracker gear")
	done()

func test_item_upgrades_and_serialization_keep_requirements() -> void:
	var it := DB.make_item(&"tc_eventide_staff", BH.Rarity.MASTER, 130, 9)
	it.enchant_rank = 0
	var back := ItemInstance.from_dict(JSON.parse_string(JSON.stringify(it.to_dict())))
	eq(back.base.id, &"tc_eventide_staff", "base kept")
	eq(ClassRequirements.text(back.base), "For Void Sovereign only", "requirement kept")
	ok(it.damage_range().y > it.base.damage_max, "scales with its item level like any weapon")
	done()

# ---- Future Transcendent Dungeons ---------------------------------------------------------------------------------------

func test_dungeon_requirement_query() -> void:
	var gp: Array = [&"knight", &"royal_guard", &"grand_paladin"]
	var hunter: Array = [&"ranger"]
	eq(ClassTranscendence.requirement_check_line(gp, {}), "", "no rule: everyone")
	eq(ClassTranscendence.requirement_check_line(hunter, {"min_stage": 1}), "Requires a transcended class", "stage gate")
	eq(ClassTranscendence.requirement_check_line(gp, {"min_stage": 2}), "", "a master passes stage 2")
	eq(ClassTranscendence.requirement_check_line(gp, {"families": [&"mage", &"ranger"]}), "For Mage or Hunter classes", "family gate")
	eq(ClassTranscendence.requirement_check_line(gp, {"lineages": [&"royal_guard"]}), "", "lineage gate")
	eq(ClassTranscendence.requirement_check_line(gp, {"classes": [&"dark_general"]}), "For Dark General only", "exact gate")
	ok(ClassTranscendence.requirement_check_line(gp, {"classes": [&"mystery"]}).contains("unknown class"), "unknown ids never pass")
	var h := hero(&"knight", 130)
	ok(ClassTranscendence.requirement_check(h, {"min_stage": 1}) != "", "callable on a real hero")
	done()
