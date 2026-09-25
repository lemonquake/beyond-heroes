class_name ClassResource
extends RefCounted
## Knight VALOR and Mage ARCANE CHARGE.
##
## Valor (0-100): +3 per hit landed, +8 per block, +15 per parry, +1 per 5% max HP taken, +2/s while an enemy is
## within 8 m. Decays 6/s after 3 s out of combat. At 50+ (40 with Valiant Heart) the Knight is Resolute:
## 10% more physical damage and knockback. Judgment spends it.
##
## Arcane Charge (0-max, default 5): +1 per spell cast, lost one at a time after 4 s without casting.
## Each charge: 6% more spell damage and 8% more mana cost. At 3+ some spells change (Firebolt splits,
## Chain Lightning +2 chains). At maximum the Mage is Overcharged: takes 15% more damage.

signal changed(value: float, max_value: float)

var kind: StringName
var value := 0.0
var max_value := 100.0
var _since_combat := 99.0
var _since_cast := 99.0
var _decay_acc := 0.0

const VALOR_DECAY_DELAY := 3.0
const VALOR_DECAY := 6.0
const ARCANE_DECAY_DELAY := 4.0
const ARCANE_DECAY_STEP := 1.2
const ARCANE_DMG_PER := 0.06
const ARCANE_COST_PER := 0.08

func _init(p_kind: StringName) -> void:
	kind = p_kind
	max_value = 100.0 if kind == &"valor" else 5.0

func set_max(m: float) -> void:
	max_value = m
	value = minf(value, max_value)

func gain(amount: float, gain_mult := 1.0) -> void:
	if amount <= 0.0:
		return
	var old := value
	value = clampf(value + amount * gain_mult, 0.0, max_value)
	if kind == &"valor":
		_since_combat = 0.0
	else:
		_since_cast = 0.0
	if value != old:
		changed.emit(value, max_value)

func spend_all() -> float:
	var v := value
	value = 0.0
	changed.emit(value, max_value)
	return v

func spend(amount: float) -> bool:
	if value + 0.001 < amount:
		return false
	value -= amount
	changed.emit(value, max_value)
	return true

func tick(delta: float, in_combat: bool, hold := false) -> void:
	if kind == &"valor":
		if in_combat:
			_since_combat = 0.0
			gain(2.0 * delta)
		else:
			_since_combat += delta
			if _since_combat > VALOR_DECAY_DELAY and value > 0.0 and not hold:
				value = maxf(0.0, value - VALOR_DECAY * delta)
				changed.emit(value, max_value)
	else:
		_since_cast += delta
		if _since_cast > ARCANE_DECAY_DELAY and value > 0.0:
			_decay_acc += delta
			if _decay_acc >= ARCANE_DECAY_STEP:
				_decay_acc = 0.0
				value = maxf(0.0, value - 1.0)
				changed.emit(value, max_value)

## Runtime stat modifiers from the resource state. (Resolute's 10% more physical damage is added to
## each physical DamageRequest by the player, since "more" multipliers live on requests.)
func modifiers(resolute_at := 50.0) -> Array:
	var out: Array = []
	if kind == &"valor" and value >= resolute_at:
		out.append(StatModifier.inc(&"impact_strength", 0.10, "Resolute"))
	return out

func spell_damage_more() -> float:
	return 1.0 + ARCANE_DMG_PER * value if kind == &"arcane" else 1.0

func mana_cost_mult() -> float:
	return 1.0 + ARCANE_COST_PER * value if kind == &"arcane" else 1.0

func is_overcharged() -> bool:
	return kind == &"arcane" and value >= max_value

func is_resolute(threshold := 50.0) -> bool:
	return kind == &"valor" and value >= threshold
