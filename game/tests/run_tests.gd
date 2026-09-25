extends Node
## Headless test runner. Usage:
##   godot --headless --path game res://tests/run_tests.tscn
## Writes a JSON report to ../work/lemondev/bh-001/evidence/tests/report.json and exits with code 0/1.

const DIR := "res://tests/unit/"

func _ready() -> void:
	var t0 := Time.get_ticks_msec()
	var total_checks := 0
	var all_failures: PackedStringArray = []
	var suites := {}
	var files := DirAccess.get_files_at(DIR)
	files.sort()
	for f in files:
		if not f.ends_with(".gd") or not f.begins_with("test_"):
			continue
		var script: GDScript = load(DIR + f)
		var inst: TestCase = script.new()
		var methods := []
		for m in script.get_script_method_list():
			if String(m.name).begins_with("test_"):
				methods.append(m.name)
		methods.sort()
		var ts := Time.get_ticks_usec()
		for m in methods:
			inst.begin("%s.%s" % [f.get_basename(), m])
			inst.call(m)
		var dur := (Time.get_ticks_usec() - ts) / 1000.0
		suites[f] = {"tests": methods.size(), "checks": inst.checks, "failures": Array(inst.failures), "ms": dur}
		total_checks += inst.checks
		all_failures.append_array(inst.failures)
		print("[%s] %s — %d tests, %d checks, %d failures (%.1f ms)" % ["PASS" if inst.failures.is_empty() else "FAIL", f, methods.size(), inst.checks, inst.failures.size(), dur])
	for fl in all_failures:
		print("  FAIL ", fl)
	var report := {"engine": Engine.get_version_info().string, "checks": total_checks, "failures": Array(all_failures),
		"suites": suites, "elapsed_ms": Time.get_ticks_msec() - t0, "timestamp": Time.get_datetime_string_from_system()}
	var out_dir := ProjectSettings.globalize_path("res://").path_join("../work/lemondev/bh-001/evidence/tests")
	DirAccess.make_dir_recursive_absolute(out_dir)
	var fa := FileAccess.open(out_dir.path_join("report.json"), FileAccess.WRITE)
	if fa:
		fa.store_string(JSON.stringify(report, "  "))
	var md := FileAccess.open(ProjectSettings.globalize_path("res://").path_join("../docs/ELEMENT_MATRIX.md"), FileAccess.WRITE)
	if md:
		md.store_string(Elements.matrix_markdown())
	print("TOTAL: %d checks, %d failures" % [total_checks, all_failures.size()])
	get_tree().quit(0 if all_failures.is_empty() else 1)
