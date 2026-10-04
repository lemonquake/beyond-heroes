class_name StatusController
extends RefCounted
## Per-actor status/buff model. Pure logic: no nodes. The owning actor ticks it and reacts to its signals.

signal status_added(id: StringName)
signal status_removed(id: StringName)
signal dot_tick(id: StringName, amount: float, element: int)
signal staggered(poise_broken: bool)
signal changed

class Instance:
	var id: StringName
	var remaining := 0.0
	var duration := 0.0
	var magnitude := 0.0
	var dps := 0.0
	var element := Elements.PHYSICAL
	var tick_timer := 0.0
	var infinite := false
	var modifiers: Array = []
	var stacks := 1
	var source_name := ""                # who applied it (tooltips)

const DOT_TICK := 0.5
const BUILDUP_DECAY := 12.0          # points per second
const BUILDUP_DECAY_DELAY := 2.0
const POISE_RECOVER_DELAY := 2.0
const POISE_RECOVER_RATE := 0.35     # fraction of poise per second
const BURN_DPS_FRACTION := 0.25      # burning dps = 25% of the igniting hit's fire damage
const BLEED_DPS_FRACTION := 0.2
const CHILL_SLOW := 0.25
const MAX_STAGGER_DURATION := 0.75
const STAGGER_RECOVERY := 0.6
const POISON_DPS_FRACTION := 0.35

var statuses := {}                   # id -> Instance
var buildup := {}                    # id -> float
var poise_meter := 0.0
var status_res := 0.0
var max_poise := 30.0
var grants_stagger_window := false   # elites and bosses become Exposed after a poise break
var immunities := {}                 # status id -> true (bosses: frozen, stunned)
var _since_buildup := 0.0
var _since_poise := 0.0
var _stagger_recovery := 0.0

func has(id: StringName) -> bool:
	return statuses.has(id)

func magnitude(id: StringName, default_value := 0.0) -> float:
	return statuses[id].magnitude if statuses.has(id) else default_value

func remaining(id: StringName) -> float:
	return statuses[id].remaining if statuses.has(id) else 0.0

func stacks(id: StringName) -> int:
	return statuses[id].stacks if statuses.has(id) else 0

func is_disabled() -> bool:
	return has(&"frozen") or has(&"stunned") or has(&"staggered") or has(&"petrified")

func is_silenced() -> bool:
	return has(&"silenced") or is_disabled()

func is_immune(id: StringName) -> bool:
	return immunities.has(id)

## Apply or refresh a status. Single instance per id: duration refreshes to the larger value, magnitude/dps keep the max.
func apply(id: StringName, duration := -1.0, mag := 0.0, dps := 0.0, element := Elements.PHYSICAL, mods: Array = []) -> void:
	if id == &"staggered" and (has(id) or _stagger_recovery > 0.0):
		return
	if immunities.has(id):
		# Bosses shrug off hard control: Freeze becomes a heavy Chill, Stun becomes a Stagger.
		if id == &"frozen" and not immunities.has(&"chilled"):
			apply(&"chilled", 3.0, CHILL_SLOW, 0.0, Elements.ICE, [StatModifier.more(&"move_speed", -CHILL_SLOW), StatModifier.more(&"attack_speed", -CHILL_SLOW)])
		return
	if id == &"frozen" and has(&"freeze_immune"):
		return
	if id == &"stunned" and has(&"stun_immune"):
		return
	var dur := duration if duration >= 0.0 else StatusRules.base_duration(id)
	if StatusRules.is_debuff(id) and not bool(StatusRules.DEFS.get(id, {}).get("fixed_duration", false)):
		dur *= (1.0 - status_res)
	if id == &"staggered":
		if dur <= 0.0:
			return
		dur = minf(dur, MAX_STAGGER_DURATION)
	var inst: Instance = statuses.get(id)
	var is_new := inst == null
	if is_new:
		inst = Instance.new()
		inst.id = id
		statuses[id] = inst
	inst.infinite = dur <= 0.0
	inst.duration = maxf(inst.duration, dur) if not is_new else dur
	inst.remaining = maxf(inst.remaining, dur)
	inst.magnitude = maxf(inst.magnitude, mag)
	inst.dps = maxf(inst.dps, dps)
	inst.element = element
	if not is_new and StatusRules.max_stacks(id) > 1:
		inst.stacks = mini(inst.stacks + 1, StatusRules.max_stacks(id))
	if not mods.is_empty():
		inst.modifiers = mods
	elif inst.modifiers.is_empty():
		inst.modifiers = StatusRules.default_mods(id)
	if is_new:
		_on_added(id)
		status_added.emit(id)
	changed.emit()

