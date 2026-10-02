class_name NetGuard
extends RefCounted
## Limits on what another machine may send (bh-032). Every network handler that accepts a Dictionary, an Array, a number
## or a string from a peer runs it through here first: bounded size, expected types, finite numbers, and a per-peer rate.
## This keeps a damaged or modified client from stalling the room, spamming it or crashing a handler with a wrong type.
## It does not make combat server-authoritative: a map owner still simulates its monsters and a client still reports its
## own hits (see docs/OFFICIAL_SERVER.md, "What the server decides").

const MAX_PROFILE_BYTES := 12000
const MAX_PACK_BYTES := 24000
const MAX_CHECKPOINT_BYTES := 400000
const MAX_ALLIES_PER_PACK := 48
const MAX_APPEARANCE_BYTES := 16000
const MAX_TEXT := 240
const HIT_REACH := 60.0              # a reported hit must land this close to the hero that claims it
const HIT_DAMAGE_CAP := 2.0e6        # no single blow is larger than this; real damage stays far below it

## {"peer:key": [tokens, last_msec]}; static so every handler shares one table.
static var _buckets := {}

## Token bucket: `per_second` sustained, `burst` at once. False means this message should be dropped.
static func allow(peer: int, key: String, per_second: float, burst := 0.0, now_msec := -1) -> bool:
	var now := now_msec if now_msec >= 0 else Time.get_ticks_msec()
	var cap := burst if burst > 0.0 else maxf(per_second, 1.0)
	var id := "%d:%s" % [peer, key]
	var b: Array = _buckets.get(id, [cap, now])
	var tokens := minf(cap, float(b[0]) + float(now - int(b[1])) * 0.001 * per_second)
	if tokens < 1.0:
		_buckets[id] = [tokens, now]
		return false
	_buckets[id] = [tokens - 1.0, now]
	return true

static func forget(peer: int) -> void:
	var prefix := "%d:" % peer
	for id in _buckets.keys():
		if String(id).begins_with(prefix):
			_buckets.erase(id)

static func reset() -> void:
	_buckets.clear()

## Serialized size of any value. Large nested payloads are refused before they are walked.
static func fits(value: Variant, max_bytes: int) -> bool:
	return var_to_bytes(value).size() <= max_bytes

static func finite_vec(v: Variant) -> bool:
	return v is Vector3 and (v as Vector3).is_finite()

static func finite(v: Variant) -> bool:
	return (v is float or v is int) and is_finite(float(v))

static func text(v: Variant, max_len := MAX_TEXT) -> String:
	return String(v).left(max_len) if v is String or v is StringName else ""

## A player's profile as the room stores it: known keys only, expected types, bounded strings.
static func clean_profile(p: Variant) -> Dictionary:
	if not p is Dictionary or not fits(p, MAX_PROFILE_BYTES):
		return {}
	var d: Dictionary = p
	var out := {
		"name": text(d.get("name", "Hero"), 18),
		"cls": text(d.get("cls", "knight"), 24),
		"level": clampi(int(d.get("level", 1)) if finite(d.get("level", 1)) else 1, 1, BH.LEVEL_CAP),
		"map": text(d.get("map", ""), 64),
		"dungeon_level": clampi(int(d.get("dungeon_level", 1)) if finite(d.get("dungeon_level", 1)) else 1, 1, 9999),
		"device": text(d.get("device", "PC"), 12),
		"scope": text(d.get("scope", ""), 16),
		"room": text(d.get("room", ""), 64),
		"ticket": text(d.get("ticket", ""), 128),
		"guild": d.get("guild", {}) if d.get("guild", {}) is Dictionary else {},
		"userid": text(d.get("userid", ""), 32),
		"character": text(d.get("character", ""), 64),
	}
	return out

## An ally snapshot is an Array of {"k": key, "s": 12-element state, ...}. False when it is not that or is oversized.
static func ally_pack_ok(pack: Variant) -> bool:
	if not pack is Array or (pack as Array).size() > MAX_ALLIES_PER_PACK or not fits(pack, MAX_PACK_BYTES):
		return false
	for e in pack:
		if not e is Dictionary or not (e as Dictionary).get("k", null) is String:
			return false
		var s: Variant = (e as Dictionary).get("s", null)
		if not s is Array or (s as Array).size() < 12 or not finite_vec(s[0]) or not finite(s[1]) or not finite_vec(s[2]) \
				or not finite(s[3]) or not finite(s[4]) or not (s[5] is bool) or not finite(s[11]):
			return false
	return true

## The pieces of a reported hit that the host applies to a monster: numbers only, finite, and no larger than any real blow.
static func clean_result(d: Variant) -> Dictionary:
	if not d is Dictionary or not fits(d, MAX_PACK_BYTES):
		return {}
	var src: Dictionary = d
	var out := {}
	for f in NetCodec.RES_FIELDS:
		if not src.has(f):
			continue
		var v: Variant = src[f]
		match f:
			"total", "healed", "absorbed":
				if not finite(v):
					return {}
				out[f] = int(clampf(float(v), 0.0, HIT_DAMAGE_CAP))
			"pre_mitigation", "blocked_amount", "knockback", "poise_damage", "leech", "mana_leech":
				if not finite(v):
					return {}
				out[f] = clampf(float(v), 0.0, DamagePipeline.MAX_KNOCKBACK if f == "knockback" else HIT_DAMAGE_CAP)
			"is_crit", "evaded", "blocked", "perfect_block", "immune", "shattered", "purified", "heavy", "finisher":
				out[f] = bool(v) if v is bool else false
			"dominant_element":
				out[f] = clampi(int(v), 0, 31) if finite(v) else 0
			"skill", "skill_name":
				out[f] = text(v, 48)
	var comps: Variant = src.get("components", {})
	var clean := {}
	if comps is Dictionary:
		for k in comps:
			if finite(k) and finite(comps[k]) and clean.size() < 16:
				clean[int(k)] = clampf(float(comps[k]), 0.0, HIT_DAMAGE_CAP)
	out["components"] = clean
	var buildup := {}
	var raw_buildup: Variant = src.get("buildup", {})
	if raw_buildup is Dictionary:
		for k in raw_buildup:
			if (k is String or k is StringName) and String(k).length() <= 24 and finite(raw_buildup[k]) and buildup.size() < 8:
				buildup[StringName(k)] = clampf(float(raw_buildup[k]), 0.0, 100.0)
	out["buildup"] = buildup
	var reactions := []
	var raw_reactions: Variant = src.get("reactions", [])
	if raw_reactions is Array:
		for x in raw_reactions:
			if (x is String or x is StringName) and String(x).length() <= 24 and reactions.size() < 8:
				reactions.append(String(x))
	out["reactions"] = reactions
	var tags: Variant = src.get("tags", {})
	out["tags"] = {&"push_dir": tags.get(&"push_dir", Vector3.ZERO) if tags is Dictionary and finite_vec(tags.get(&"push_dir", Vector3.ZERO)) else Vector3.ZERO,
		&"launch": clampf(float(tags.get(&"launch", 0.0)), 0.0, DamagePipeline.MAX_LAUNCH) if tags is Dictionary and finite(tags.get(&"launch", 0.0)) else 0.0}
	return out
