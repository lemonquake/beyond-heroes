class_name Spinner
extends Node3D
## Turns slowly around a local axis (the Old Mill's water wheel).

var axis := Vector3.RIGHT
var speed := 0.6            # radians per second

func _process(delta: float) -> void:
	rotate_object_local(axis, speed * delta)
