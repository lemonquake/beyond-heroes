class_name GuildFighter
extends QuakeAlly
## bh-027: a member of the hero's guild answering Call to Arms (GuildSummons): a whole hero of their own class, level
## and gear, fighting beside the Guildmaster with the Quake Team's AI for as long as the call lasts. Unlike the Quake
## Team they fight in multiplayer too (every other player sees them, like a Tempo), they never go shopping, and their
## trait (DataGuildPassives.TRAITS) shapes how they fight.

var member_id := 0
var trait_id: StringName = &""
var guild_name := ""
var guild_color := Color(1.0, 0.86, 0.5)

## The formation behind the leader: two ranks of three, wide enough that six fighters never stack.
const RANKS := [Vector2(-2.6, 3.2), Vector2(2.6, 3.2), Vector2(0.0, 4.4), Vector2(-4.4, 5.4), Vector2(4.4, 5.4), Vector2(0.0, 6.8)]

func bind_member(m: QuakeMate, member: Dictionary, p_player: Node3D, p_slot: int, gname: String, gcolor: Color) -> GuildFighter:
	member_id = int(member.id)
	trait_id = StringName(member.get("trait", ""))
	guild_name = gname
	guild_color = gcolor
	bind_mate(m, p_player, p_slot)
	name = "GuildFighter_%d" % member_id
	return self

func _ready() -> void:
	super._ready()
	add_to_group(&"guild_fighter")

func _online_ok() -> bool:
	return true

func _in_town() -> bool:
	return false

func _formation_point() -> Vector3:
	var p := owner_player
	var f: Vector3 = p.global_transform.basis.z.slide(Vector3.UP).normalized()
	if f.length() < 0.1:
		f = Vector3.BACK
	var side := f.cross(Vector3.UP)
	var o: Vector2 = RANKS[slot_index % RANKS.size()]
	return p.global_position - f * o.y + side * o.x

func _spirit_look() -> void:
	super._spirit_look()
	visual.set_rim(guild_color.lightened(0.2), 0.26)
	if _light:
		_light.light_color = guild_color.lightened(0.3)

func _update_plate() -> void:
	if _plate == null:
		return
	_plate_level = hero.progress.level
	_plate.text = "%s  Lv %d\n%s" % [mate.display_name(), _plate_level, guild_name]
	_plate.modulate = guild_color.lightened(0.35)

func rebuild_stats() -> void:
	var mods := status.stat_modifiers()
	mods.append_array(DataTempos.mods_from(data.trait_def().get("mods", []), data.trait_def().get("name", "Trait")))
	mods.append_array(DataGuildPassives.trait_mods(trait_id))
	if _smoke_t > 0.0:
		mods.append(StatModifier.inc(&"evasion", 1.0, "Smoke"))
	stats = hero.compute_stats(mods)
	level = hero.progress.level
	if _plate and _plate_level != level:
		_update_plate()

func _fall_notice() -> void:
	Events.notify.emit("%s was knocked out - back in the fight in a moment." % mate.display_name(), &"error")
	GuildSummons.on_fighter_fell(self)

## The call is over: a bow, a flash of the guild's colour, gone.
func depart() -> void:
	if not is_inside_tree():
		queue_free()
		return
	FX.spawn(VFXLib.particles(Color(guild_color, 0.8), 26, 0.9, true, 0.1, 2.2, 180.0, Vector3(0, 1.5, 0), 0.5), global_position + Vector3.UP)
	queue_free()
