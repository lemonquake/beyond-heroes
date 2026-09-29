class_name DialogueSession
extends RefCounted
## One running conversation: walks the Dialogue graph line by line, offers choices, runs actions, remembers visited
## nodes, and hands world requests (open a shop, heal, respec) to whoever listens. The UI only renders and forwards
## input: advance() for the next line, choose(i) for a response.

signal line_shown(speaker: String, portrait: String, text_bbcode: String, index: int, count: int)
signal choices_shown(choices: Array)          # [{text, enabled}]
signal request(kind: StringName, arg: Variant) # open_shop(id), heal, service(id)
signal ended

var npc: NpcDef
var hero: HeroData
var model: Dialogue
var node_id := ""
var lines := PackedStringArray()
var line_index := 0
var choices: Array = []
var finished := false

static func start(p_npc: NpcDef, p_hero: HeroData) -> DialogueSession:
	var s := DialogueSession.new()
	s.npc = p_npc
	s.hero = p_hero
	s.model = Dialogue.new(p_npc.id, p_npc.graph)
	return s

## Call after connecting signals.
func begin(at := "") -> void:
	Events.dialogue_started.emit(npc.id)
	var first := at if at != "" else model.entry_node(hero)
	_enter(first)

func _enter(id: String) -> void:
	id = model.resolve(id, hero) if id != "" and id != "end" else id
	if id == "" or id == "end":
		finish()
		return
	node_id = id
	var n := model.node(id)
	if n.is_empty():
		push_warning("Dialogue %s: missing node %s" % [npc.id, id])
		finish()
		return
	hero.mark_dialogue_visited(npc.id, id)
	_apply(model.run_actions(n.get("actions", []), hero))
	if finished:
		return
	lines = model.lines_of(n)
	if lines.size() == 1 and lines[0] == "":
		lines = PackedStringArray()
	line_index = 0
	choices = []
	if lines.is_empty():
		_after_lines()
	else:
		_show_line()

func _show_line() -> void:
	var n := model.node(node_id)
	var speaker := String(n.get("speaker", npc.display_name))
	var portrait := String(n.get("portrait", npc.portrait))
	line_shown.emit(speaker, portrait, Dialogue.highlight(Dialogue.fill(lines[line_index], hero)), line_index, lines.size())
	if line_index == lines.size() - 1:
		var n2 := model.node(node_id)
		choices = model.choices(n2, hero)
		if not choices.is_empty():
			choices_shown.emit(choices)

## Next line; at the end of a node without choices, follow "next" (or end).
func advance() -> void:
	if finished:
		return
	if line_index < lines.size() - 1:
		line_index += 1
		_show_line()
		return
	if not choices.is_empty():
		return  # waiting for a choice
	_after_lines()

func _after_lines() -> void:
	var n := model.node(node_id)
	choices = model.choices(n, hero)
	if not choices.is_empty():
		if lines.is_empty():
			choices_shown.emit(choices)
		return
	_enter(String(n.get("next", "end")))

func choose(index: int) -> void:
	if finished or index < 0 or index >= choices.size():
		return
	var c: Dictionary = choices[index]
	if not c.get("enabled", true):
		return
	_apply(model.run_actions(c.get("actions", []), hero))
	var nxt := String(c.get("next", "end"))
	choices = []
	if not finished:
		_enter(nxt)

func _apply(out: Dictionary) -> void:
	if out.has("heal"):
		request.emit(&"heal", null)
	if out.has("service"):
		request.emit(&"service", out.service)
	if out.has("open_shop"):
		request.emit(&"open_shop", out.open_shop)
	if out.has("cutscene"):
		request.emit(&"cutscene", out.cutscene)

func finish() -> void:
	if finished:
		return
	finished = true
	Events.dialogue_ended.emit(npc.id)
	ended.emit()
