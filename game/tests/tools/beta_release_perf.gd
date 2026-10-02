extends "res://tests/tools/perf_probe.gd"
## QA entry point: apply an explicit 720p window before Main reapplies Settings,
## and include the median and sample count in the existing probe's summaries.
## Uses the existing scratch-slot and runtime-only quality arguments.

func _ready() -> void:
	Settings.resolution = 0
	Settings.window_mode = 0
	# run-only quality profile, so a result never depends on the player's own settings.cfg (nothing is saved):
	#   --profile=pc-low   shadows, effects, textures and anti-aliasing at Low, 3D at 100 %   (the 720p/low PC target)
	#   --profile=pc-high  the desktop defaults
	#   --profile=mobile   efficiency mode: the phone preset, 70 % 3D, 30 fps cap lifted by the probe
	Settings.minimap_zoom = 1               # pinned (the player's own Wide zoom made the minimap re-render every frame before bh-032)
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--minimap_zoom="):
			Settings.minimap_zoom = int(a.get_slice("=", 1))
		if a.begins_with("--profile="):
			match a.get_slice("=", 1):
				"pc-low":
					Settings._desktop_preset()
					Settings.shadows_quality = 0
					Settings.texture_quality = 0
					Settings.effects_quality = 0
					Settings.anti_aliasing = 0
				"pc-high":
					Settings._desktop_preset()
				"mobile":
					Settings._efficiency_preset()
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
