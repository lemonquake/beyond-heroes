class_name TouchText
extends RefCounted
## bh-032: readable text for touch play. The interface is drawn for a 1080p desktop; on a phone the same 15-pixel label is about
## a millimetre tall. Every label, button and text box added under the UI in touch mode is raised to MIN_SIZE (about 11 sp on a
## 400 dpi phone at the touch scale of 1.25). Short badges (hotkey letters, counts) are left alone: they sit inside art that
## cannot grow with them.

const MIN_SIZE := 22
const SHORT_BADGE := 6               # labels this short are icons' captions, not reading text

static func install(root: Node) -> void:
	root.get_tree().node_added.connect(func(n: Node) -> void:
		if n is Control and is_instance_valid(root) and root.is_ancestor_of(n):
			enlarge.call_deferred(n))

static func enlarge(n: Control) -> void:
	if not is_instance_valid(n) or not Settings.touch_mode or n.has_meta(&"touch_text_skip"):
		return
	if n is Label:
		var t := (n as Label).text
		if t != "" and t.length() <= SHORT_BADGE:      # an empty label is filled in later (quest text, names): it is reading text
			return
	elif not (n is Button or n is LineEdit):
		return
	elif n is Button and (n as Button).text.length() <= SHORT_BADGE and (n as Button).icon != null:
		return
	if n.get_theme_font_size(&"font_size") < MIN_SIZE:
		n.add_theme_font_size_override(&"font_size", MIN_SIZE)
