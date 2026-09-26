class_name SetDef
extends Resource
## An equipment set. Equipping several different pieces unlocks cumulative bonuses.
## bonuses: {pieces_required: {"desc": String, "mods": [StatModifier], "flags": {flag: magnitude}}}

@export var id: StringName
@export var display_name: String
@export var class_hint: StringName = &""
@export var pieces: Array = []            # item base ids
@export var bonuses := {}
@export_multiline var lore := ""

func thresholds() -> Array:
	var t := bonuses.keys()
	t.sort()
	return t

## Modifiers granted when `count` distinct pieces are equipped.
func modifiers_for(count: int) -> Array:
	var out: Array = []
	for n in thresholds():
		if count < int(n):
			continue
		var b: Dictionary = bonuses[n]
		var src := "%s (%d)" % [display_name, n]
		for m in b.get("mods", []):
			out.append(StatModifier.new(m.stat, m.op, m.value, src))
		var fl: Dictionary = b.get("flags", {})
		for f in fl:
			out.append(StatModifier.flat(StringName("flag_" + String(f)), float(fl[f]), src))
	return out
