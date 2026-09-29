extends TestCase
## Regression coverage for the real dialogue handoff and crystal purchase controls.

func _init() -> void:
	strict = true

func test_dialogue_socket_shop_purchase() -> void:
	var old_hero := Game.hero
	var old_ui := Game.ui_root
	var old_blocking := Game.ui_blocking
	var ui := UIRoot.new()
	Game.hero = Game.new_hero(&"knight", "CrystalTest")
	Game.hero.inventory.gold = 50000
	host.add_child(ui)
	for id in [&"ysolde", &"anselm", &"dagna"]:
		var def := DB.npc(id)
		Game.hero.mark_dialogue_visited(id, "first")
		ui.dialogue.start_def(def)
		ui.dialogue._finish_typing()
		ui.dialogue.session.choose(0)
		await host.get_tree().process_frame
		var socket := ui.window(&"socketing") as SocketWindow
		ok(socket.visible, "%s: conversation opens socket work" % id)
		eq(socket.specialist, def.display_name, "specialist survives dialogue close")
		eq(socket.shop_id, def.shop, "shop survives dialogue close")
		var shop := ui.window(&"shop") as ShopWindow
		shop.mode = "buyback"
		shop.filter = "weapons"
		socket._open_shop()
		await host.get_tree().process_frame
		ok(shop.visible, "Buy Crystals opens the merchant")
		eq(shop.shop.def.id, def.shop, "the right merchant opens")
		eq(shop.mode, "buy", "buyback is reset")
		eq(shop.filter, "all", "old filter cannot hide crystals")
		ok(shop._entries().size() >= 7, "all starter crystal families visible")
		var slot := shop._stock_grid.get_child(0) as ItemSlot
		var before := Game.hero.inventory.gold
		var price := shop.shop.buy_price(slot.index, Game.hero)
		shop._on_stock_clicked(slot, MOUSE_BUTTON_LEFT, false, false)
		ok(ui.confirm.visible, "click or tap opens purchase confirmation")
		eq(Game.hero.inventory.gold, before, "confirmation has not charged yet")
		ui.confirm._confirm()
		eq(Game.hero.inventory.gold, before - price, "purchase charges exactly once")
		ok(not Sockets.crystals_for(Game.hero, Sockets.pieces(Game.hero)[0]).is_empty(), "bought crystal available to socket")
		ui.close_all()
	ui.free()
	Game.hero = old_hero
	Game.ui_root = old_ui
	Game.ui_blocking = old_blocking
	done()

func test_saved_crystal_stock_recovers_and_unlocks() -> void:
	var h := Game.new_hero(&"knight", "StockTest")
	h.progress.level = 11
	var def := DB.shop(&"lapidary_crystals")
	var s := Shop.open(def, h)
	eq(s.stock.size(), 7, "fragments before level 12")
	h.progress.level = 12
	s = Shop.open(def, h)
	eq(s.stock.size(), 14, "shards unlock immediately without waiting three levels")
	var sold := DB.make_item(&"health_potion")
	s.buyback.append({"item": sold, "price": 10})
	s.stock.clear()
	s.save(h)
	s = Shop.open(def, h)
	eq(s.stock.size(), 14, "empty stock from an earlier save is repaired")
	eq(s.buyback.size(), 1, "buyback survives repair")
	s = Shop.open(def, h)
	eq(s.stock.size(), 14, "reopening never duplicates stock")
	done()
