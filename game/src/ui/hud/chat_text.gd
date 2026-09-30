class_name ChatText
extends RefCounted

const MAX_CHARS := 120
const EMOJIS := ["😀", "😂", "😊", "😢", "😮", "😎", "❤️", "👍", "👎", "🎉", "🔥", "💀"]

static func clean(text: String) -> String:
	var out := ""
	for i in text.length():
		var c := text.unicode_at(i)
		if c >= 32 and c != 127:
			out += String.chr(c)
		if out.length() >= MAX_CHARS:
			break
	return out.strip_edges()

static func mention(name: String) -> String:
	return "@\"%s\"" % name if name.contains(" ") or name.contains("@") else "@" + name

static func has_mention(text: String, name: String) -> bool:
	var token := mention(name).to_lower()
	var lower := text.to_lower()
	var start := lower.find(token)
	while start >= 0:
		var end := start + token.length()
		var before_ok := start == 0 or lower[start - 1] in " \t([{,;:"
		var after_ok := end == lower.length() or lower[end] in " \t.,!?;:)]}"
		if before_ok and after_ok:
			return true
		start = lower.find(token, start + 1)
	return false

## Complete the unfinished mention at the caret; quoted names support spaces.
static func completion(text: String, caret: int, names: Array) -> Dictionary:
	var before := text.left(caret)
	var at := before.rfind("@")
	if at < 0 or (at > 0 and not before[at - 1] in " \t([{,;:"):
		return {}
	var prefix := before.substr(at + 1).trim_prefix("\"").to_lower()
	# A trailing separator after a complete name ends that mention.
	for name: String in names:
		if before.substr(at).to_lower().begins_with(mention(name).to_lower() + " "):
			return {}
	var matches: Array[String] = []
	for name: String in names:
		if name.to_lower().begins_with(prefix) and not matches.has(name):
			matches.append(name)
	return {"start": at, "end": caret, "names": matches} if not matches.is_empty() else {}
