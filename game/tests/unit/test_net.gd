extends TestCase
## Multiplayer helpers that need no second machine (bh-010): room codes (an address as a short code a child can type)
## and the aura values a Knight's pulse sends to another player's hero.

func test_room_codes_round_trip() -> void:
	var r := rng(7)
	var ips := ["127.0.0.1", "192.168.1.20", "10.0.0.255", "26.123.45.67", "0.0.0.0", "255.255.255.255"]
	for i in 200:
		ips.append("%d.%d.%d.%d" % [r.randi_range(0, 255), r.randi_range(0, 255), r.randi_range(0, 255), r.randi_range(0, 255)])
	for ip in ips:
		var code := NetCodec.room_code(ip, Net.PORT, Net.PORT)
		eq(code.length(), 8, "%s -> 8-character code (%s)" % [ip, code])
		ok(not (code.contains("1") or code.contains("I") or code.contains("L") or code.contains("O")), "%s: no look-alike symbols in %s" % [ip, code])
		eq(NetCodec.parse_room_code(code, Net.PORT), [ip, Net.PORT], "%s survives its code" % ip)
		eq(NetCodec.parse_room_code(" " + code.to_lower().replace("-", " ") + " ", Net.PORT), [ip, Net.PORT], "%s: lower case and spaces are fine" % ip)
	var other := NetCodec.room_code("192.168.1.20", 25000, Net.PORT)
	eq(other.length(), 11, "a non-default port makes a longer code (%s)" % other)
	eq(NetCodec.parse_room_code(other, Net.PORT), ["192.168.1.20", 25000], "the port survives the longer code")
	done()

func test_bad_codes_are_refused() -> void:
	for bad in ["", "HELLO", "192.168.1.20", "K7QM-2X", "K7QM-2XF9", "IIII-III", "LLLL-LLL"]:
		eq(NetCodec.parse_room_code(bad, Net.PORT), [], "'%s' is not a room code" % bad)
	eq(NetCodec.room_code("not.an.ip", Net.PORT, Net.PORT), "", "a host name has no code")
	eq(NetCodec.room_code("300.1.1.1", Net.PORT, Net.PORT), "", "an out-of-range address has no code")
	done()

func test_typed_o_reads_as_zero() -> void:
	var code := NetCodec.room_code("10.0.0.1", Net.PORT, Net.PORT)
	eq(NetCodec.parse_room_code(code.replace("0", "O"), Net.PORT), ["10.0.0.1", Net.PORT], "an O typed for a zero still joins (%s)" % code)
	done()

func test_protocol_bumped_for_new_classes() -> void:
	ok(Net.PROTOCOL >= 3, "bh-011 clients refuse older hosts: travel requests, revive and ping are new messages (protocol %d)" % Net.PROTOCOL)
	for sid in [&"aura_might", &"aura_mending", &"aura_defiance", &"aura_fervor"]:
		var s := DB.skill(sid)
		ok(s != null and s.is_aura(), "%s is an aura" % sid)
		ok(StatusRules.DEFS.has(sid), "%s has a status entry" % sid)
	done()
