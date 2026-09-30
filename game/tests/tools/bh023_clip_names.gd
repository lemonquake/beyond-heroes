extends SceneTree
func _initialize() -> void:
	for p in OS.get_cmdline_user_args():
		var n: Node = load(p).instantiate()
		var ap: AnimationPlayer = n.find_children("*", "AnimationPlayer", true, false)[0]
		var l := ap.get_animation_list()
		print("NAMES ", p, " ", l.size(), " block_loop=", ap.has_animation("block_loop"), " block=", ap.has_animation("block"), " whirl=", ap.has_animation("whirlwind"), " bow_draw_hold=", ap.has_animation("bow_draw_hold"))
	quit()
