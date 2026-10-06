extends TestCase
## Class Transcendence, stage 4 (without a network): the profile guard, the path a peer may claim, the class line under
## another player's name, themes, and the master glow (present for masters only, rebuilt only when the class changes,
## never on Tempos). The two-process probes (tools/net_probes.py transcend, server/integration_probe.py --stages
## transcend) cover the real network.

var holder: Node3D

func _init() -> void:
	strict = true

func test_profile_guard_keeps_only_valid_paths() -> void:
	var good := NetGuard.clean_profile({"name": "A", "cls": "knight", "level": 130, "path": "royal_guard,grand_paladin"})
	eq(String(good.path), "royal_guard,grand_paladin", "a valid path survives")
	var other_family := NetGuard.clean_profile({"name": "A", "cls": "ranger", "level": 130, "path": "royal_guard,grand_paladin"})
	eq(String(other_family.path), "", "another family's path is dropped")
	var too_low := NetGuard.clean_profile({"name": "A", "cls": "knight", "level": 100, "path": "royal_guard,grand_paladin"})
	eq(String(too_low.path), "royal_guard", "a master above the level is dropped, the valid prefix kept")
	var junk := NetGuard.clean_profile({"name": "A", "cls": "mage", "level": 200, "path": "arcanist,void_sovereign,archmage", "label": "Emperor",
		"glow": "res://x.gdshader", "color": "#ff00ff"})
	eq(String(junk.path), "arcanist,void_sovereign", "never more than two steps")
	ok(not junk.has("label") and not junk.has("glow") and not junk.has("color"), "free text, shader and colour claims are dropped")
	var weird := NetGuard.clean_profile({"name": "A", "cls": "mage", "level": 200, "path": 42})
	eq(String(weird.path), "", "a non-text path reads as the starting class")
	var unknown := NetGuard.clean_profile({"name": "A", "cls": "warlock", "level": 200, "path": "arcanist"})
	eq(String(unknown.path), "", "an unknown family has no path")
	done()

func test_peer_path_reads_text_from_the_wire() -> void:
	# regression: the comma text was split into a PackedStringArray the validator did not accept (every peer read as
	# their starting class in the first two-client run)
	eq(ClassTranscendence.peer_class_id(&"ranger", 125, "tracker,starstrider"), &"starstrider", "wire text parses")
	eq(ClassTranscendence.peer_class_id(&"ranger", 125, ""), &"ranger", "empty = starting class")
	eq(ClassTranscendence.peer_class_id(&"ranger", 70, "tracker,starstrider"), &"tracker", "level-checked")
	eq(ClassTranscendence.peer_class_id(&"ranger", 125, "x".repeat(200)), &"ranger", "oversized text ignored")
	var h := Game.new_hero(&"shadowblade", "Wire")
	h.progress.level = 130
	ClassTranscendence.transcend(h, &"nightstalker")
	ClassTranscendence.transcend(h, &"phantom_reaper")
	eq(ClassTranscendence.peer_class_id(&"shadowblade", 130, ClassTranscendence.path_text(h)), &"phantom_reaper", "round trip")
	done()

func test_class_line_on_another_players_hero() -> void:
	holder = Node3D.new()
	host.add_child(holder)
	var saved_peers := Net.peers.duplicate(true)
	Net.peers = {7: {"name": "Friend", "cls": "knight", "level": 130, "device": "PC", "path": "royal_guard"}}
	var av := NetAvatar.new().setup(7, "p", {"name": "Friend", "lvl": 130, "mhp": 100.0, "hp": 100.0})
	holder.add_child(av)
	ok(av._sub.text.begins_with("Level 130 Royal Guard"), "the class line under the name (%s)" % av._sub.text)
	ok(av._sub.position == Vector3(0, 2.42, 0) and av._tag.offset == Vector2(0, 40), "the class line keeps its place beneath the name")
	ok(av._sub.modulate.is_equal_approx(ClassTranscendence.label_color(&"royal_guard")), "in the Royal Guard colour")
	av.set_appearance({"model": HeroLook.MODEL, "scale": 1.0, "tint": Color.WHITE})
	eq(av.get_node_or_null(^"ClassGlow"), null, "no glow node")
	Net.peers[7].path = "royal_guard,grand_paladin"
	Net.roster_updated.emit()
	ok(av._sub.text.begins_with("Level 130 Grand Paladin"), "updated in place (%s)" % av._sub.text)
	eq(av.class_id, &"grand_paladin", "the avatar knows the master class")
	eq(av.get_node_or_null(^"ClassGlow"), null, "masters wear no glow")
	var sig := av.get_node_or_null(^"ClassSignature")
	ok(sig != null, "the trait node is there to draw the Grand Paladin's bursts")
	Net.roster_updated.emit()
	ok(av.get_node_or_null(^"ClassSignature") == sig, "not rebuilt while the class is unchanged")
	Net.peers[7].path = ""
	Net.roster_updated.emit()
	eq(av.get_node_or_null(^"ClassSignature"), null, "no stale traits on a starting class")
	ok(av._sub.text.begins_with("Level 130 Knight"), "back to Knight")
	# a Tempo of that player is never relabelled or given the owner's traits
	var tempo := NetAvatar.new().setup(7, "t3", {"name": "Spirit", "lvl": 130, "mhp": 100.0, "hp": 100.0})
	Net.peers[7].path = "royal_guard,grand_paladin"
	holder.add_child(tempo)
	tempo.set_appearance({"model": HeroLook.MODEL, "scale": 1.0, "tint": Color.WHITE})
	eq(tempo._sub, null, "Tempos have no class line")
	eq(tempo.get_node_or_null(^"ClassSignature"), null, "Tempos never get the owner's traits")
	holder.free()
	Net.peers = saved_peers
	done()

func test_class_label_colours_are_readable() -> void:
	# readable on dark ground: never the near-black Dark General charcoal itself
	ok(ClassTranscendence.label_color(&"dark_general").get_luminance() > 0.3, "Dark General's line is readable")
	eq(ClassTranscendence.label_color(&"knight"), UITheme.GOLD, "starting classes keep the familiar gold")
	done()

func test_showcase_and_cards_use_the_saved_class() -> void:
	var h := Game.new_hero(&"mage", "Card")
	h.progress.level = 125
	ClassTranscendence.transcend(h, &"arcanist")
	ClassTranscendence.transcend(h, &"archmage")
	var d: Dictionary = JSON.parse_string(JSON.stringify(h.to_dict()))
	eq(ClassTranscendence.class_of_save(d), &"archmage", "a save card reads Archmage")
	d.progress.level = 100
	eq(ClassTranscendence.class_of_save(d), &"arcanist", "and never more than the level allows")
	d.erase("transcendence")
	eq(ClassTranscendence.class_of_save(d), &"mage", "an old save reads Mage")
	ok(Net.PROTOCOL >= 20, "the online version moved with the new profile field (bh-040 moved it again, to 21)")
	done()