func remove(id: StringName) -> void:
	if not statuses.has(id):
		return
	statuses.erase(id)
	if id == &"frozen":
		apply(&"freeze_immune")
	elif id == &"stunned":
		apply(&"stun_immune")
	elif id == &"staggered":
		_stagger_recovery = STAGGER_RECOVERY
	status_removed.emit(id)
	changed.emit()

func clear() -> void:
	for id in statuses.keys():
		statuses.erase(id)
		status_removed.emit(id)
	buildup.clear()
	poise_meter = 0.0
	_stagger_recovery = 0.0
	changed.emit()

func _on_added(id: StringName) -> void:
	match id:
		&"wet":
			if has(&"burning"):
				remove(&"burning")
		&"frozen":
			buildup.erase(&"chilled")

## Process the status side of a resolved hit. fire_damage etc. come from result.components.
func receive_hit(result: DamageResult) -> void:
	if result.evaded:
		return
	var comp := result.components
	var wet := has(&"wet")
	# Interactions that consume statuses.
	if comp.get(Elements.WATER, 0.0) > 0.0:
		apply(&"wet")            # also extinguishes burning via _on_added / refresh below
		if has(&"burning"):
			remove(&"burning")
		wet = true
	if comp.get(Elements.FIRE, 0.0) > 0.0:
		if wet and not comp.has(Elements.WATER):
			remove(&"wet")
			wet = false
		remove(&"chilled")
		buildup.erase(&"chilled")
		if result.reactions.has(&"melt"):
			remove(&"frozen")
	if comp.get(Elements.ICE, 0.0) > 0.0 and has(&"burning"):
		remove(&"burning")
	if result.shattered:
		remove(&"frozen")
	if result.purified:
		remove(&"cursed")
	if result.reactions.has(&"umbral"):
		remove(&"purged")
	# Buildups.
	for sid in result.buildup:
		var amt: float = result.buildup[sid]
		if amt <= 0.0:
			continue
		match sid:
			&"chilled":
				apply(&"chilled", -1.0, CHILL_SLOW, 0.0, Elements.ICE, [StatModifier.more(&"move_speed", -CHILL_SLOW), StatModifier.more(&"attack_speed", -CHILL_SLOW)])
				if has(&"freeze_immune"):
					continue
				_add_buildup(&"chilled", amt * (2.0 if wet else 1.0))
				if buildup[&"chilled"] >= StatusRules.THRESHOLD:
					buildup[&"chilled"] = 0.0
					apply(&"frozen")
			&"shocked":
				_add_buildup(sid, amt * (2.0 if wet else 1.0))
				if buildup[sid] >= StatusRules.THRESHOLD:
					buildup[sid] = 0.0
					apply(&"shocked", -1.0, DamagePipeline.SHOCK_TAKEN_WET if wet else DamagePipeline.SHOCK_TAKEN)
			&"burning":
				if wet:
					continue
				_add_buildup(sid, amt)
				if buildup[sid] >= StatusRules.THRESHOLD:
					buildup[sid] = 0.0
					apply(&"burning", -1.0, 0.0, maxf(1.0, comp.get(Elements.FIRE, 0.0) * BURN_DPS_FRACTION), Elements.FIRE)
			&"bleeding":
				_add_buildup(sid, amt)
				if buildup[sid] >= StatusRules.THRESHOLD:
					buildup[sid] = 0.0
					apply(&"bleeding", -1.0, 0.0, maxf(1.0, comp.get(Elements.PHYSICAL, 0.0) * BLEED_DPS_FRACTION * result.dot_mult * result.bleed_mult), Elements.PHYSICAL)
			&"poisoned":
				_add_buildup(sid, amt)
				if buildup[sid] >= StatusRules.THRESHOLD:
					buildup[sid] = 0.0
					apply(&"poisoned", -1.0, 0.0, maxf(1.0, float(result.total) * POISON_DPS_FRACTION * result.dot_mult), Elements.PHYSICAL)
			&"wet":
				apply(&"wet")
			&"stunned":
				if amt >= StatusRules.THRESHOLD:
					apply(&"stunned")
			_:
				_add_buildup(sid, amt)
				if buildup[sid] >= StatusRules.THRESHOLD:
					buildup[sid] = 0.0
					apply(sid)
	# Poise.
	if result.poise_damage > 0.0 and not has(&"staggered") and _stagger_recovery <= 0.0:
		_since_poise = 0.0
		poise_meter += result.poise_damage
		if poise_meter >= max_poise:
			poise_meter = 0.0
			apply(&"staggered")
			if grants_stagger_window:
				apply(&"stagger_window")
			staggered.emit(true)
	changed.emit()

