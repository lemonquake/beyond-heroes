class_name NetCodec
extends RefCounted
## Plain dictionaries for the two combat objects that cross the network (bh-008): a DamageRequest (a monster's blow on
## another machine's hero, resolved over there) and a DamageResult (a client's resolved blow on a host monster).
## Stats objects never travel: each side supplies its own attacker/target stats.

const REQ_FIELDS := ["kind", "base_min", "base_max", "hand", "use_weapon", "weapon_mult", "skill_mult", "bonus_inc", "can_crit",
	"force_crit", "crit_bonus", "evadable", "graze", "blockable", "knockback", "poise", "status_power", "heavy", "positional_mult", "label"]
const RES_FIELDS := ["total", "healed", "pre_mitigation", "is_crit", "evaded", "blocked", "perfect_block", "blocked_amount", "immune",
	"shattered", "purified", "knockback", "poise_damage", "leech", "mana_leech", "absorbed", "dominant_element", "skill", "skill_name",
	"heavy", "finisher"]

static func encode_request(r: DamageRequest) -> Dictionary:
	var d := {}
	for f in REQ_FIELDS:
		d[f] = r.get(f)
	d["conversion"] = r.conversion
	d["more"] = r.more
	d["direct_status"] = r.direct_status
	d["tags"] = r.tags
	return d

static func decode_request(d: Dictionary) -> DamageRequest:
	var r := DamageRequest.new()
	for f in REQ_FIELDS:
		if d.has(f):
			r.set(f, d[f])
	r.conversion = d.get("conversion", {})
	r.more = d.get("more", [])
	r.direct_status = d.get("direct_status", {})
	r.tags = d.get("tags", {})
	return r

static func encode_result(r: DamageResult) -> Dictionary:
	var d := {}
	for f in RES_FIELDS:
		d[f] = r.get(f)
	d["components"] = r.components
	d["buildup"] = r.buildup
	d["reactions"] = Array(r.reactions).map(func(x): return String(x))
	return d

static func decode_result(d: Dictionary) -> DamageResult:
	var r := DamageResult.new()
	for f in RES_FIELDS:
		if d.has(f):
			r.set(f, d[f])
	r.components = d.get("components", {})
	r.buildup = d.get("buildup", {})
	for x in d.get("reactions", []):
		r.reactions.append(StringName(x))
	return r

# ---- Room codes (bh-010) --------------------------------------------------------------------------------------------
# A host's IPv4 address (and its port, when it is not the default) as a short code a child can read out and type:
# "K7QM-2XF". 1, I, L and O are never used, so nothing looks alike; typing is forgiving (case, spaces, dashes, and an
# O typed for a zero).

const CODE_ALPHABET := "023456789ABCDEFGHJKMNPQRSTUVWXYZ"   # 32 symbols

static func room_code(ip: String, port: int, default_port: int) -> String:
	var parts := ip.split(".")
	if parts.size() != 4:
		return ""
	var v := 0
	for p in parts:
		if not p.is_valid_int() or int(p) < 0 or int(p) > 255:
			return ""
		v = (v << 8) | int(p)
	var n := 7
	if port != default_port:
		v |= (port & 0xFFFF) << 32
		n = 10
	var s := ""
	for i in n:
		s = CODE_ALPHABET[v & 31] + s
		v >>= 5
	return s.substr(0, 4) + "-" + s.substr(4)

## [ip, port] from a room code, or [] when it is not one.
static func parse_room_code(code: String, default_port: int) -> Array:
	var c := code.strip_edges().to_upper().replace("-", "").replace(" ", "").replace("O", "0")
	if c.length() != 7 and c.length() != 10:
		return []
	var v := 0
	for ch in c:
		var d := CODE_ALPHABET.find(ch)
		if d < 0:
			return []
		v = (v << 5) | d
	var ip := "%d.%d.%d.%d" % [(v >> 24) & 255, (v >> 16) & 255, (v >> 8) & 255, v & 255]
	var port := default_port if c.length() == 7 else (v >> 32) & 0xFFFF
	return [ip, port]

# ---- Compact snapshots (bh-035) -------------------------------------------------------------------------------------
# A hero or monster snapshot sent as generic Variants cost 136-192 bytes (every float a typed 8-byte value, every field
# its own header). Packed by hand it is about 40: position as three 32-bit floats, yaw and velocity quantised to 16 bits,
# flags in one byte. The decoded Array has the same layout as before, so everything that reads a snapshot is unchanged.
#   actor   [pos, yaw, vel, hp, max_hp, alive, action, serial, rate, loop, combat, level]
#   monster [id, pos, yaw, vel, hp, max_hp, action, serial, rate, loop, engaged, shield]

const _YAW_Q := 32767.0 / PI
const _VEL_Q := 100.0                # centimetres per second

