extends Node
## Headless test runner. Usage:
##   godot --headless --path game res://tests/run_tests.tscn
## Writes a JSON report to ../work/lemondev/bh-002/evidence/tests/report.json and exits with code 0/1.
## Optional: -- --only=test_island,test_maps runs just those suites (the report then covers only them).

const DIR := "res://tests/unit/"

func _ready() -> void:
	_run.call_deferred()

func _run() -> void:
	# anything a test saves (a bonfire rest, a travel) goes to a hidden slot: slots 0-2 are the player's own heroes, and
	# Game.save_slot starts at 0 (the crafting suite's bonfire rest overwrote Slot 1 with a "Crafter", bh-011)
	Game.save_slot = 99
	var t0 := Time.get_ticks_msec()
	var total_checks := 0
	var all_failures: PackedStringArray = []
	var suites := {}
	var files := DirAccess.get_files_at(DIR)
	files.sort()
	var only: PackedStringArray = []
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--only="):
			only = a.substr(7).split(",", false)
	for f in files:
		if not f.ends_with(".gd") or not f.begins_with("test_"):
			continue
		if not only.is_empty() and not only.has(f.get_basename()):
			continue
		var script: GDScript = load(DIR + f)
		var inst: TestCase = script.new()
		inst.host = self
		var methods := []
		for m in script.get_script_method_list():
			if String(m.name).begins_with("test_"):
				methods.append(m.name)
		methods.sort()
		var ts := Time.get_ticks_usec()
		for m in methods:
			inst.begin("%s.%s" % [f.get_basename(), m])
			var d0 := inst._done
			await inst.call(m)  # tests may be coroutines (e.g. waiting for a navigation sync)
			if inst.strict and inst._done == d0:
				inst.failures.append("%s.%s: aborted before done() (script error?)" % [f.get_basename(), m])
		var dur := (Time.get_ticks_usec() - ts) / 1000.0
		suites[f] = {"tests": methods.size(), "checks": inst.checks, "failures": Array(inst.failures), "ms": dur}
		total_checks += inst.checks
		all_failures.append_array(inst.failures)
		print("[%s] %s — %d tests, %d checks, %d failures (%.1f ms)" % ["PASS" if inst.failures.is_empty() else "FAIL", f, methods.size(), inst.checks, inst.failures.size(), dur])
	for fl in all_failures:
		print("  FAIL ", fl)
	var report := {"engine": Engine.get_version_info().string, "checks": total_checks, "failures": Array(all_failures),
		"suites": suites, "elapsed_ms": Time.get_ticks_msec() - t0, "timestamp": Time.get_datetime_string_from_system()}
	var out_dir := ProjectSettings.globalize_path("res://").path_join("../work/lemondev/bh-002/evidence/tests")
	DirAccess.make_dir_recursive_absolute(out_dir)
	var fa := FileAccess.open(out_dir.path_join("report.json"), FileAccess.WRITE)
	if fa:
		fa.store_string(JSON.stringify(report, "  "))
	var md := FileAccess.open(ProjectSettings.globalize_path("res://").path_join("../docs/ELEMENT_MATRIX.md"), FileAccess.WRITE)
	if md:
		md.store_string(Elements.matrix_markdown())
	print("TOTAL: %d checks, %d failures" % [total_checks, all_failures.size()])
	get_tree().quit(0 if all_failures.is_empty() else 1)
