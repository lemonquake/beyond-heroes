class_name NetCodec
extends RefCounted
## Plain dictionaries for the two combat objects that cross the network (bh-008): a DamageRequest (a monster's blow on
## another machine's hero, resolved over there) and a DamageResult (a client's resolved blow on a host monster).
## Stats objects never travel: each side supplies its own attacker/target stats.

const REQ_FIELDS := ["kind", "base_min", "base_max", "hand", "use_weapon", "weapon_mult", "skill_mult", "bonus_inc", "can_crit",
	"force_crit", "crit_bonus", "evadable", "blockable", "knockback", "poise", "status_power", "heavy", "positional_mult", "label"]
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