static func _put_core(b: StreamPeerBuffer, pos: Vector3, yaw: float, vel: Vector3, hp: float, max_hp: float, action: String,
		serial: int, rate: float, flags: int) -> void:
	b.put_float(pos.x)
	b.put_float(pos.y)
	b.put_float(pos.z)
	b.put_16(int(clampf(wrapf(yaw, -PI, PI) * _YAW_Q, -32767.0, 32767.0)))
	b.put_16(int(clampf(vel.x * _VEL_Q, -32767.0, 32767.0)))
	b.put_16(int(clampf(vel.y * _VEL_Q, -32767.0, 32767.0)))
	b.put_16(int(clampf(vel.z * _VEL_Q, -32767.0, 32767.0)))
	b.put_float(hp)
	b.put_float(max_hp)
	b.put_u8(flags)
	b.put_u16(serial & 0xFFFF)
	b.put_u16(int(clampf(rate * 1000.0, 0.0, 65535.0)))
	var name := action.to_utf8_buffer()
	b.put_u8(mini(name.size(), 64))
	b.put_data(name.slice(0, 64))

## Reads one core block, or returns [] when the buffer is too short (a malformed packet is simply dropped).
static func _get_core(b: StreamPeerBuffer) -> Array:
	if b.get_available_bytes() < 34:
		return []
	var pos := Vector3(b.get_float(), b.get_float(), b.get_float())
	var yaw := b.get_16() / _YAW_Q
	var vel := Vector3(b.get_16() / _VEL_Q, b.get_16() / _VEL_Q, b.get_16() / _VEL_Q)
	var hp := b.get_float()
	var max_hp := b.get_float()
	var flags := b.get_u8()
	var serial := b.get_u16()
	var rate := b.get_u16() / 1000.0
	var n := b.get_u8()
	if n > 64 or b.get_available_bytes() < n:
		return []
	var action := (b.get_data(n)[1] as PackedByteArray).get_string_from_utf8() if n > 0 else ""
	return [pos, yaw, vel, hp, max_hp, flags, action, serial, rate]

## A hero / Tempo / arena fighter snapshot (Net.actor_state) as bytes.
static func pack_actor(s: Array) -> PackedByteArray:
	var b := StreamPeerBuffer.new()
	var flags := (1 if s[5] else 0) | (2 if s[9] else 0) | (4 if s[10] else 0)
	_put_core(b, s[0], s[1], s[2], s[3], s[4], String(s[6]), int(s[7]), float(s[8]), flags)
	b.put_u16(clampi(int(s[11]), 0, 65535))
	return b.data_array

static func unpack_actor(bytes: Variant) -> Array:
	if not bytes is PackedByteArray or (bytes as PackedByteArray).size() > 160:
		return []
	var b := StreamPeerBuffer.new()
	b.data_array = bytes
	var c := _get_core(b)
	if c.is_empty() or b.get_available_bytes() < 2:
		return []
	var f: int = c[5]
	return [c[0], c[1], c[2], c[3], c[4], (f & 1) != 0, c[6], c[7], c[8], (f & 2) != 0, (f & 4) != 0, b.get_u16()]

## Monster snapshots (Net.enemy_state) packed back to back: [u16 count, (u32 id, core, f32 shield)...].
static func pack_monsters(states: Array) -> PackedByteArray:
	var b := StreamPeerBuffer.new()
	b.put_u16(states.size())
	for s in states:
		b.put_u32(int(s[0]))
		var flags := (2 if s[9] else 0) | (4 if s[10] else 0)
		_put_core(b, s[1], s[2], s[3], s[4], s[5], String(s[6]), int(s[7]), float(s[8]), flags)
		b.put_float(float(s[11]))
	return b.data_array

static func unpack_monsters(bytes: Variant, max_count := 512) -> Array:
	var out := []
	if not bytes is PackedByteArray or (bytes as PackedByteArray).size() < 2:
		return out
	var b := StreamPeerBuffer.new()
	b.data_array = bytes
	var n := b.get_u16()
	if n > max_count:
		return out
	for i in n:
		if b.get_available_bytes() < 4:
			return out
		var id := b.get_u32()
		var c := _get_core(b)
		if c.is_empty() or b.get_available_bytes() < 4:
			return out
		var f: int = c[5]
		out.append([id, c[0], c[1], c[2], c[3], c[4], c[6], c[7], c[8], (f & 2) != 0, (f & 4) != 0, b.get_float()])
	return out

## An ally pack on the wire: each entry's state Array becomes bytes ("b"); everything else (key, name, guild) stays.
static func pack_allies(pack: Array) -> Array:
	var out := []
	for e in pack:
		var w: Dictionary = (e as Dictionary).duplicate()
		w.erase("s")
		w["b"] = pack_actor(e.s)
		out.append(w)
	return out

## The other way; entries that do not decode are dropped (NetGuard.ally_pack_ok then checks what is left).
static func unpack_allies(wire: Variant) -> Array:
	var out := []
	if not wire is Array or (wire as Array).size() > 48:
		return out
	for e in wire:
		if not e is Dictionary:
			return []
		var s := unpack_actor((e as Dictionary).get("b", null))
		if s.is_empty():
			return []
		var d: Dictionary = (e as Dictionary).duplicate()
		d.erase("b")
		d["s"] = s
		out.append(d)
	return out
