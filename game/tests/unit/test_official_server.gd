extends TestCase

func test_twelve_player_capacity() -> void:
	eq(Net.MAX_PLAYERS, 12, "official capacity excludes the headless coordinator")
	eq(Net.MAX_CLIENTS, 11, "custom capacity counts the host")
	eq(Net.PROTOCOL, 15, "official and custom realm handshake has a separate protocol")
	done()

func test_endpoint_requires_verified_https_origin() -> void:
	for endpoint in ["https://localhost:8443", "https://192.168.1.20:8443", "https://server.example.com"]:
		ok(Official.valid_endpoint(endpoint), "valid HTTPS origin")
	for endpoint in ["http://localhost:8443", "https://", "https://name:password@example.com", "https://example.com/secret", "https://example.com?token=x", "https://example.com\n"]:
		ok(not Official.valid_endpoint(endpoint), "reject unsafe origin")
	done()

func test_official_scope_never_reads_or_writes_local_heroes() -> void:
	var previous := SaveSystem.scope
	SaveSystem.scope = "official"
	var hero := Game.new_hero(&"knight", "ServerOnly")
	ok(not SaveSystem.save_hero(hero, 98), "official hero cannot write a local slot")
	eq(SaveSystem.read_slot(98), {}, "official hero cannot fall back to a local slot")
	SaveSystem.scope = previous
	done()

func test_custom_room_paths_preserve_original_offline_slots() -> void:
	var previous := SaveSystem.scope
	var old_room := SaveSystem.custom_room
	SaveSystem.scope = "legacy"
	var original := SaveSystem.slot_path(0)
	ok(SaveSystem.choose_custom_room("0123456789abcdef0123456789abcdef"), "valid room identity")
	var first := SaveSystem.slot_path(0)
	ok(first != original, "custom character cannot replace an offline save")
	ok(SaveSystem.choose_custom_room("fedcba9876543210fedcba9876543210"), "second room identity")
	ok(first != SaveSystem.slot_path(0), "custom rooms have separate characters")
	ok(not SaveSystem.choose_custom_room("../../slot_0"), "room cannot escape its save directory")
	SaveSystem.scope = previous
	SaveSystem.custom_room = old_room
	done()

func test_offline_character_roundtrip_does_not_require_an_account() -> void:
	var previous := SaveSystem.scope
	SaveSystem.scope = "legacy"
	var slot := 100000 + randi_range(0, 1000000)
	while FileAccess.file_exists(SaveSystem.slot_path(slot)):
		slot += 1
	var hero := Game.new_hero(&"ranger", "OfflineCheck")
	hero.inventory.gold = 1234
	ok(SaveSystem.save_hero(hero, slot), "offline writes without authentication")
	var loaded := SaveSystem.load_hero(slot)
	ok(loaded != null, "offline reloads without a server")
	if loaded:
		eq(loaded.hero_name, "OfflineCheck", "offline identity survives")
		eq(loaded.inventory.gold, 1234, "offline progress survives")
	SaveSystem.delete_slot(slot)
	SaveSystem.scope = previous
	done()

func test_main_menu_requires_a_mode_and_enables_offline_immediately() -> void:
	var previous := SaveSystem.scope
	var menu := MainMenu.new()
	host.add_child(menu)
	for button in menu._buttons:
		if button.name in ["continue", "new", "load"]:
			ok(button.disabled, "initial main menu waits for realm selection")
	ok(menu._server_menu != null, "server chooser appears first")
	menu._server_menu.selected.emit("offline", {})
	eq(SaveSystem.scope, "legacy", "offline chooses existing local slots")
	for button in menu._buttons:
		if button.name == "new":
			ok(not button.disabled, "offline play available without waiting for server status")
	menu.queue_free()
	await host.get_tree().process_frame
	SaveSystem.scope = previous
	done()
