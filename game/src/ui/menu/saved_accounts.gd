class_name SavedAccounts
## bh-030: official accounts remembered on this device, so the sign-in page offers them as cards. Each entry keeps the
## server address and the UserID, and the password only when the player ticked "Remember password". The file is
## encrypted with a key tied to this device (FileAccess.open_encrypted_with_pass); copying it to another PC does not
## reveal the passwords. Tests and probes use `path` to point at a scratch file.

const MAX := 12
static var path := "user://official_accounts.dat"

static func _key() -> String:
	var id := OS.get_unique_id()
	if id == "":
		# no device id on this platform: a random key kept beside the file
		var kf := "user://official_accounts.key"
		if FileAccess.file_exists(kf):
			id = FileAccess.get_file_as_string(kf)
		else:
			id = Crypto.new().generate_random_bytes(24).hex_encode()
			var f := FileAccess.open(kf, FileAccess.WRITE)
			if f:
				f.store_string(id)
	return "beyond-heroes/accounts/" + id

## Every remembered account, the most recently used first: [{url, userid, password, remember_password, last_used}].
static func all() -> Array:
	if not FileAccess.file_exists(path):
		return []
	var f := FileAccess.open_encrypted_with_pass(path, FileAccess.READ, _key())
	if f == null:
		return []
	var parsed = JSON.parse_string(f.get_as_text())
	if not (parsed is Array):
		return []
	var out := []
	for e in parsed:
		if e is Dictionary and String(e.get("userid", "")) != "":
			out.append({"url": String(e.get("url", "")), "userid": String(e.get("userid", "")),
				"password": String(e.get("password", "")) if bool(e.get("remember_password", false)) else "",
				"remember_password": bool(e.get("remember_password", false)), "last_used": float(e.get("last_used", 0.0))})
	out.sort_custom(func(a, b): return float(a.last_used) > float(b.last_used))
	return out

## Accounts of one server.
static func for_server(url: String) -> Array:
	return all().filter(func(e): return String(e.url) == url)

static func _write(list: Array) -> bool:
	var f := FileAccess.open_encrypted_with_pass(path, FileAccess.WRITE, _key())
	if f == null:
		return false
	f.store_string(JSON.stringify(list.slice(0, MAX)))
	return true

## Remember (or update) an account after a successful sign-in. The password is kept only with `remember_password`.
static func remember(url: String, userid: String, password: String, remember_password: bool) -> void:
	var list := all().filter(func(e): return not (String(e.url) == url and String(e.userid).to_lower() == userid.to_lower()))
	list.push_front({"url": url, "userid": userid, "password": password if remember_password else "",
		"remember_password": remember_password, "last_used": Time.get_unix_time_from_system()})
	_write(list)

static func forget(url: String, userid: String) -> void:
	_write(all().filter(func(e): return not (String(e.url) == url and String(e.userid).to_lower() == userid.to_lower())))
