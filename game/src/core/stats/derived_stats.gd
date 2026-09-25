class_name DerivedStats
extends RefCounted
## Snapshot of an actor's final combat statistics plus a per-stat explanation of how it was computed.

var values := {}                 # StringName -> float
var explain := {}                # StringName -> PackedStringArray (tooltip lines)
var level := 1
var affinity := Elements.PHYSICAL
var loadout: WeaponLoadout
var flags := {}                  # talent/unique flags: StringName -> float (magnitude)
var immune := {}                 # element int -> true
var absorb := {}                 # element int -> fraction healed (on top of 100% resist)

func get_stat(k: StringName, default_value := 0.0) -> float:
	return values.get(k, default_value)

func set_stat(k: StringName, v: float, lines: PackedStringArray = PackedStringArray()) -> void:
	values[k] = v
	if not lines.is_empty():
		explain[k] = lines

func has_flag(f: StringName) -> bool:
	return flags.has(f)

func flag(f: StringName, default_value := 0.0) -> float:
	return flags.get(f, default_value)

func duplicate_stats() -> DerivedStats:
	var d := DerivedStats.new()
	d.values = values.duplicate()
	d.explain = explain.duplicate()
	d.level = level
	d.affinity = affinity
	d.loadout = loadout
	d.flags = flags.duplicate()
	d.immune = immune.duplicate()
	d.absorb = absorb.duplicate()
	return d
