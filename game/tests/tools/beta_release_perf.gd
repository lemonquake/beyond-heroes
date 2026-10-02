extends "res://tests/tools/perf_probe.gd"
## QA entry point: apply an explicit 720p window before Main reapplies Settings,
## and include the median and sample count in the existing probe's summaries.
## Uses the existing scratch-slot and runtime-only quality arguments.

func _ready() -> void:
	Settings.resolution = 0
	Settings.window_mode = 0
	super._ready()

func _summary(rows: Array[Dictionary]) -> Dictionary:
	var report := super._summary(rows)
	for key in report:
		var values: Array[float] = []
		for row in rows:
			values.append(float(row[key]))
		values.sort()
		if values.is_empty():
			continue
		var middle := values.size() / 2
		var median := values[middle] if values.size() % 2 == 1 else (values[middle - 1] + values[middle]) * 0.5
		report[key]["median"] = snappedf(median, 0.01)
		report[key]["samples"] = values.size()
	return report
