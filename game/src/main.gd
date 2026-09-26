extends Node
## Boot scene. Until the main menu / character selection land, it starts a Wanderer (Knight) in the map given by
## `--map=<id>` (default: the Hero Sanctuary) at `--spawn=<id>` and hands it the temporary map explorer pawn.

func _ready() -> void:
	var args := {}
	for a in OS.get_cmdline_user_args() + OS.get_cmdline_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
	var world := Node3D.new()
	world.name = "World"
	add_child(world)
	Game.world_parent = world
	if Game.hero == null:
		var h := HeroData.new()
		h.setup(DB.class_def(&"knight"), "Wanderer")
		h.init_new()
		Game.hero = h
	var map_id := StringName(args.get("map", String(Game.hero.current_map)))
	if DB.map_def(map_id) == null:
		map_id = &"sanctuary"
	var explorer := MapExplorer.new()
	explorer.name = "Explorer"
	Game.player = explorer
	Game.load_map(map_id, StringName(args.get("spawn", "start")))
