class_name DungeonRuntime
extends Node
## Lives on every dungeon floor (bh-012, added by dungeon.gd). Breaks the floor's seal when its Seal Keepers are cleared
## (floors 1..N-2) or its champion falls (floor N-1), and on the last floor records the boss's defeat: the "cleared"
## flag wakes the way home and (bh-013) the raid starts the dungeon's recovery — its camps stay empty for 30 min to
## 2 h, the boss never returns, and its Usurper takes the sanctum. A recovering floor tells the hero why it is quiet.

var dungeon: StringName
var floor_n := 1

func _ready() -> void:
	Events.camp_cleared.connect(_on_camp_cleared)
	Events.miniboss_defeated.connect(_on_miniboss)
	Events.actor_died.connect(_on_died)
	_quiet_notice.call_deferred()

func _exit_tree() -> void:
	if Events.camp_cleared.is_connected(_on_camp_cleared):
		Events.camp_cleared.disconnect(_on_camp_cleared)
	if Events.miniboss_defeated.is_connected(_on_miniboss):
		Events.miniboss_defeated.disconnect(_on_miniboss)
	if Events.actor_died.is_connected(_on_died):
		Events.actor_died.disconnect(_on_died)

func map_id() -> StringName:
	return DataDungeons.map_id(dungeon, floor_n)

func _quiet_notice() -> void:
	if floor_n > DataDungeons.floor_count(dungeon) or Game.hero == null or not is_inside_tree() or not DataDungeons.recovering(Game.hero, dungeon):
		return
	Events.notify.emit("The halls are quiet: %s is still recovering from your raid. Its monsters return in %s." % [
		DataDungeons.get_def(dungeon).name, DataDungeons.fmt_minutes(DataDungeons.recover_left(Game.hero, dungeon))], &"info")

func _on_camp_cleared(map: StringName, zone: String, _left: int, _total: int) -> void:
	if map == map_id() and zone == DataDungeons.SEAL_ZONE:
		break_seal()

func _on_miniboss(id: StringName) -> void:
	if floor_n == DataDungeons.champion_floor(dungeon) and id == StringName(DataDungeons.get_def(dungeon).miniboss.id):
		break_seal()

## Open this floor's descent portal for good (idempotent).
func break_seal() -> bool:
	var flag := DataDungeons.seal_flag(dungeon, floor_n)
	if Game.hero == null or Game.has_flag(flag) or floor_n > DungeonGrowth.total(Game.hero, dungeon):
		return false
	Game.set_world_flag(flag, true)
	var message := "The seal breaks. The way home is open." if floor_n == DungeonGrowth.total(Game.hero, dungeon) else "The seal breaks. The way down to %s is open." % DataDungeons.floor_title(dungeon, floor_n + 1)
	Events.notify.emit(message, &"discovery")
	Audio.play_ui(&"level_up")
	return true

func _on_died(actor: Node, _killer: Node) -> void:
	if not (actor is Enemy) or Game.hero == null:
		return
	var e := actor as Enemy
	if not e.is_boss or e.def.id != DataDungeons.get_def(dungeon).get("boss", &""):
		return
	var id := e.def.id
	var rec: Dictionary = Game.hero.miniboss_log.get(id, {"kills": 0, "at": 0.0})
	Game.hero.miniboss_log[id] = {"kills": int(rec.kills) + 1, "at": Game.hero.play_time}
	if not Game.has_flag(DataDungeons.cleared_flag(dungeon)):
		Game.set_world_flag(DataDungeons.cleared_flag(dungeon), true)
	var raid := DataDungeons.record_raid(Game.hero, dungeon)
	Game.hero.add_clear()
	Events.notify.emit("%s is raided! The way home is open. Its halls recover in %s; its lord will not return." % [
		DataDungeons.get_def(dungeon).name, DataDungeons.fmt_minutes(float(raid.until) - float(raid.at))], &"discovery")
