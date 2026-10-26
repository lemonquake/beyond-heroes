extends "res://tests/tools/beta_release_perf.gd"
## Same workload as the existing probe, with sample durations, threshold counts and raw frame evidence.

var _summary_index := 0

func _summary(rows: Array[Dictionary]) -> Dictionary:
	var result := super._summary(rows)
	var total_ms := 0.0
	var over_100 := 0
	var over_60 := 0
	for row in rows:
		total_ms += float(row.frame)
		over_100 += int(float(row.frame) > 10.0)
		over_60 += int(float(row.frame) > 1000.0 / 60.0)
	if result.has("frame"):
		result.frame["duration_s"] = total_ms / 1000.0
		result.frame["frames_over_10ms"] = over_100
		result.frame["frames_over_16_67ms"] = over_60
		result.frame["average_fps"] = rows.size() * 1000.0 / maxf(total_ms, 0.001)
	if args.has("out"):
		var raw_path := String(args.out).get_basename() + "_frames_%d.json" % _summary_index
		var f := FileAccess.open(raw_path, FileAccess.WRITE)
		if f:
			f.store_string(JSON.stringify({"rows": rows, "engine": Engine.get_version_info().string,
				"adapter": RenderingServer.get_video_adapter_name(), "renderer": RenderingServer.get_current_rendering_method(),
				"body": args.get("body", "custom"), "touch": Settings.touch_mode, "lite": Settings.lite,
				"window": [get_window().size.x, get_window().size.y], "render_scale": get_viewport().scaling_3d_scale,
				"user_data": OS.get_user_data_dir()}))
	_summary_index += 1
	return result
