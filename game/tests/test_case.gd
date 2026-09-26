class_name TestCase
extends RefCounted
## Minimal assertion base for the headless test runner.

var failures: PackedStringArray = []
var checks := 0
var _current := ""
var host: Node                    # a node inside the scene tree that tests may parent nodes to (set by the runner)
var strict := false               # strict suites must reach done() in every test; an aborted test is a failure
var _done := 0

## Call as the last statement of a test in a strict suite (proves the test body ran to completion).
func done() -> void:
	_done += 1

func begin(name: String) -> void:
	_current = name

func ok(cond: bool, msg: String) -> void:
	checks += 1
	if not cond:
		failures.append("%s: %s" % [_current, msg])

func eq(a, b, msg: String) -> void:
	checks += 1
	if typeof(a) in [TYPE_FLOAT, TYPE_INT] and typeof(b) in [TYPE_FLOAT, TYPE_INT]:
		if absf(float(a) - float(b)) > 0.0001:
			failures.append("%s: %s — expected %s, got %s" % [_current, msg, b, a])
	elif a != b:
		failures.append("%s: %s — expected %s, got %s" % [_current, msg, b, a])

func near(a: float, b: float, tol: float, msg: String) -> void:
	checks += 1
	if absf(a - b) > tol:
		failures.append("%s: %s — expected %s ± %s, got %s" % [_current, msg, b, tol, a])

## Helpers shared by tests.
static func rng(seed_value := 1) -> RandomNumberGenerator:
	var r := RandomNumberGenerator.new()
	r.seed = seed_value
	return r

## A bare stat block for pipeline tests: every modifier zero, level 1.
static func blank_stats(level := 1) -> DerivedStats:
	var d := DerivedStats.new()
	d.level = level
	d.loadout = WeaponLoadout.new()
	d.values = {&"max_hp": 1000.0, &"crit_damage": 1.5, &"impact_strength": 1.0}
	return d
