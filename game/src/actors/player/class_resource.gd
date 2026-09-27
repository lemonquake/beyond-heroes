class_name ClassResource
extends RefCounted
## Knight VALOR, Mage ARCANE CHARGE, Ranger FOCUS and Shadowblade COMBO.
##
## Valor (0-100): +3 per hit landed, +8 per block, +15 per parry, +1 per 5% max HP taken, +2/s while an enemy is
## within 8 m. Decays 6/s after 3 s out of combat. At 50+ (40 with Valiant Heart) the Knight is Resolute:
## 10% more physical damage and knockback. Judgment spends it.
##
## Arcane Charge (0-max, default 5): +1 per spell cast, lost one at a time after 4 s without casting.
## Each charge: 6% more spell damage and 8% more mana cost. At 3+ some spells change (Firebolt splits,
## Chain Lightning +2 chains). At maximum the Mage is Overcharged: takes 15% more damage.
##
## Focus (0-100, bh-010): the Ranger's calm. In combat it builds +6/s while no enemy is within 5 m and +3 per ranged
## hit; an enemy within 3 m drains it (-10/s). Out of combat it fades 8/s after 3 s. At 60+ (50 with Patient Hunter)
## the Ranger is Steady: +10% critical chance. Deadeye spends it all.
##
## Combo (0-5 pips, +Shadow Discipline, bh-010): the Shadowblade's rhythm. Builders and basic hits add pips (a
## critical builder hit adds one more); finishers spend them all. At maximum the Shadowblade is Poised: the next
## finisher always crits. Pips fade one at a time (every 1.5 s) after 5 s without landing a hit.

signal changed(value: float, max_value: float)

var kind: StringName
var value := 0.0
var max_value := 100.0
var _since_combat := 99.0
var _since_cast := 99.0
var _decay_acc := 0.0
var decay_delay_bonus := 0.0          # Shadow Discipline: pips linger longer

const VALOR_DECAY_DELAY := 3.0
const VALOR_DECAY := 6.0
const ARCANE_DECAY_DELAY := 4.0
const ARCANE_DECAY_STEP := 1.2
const ARCANE_DMG_PER := 0.06
const ARCANE_COST_PER := 0.08
const FOCUS_CALM_RATE := 6.0
const FOCUS_CALM_RANGE := 5.0
const FOCUS_PRESSURE_RANGE := 3.0
const FOCUS_PRESSURE_DRAIN := 10.0
const FOCUS_DECAY_DELAY := 3.0
const FOCUS_DECAY := 8.0
const FOCUS_PER_RANGED_HIT := 3.0
const STEADY_AT := 60.0
const STEADY_CRIT := 0.10
const COMBO_MAX := 5.0
const COMBO_DECAY_DELAY := 5.0
const COMBO_DECAY_STEP := 1.5

func _init(p_kind: StringName) -> void:
	kind = p_kind
	match kind:
		&"arcane": max_value = 5.0
		&"combo": max_value = COMBO_MAX
		_: max_value = 100.0

## Pip resources (drawn as pips on the HUD) versus bar resources.
func is_pips() -> bool:
	return kind == &"arcane" or kind == &"combo"

func set_max(m: float) -> void:
	max_value = m
	value = minf(value, max_value)

func gain(amount: float, gain_mult := 1.0) -> void:
	if amount <= 0.0:
		return
	var old := value
	value = clampf(value + amount * gain_mult, 0.0, max_value)
	if kind == &"arcane":
		_since_cast = 0.0
	else:
		_since_combat = 0.0
		_decay_acc = 0.0
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

func drain(amount: float) -> void:
	if amount <= 0.0 or value <= 0.0:
		return
	value = maxf(0.0, value - amount)
	changed.emit(value, max_value)

## `calm` (Focus): no enemy within FOCUS_CALM_RANGE; `pressed` (Focus): an enemy within FOCUS_PRESSURE_RANGE.
func tick(delta: float, in_combat: bool, hold := false, calm := false, pressed := false, gain_mult := 1.0) -> void:
	match kind:
		&"valor":
			if in_combat:
				_since_combat = 0.0
				gain(2.0 * delta)
			else:
				_since_combat += delta
				if _since_combat > VALOR_DECAY_DELAY and value > 0.0 and not hold:
					value = maxf(0.0, value - VALOR_DECAY * delta)
					changed.emit(value, max_value)
		&"focus":
			if in_combat:
				_since_combat = 0.0
				if pressed:
					drain(FOCUS_PRESSURE_DRAIN * delta)
				elif calm:
					gain(FOCUS_CALM_RATE * delta, gain_mult)
			else:
				_since_combat += delta
				if _since_combat > FOCUS_DECAY_DELAY and value > 0.0 and not hold:
					drain(FOCUS_DECAY * delta)
		&"combo":
			_since_combat += delta
			if _since_combat > COMBO_DECAY_DELAY + decay_delay_bonus and value > 0.0 and not hold:
				_decay_acc += delta
				if _decay_acc >= COMBO_DECAY_STEP:
					_decay_acc = 0.0
					drain(1.0)
		_:
			_since_cast += delta
			if _since_cast > ARCANE_DECAY_DELAY and value > 0.0:
				_decay_acc += delta
				if _decay_acc >= ARCANE_DECAY_STEP:
					_decay_acc = 0.0
					value = maxf(0.0, value - 1.0)
					changed.emit(value, max_value)

## Runtime stat modifiers from the resource state. (Resolute's 10% more physical damage is added to
## each physical DamageRequest by the player, since "more" multipliers live on requests.)
func modifiers(resolute_at := 50.0, steady_at := STEADY_AT) -> Array:
	var out: Array = []
	if kind == &"valor" and value >= resolute_at:
		out.append(StatModifier.inc(&"impact_strength", 0.10, "Resolute"))
	elif kind == &"focus" and value >= steady_at:
		out.append(StatModifier.flat(&"crit_chance", STEADY_CRIT, "Steady"))
	return out

func spell_damage_more() -> float:
	return 1.0 + ARCANE_DMG_PER * value if kind == &"arcane" else 1.0

func mana_cost_mult() -> float:
	return 1.0 + ARCANE_COST_PER * value if kind == &"arcane" else 1.0

func is_overcharged() -> bool:
	return kind == &"arcane" and value >= max_value

func is_resolute(threshold := 50.0) -> bool:
	return kind == &"valor" and value >= threshold

func is_steady(threshold := STEADY_AT) -> bool:
	return kind == &"focus" and value >= threshold

func is_poised() -> bool:
	return kind == &"combo" and value >= max_value - 0.001