func _add_buildup(id: StringName, amt: float) -> void:
	_since_buildup = 0.0
	buildup[id] = minf(StatusRules.THRESHOLD * 1.5, buildup.get(id, 0.0) + amt)

## Advance timers. Emits dot_tick for damage-over-time; the actor routes those through the damage pipeline.
func tick(dt: float) -> void:
	if not is_finite(dt) or dt <= 0.0:
		return
	_stagger_recovery = maxf(0.0, _stagger_recovery - dt)
	var expired: Array[StringName] = []
	for id in statuses.keys():
		var inst: Instance = statuses.get(id)
		if inst == null:
			continue
		if inst.dps > 0.0:
			inst.tick_timer += dt
			while inst.tick_timer >= DOT_TICK:
				inst.tick_timer -= DOT_TICK
				dot_tick.emit(id, inst.dps * DOT_TICK, inst.element)
		if not inst.infinite:
			inst.remaining -= dt
			if inst.remaining <= 0.0:
				expired.append(id)
	for id in expired:
		if statuses.has(id) and statuses[id].remaining <= 0.0:
			remove(id)
	_since_buildup += dt
	if _since_buildup > BUILDUP_DECAY_DELAY and not buildup.is_empty():
		for k in buildup.keys():
			buildup[k] = maxf(0.0, buildup[k] - BUILDUP_DECAY * dt)
	_since_poise += dt
	if _since_poise > POISE_RECOVER_DELAY and poise_meter > 0.0:
		poise_meter = maxf(0.0, poise_meter - max_poise * POISE_RECOVER_RATE * dt)

## Stat modifiers currently contributed by statuses/buffs (chill slow, war cry, haste ...).
func stat_modifiers() -> Array:
	var out: Array = []
	for id in statuses:
		var inst: Instance = statuses[id]
		if inst.stacks <= 1:
			out.append_array(inst.modifiers)
		else:
			for m in inst.modifiers:
				out.append(StatModifier.new(m.stat, m.op, m.value * inst.stacks, m.source))
	return out

## Remove every debuff matching `ids` (cleanse). Returns how many were removed.
func cleanse(ids: Array) -> int:
	var n := 0
	for id in ids:
		if statuses.has(id):
			remove(id)
			n += 1
	return n

## Remove every harmful status (debuffs). Returns how many were removed.
func cleanse_harmful() -> int:
	var ids := []
	for id in statuses:
		if StatusRules.is_debuff(id):
			ids.append(id)
	return cleanse(ids)

func visible_statuses() -> Array:
	var out := []
	for id in statuses:
		if not StatusRules.is_hidden(id):
			out.append(statuses[id])
	return out

## bh-017: multiplier on every point of healing and regeneration this actor receives — Grievous Wound (-25% per stack,
## up to -75%), Vigor (+25%), Purged (halved). Applied by Actor.heal and by each regeneration tick.
func heal_taken_mult() -> float:
	var m := 1.0
	for id in statuses:
		var per := StatusRules.heal_taken(id)
		if per != 0.0:
			m += per * float(statuses[id].stacks)
	if statuses.has(&"purged"):
		m *= 0.5
	if statuses.has(&"bloodcurse"):
		m *= 1.0 - clampf(magnitude(&"bloodcurse"), 0.0, 0.70)
	return clampf(m, 0.0, 3.0)
