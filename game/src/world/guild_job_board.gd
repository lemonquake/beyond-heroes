class_name GuildJobBoard
extends Node3D
## A guild's job board in the Guild House (bh-016): Interact opens GuildJobsWindow on that guild's page.

var guild: StringName = &"swordfin"
var interact_range := 2.6
var _plate: Label3D

func _ready() -> void:
	add_to_group(&"interactable")
	var g := DataGuilds.guild(guild)
	_plate = Label3D.new()
	_plate.text = "%s Jobs\n[Bounties · Errands · Pay]" % String(g.get("short", "Guild"))
	_plate.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	_plate.fixed_size = true
	_plate.pixel_size = 0.0008
	_plate.font = UITheme.body_bold()
	_plate.font_size = 22
	_plate.outline_size = 8
	_plate.outline_modulate = Color(0, 0, 0, 0.85)
	_plate.modulate = (g.get("color", UITheme.PARCHMENT) as Color).lightened(0.45)
	_plate.position.y = 2.7
	_plate.visible = false
	add_child(_plate)

func _process(_d: float) -> void:
	var p := Game.player as Node3D
	_plate.visible = p != null and is_instance_valid(p) and p.global_position.distance_to(global_position) < 7.0

func can_interact(_p: Node) -> bool:
	return not Game.travelling

func interact_text() -> String:
	return "Read the %s job board" % String(DataGuilds.guild(guild).get("short", "guild"))

func interact_anim() -> StringName:
	return &""

func interact(_p: Node) -> void:
	if Game.ui_root and Game.ui_root.has_method(&"open_guild_jobs"):
		Game.ui_root.open_guild_jobs(guild)
