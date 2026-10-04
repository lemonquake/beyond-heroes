class_name RelicCache
## Opening a Relic Cache (bh-012): roll its gear (ItemGenerator.relic_items), put it in the bag (or at the hero's feet
## when the bag is full) and show the reveal. Pure enough to call from tests with a null player.

static func open(hero: HeroData, tier: int, player: Node3D = null, rng: RandomNumberGenerator = null) -> Array:
	if hero == null:
		return []
	if rng == null:
		rng = RandomNumberGenerator.new()
		rng.randomize()
	var mf := 0.0
	if player is Player:
		mf = (player as Player).stats.get_stat(&"magic_find")
	var items := ItemGenerator.relic_items(tier, hero.progress.level, rng, mf, ClassTranscendence.current_class_id(hero) if hero.cls else &"")
	for it: ItemInstance in items:
		if hero.inventory.add(it) > 0 and player != null and player.is_inside_tree():
			Loot.spawn_item(it, player.global_position, rng.randf() * TAU, 1.2)
	hero.inventory.changed.emit()
	var c: Dictionary = DataRelics.CACHES[clampi(tier, 0, DataRelics.CACHES.size() - 1)]
	if Game.ui_root and is_instance_valid(Game.ui_root) and Game.ui_root.has_method(&"reveal"):
		Game.ui_root.reveal(String(c.name), items.map(func(it): return GachaRevealWindow.item_card(it)))
	return items
