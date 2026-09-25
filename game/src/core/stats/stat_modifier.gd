class_name StatModifier
extends RefCounted
## One modification of one stat. Final = (base + sum FLAT) * (1 + sum INC) * product(1 + MORE).

enum Op { FLAT, INC, MORE }

var stat: StringName
var op: Op = Op.FLAT
var value: float = 0.0
var source: String = ""   # human-readable origin, used in stat tooltips ("Iron Helm", "Talent: Bulwark")

func _init(p_stat: StringName = &"", p_op: Op = Op.FLAT, p_value: float = 0.0, p_source: String = "") -> void:
	stat = p_stat
	op = p_op
	value = p_value
	source = p_source

static func flat(s: StringName, v: float, src: String = "") -> StatModifier:
	return StatModifier.new(s, Op.FLAT, v, src)

static func inc(s: StringName, v: float, src: String = "") -> StatModifier:
	return StatModifier.new(s, Op.INC, v, src)

static func more(s: StringName, v: float, src: String = "") -> StatModifier:
	return StatModifier.new(s, Op.MORE, v, src)

func to_dict() -> Dictionary:
	return {"stat": String(stat), "op": int(op), "value": value, "source": source}

static func from_dict(d: Dictionary) -> StatModifier:
	return StatModifier.new(StringName(d.get("stat", "")), int(d.get("op", 0)) as Op, float(d.get("value", 0.0)), String(d.get("source", "")))

func describe() -> String:
	return StatDefs.format_modifier(stat, op, value)
