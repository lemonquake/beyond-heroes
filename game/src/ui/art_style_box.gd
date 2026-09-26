@tool
class_name ArtStyleBox
extends StyleBox
## 9-slice texture style drawn at a scale (UI art is authored at 2x and drawn at 0.5 at 1920x1080, so the canvas_items
## stretch maps it 1:1 to texels at 3840x2160). StyleBoxTexture cannot scale its margins; this can.
## `expand` grows the drawn rect outward (transparent glow padding baked into the art) without affecting layout.

var texture: Texture2D
var margins := PackedInt32Array([0, 0, 0, 0])      # texture px: left, top, right, bottom
var expand := PackedInt32Array([0, 0, 0, 0])       # texture px
var draw_scale := 0.5
var tile := false                                  # tile the centre and edges instead of stretching
var modulate := Color.WHITE
var draw_center := true

func _draw(to_canvas_item: RID, rect: Rect2) -> void:
	if texture == null:
		return
	var s := draw_scale
	var r := rect.grow_individual(expand[0] * s, expand[1] * s, expand[2] * s, expand[3] * s)
	RenderingServer.canvas_item_add_set_transform(to_canvas_item, Transform2D(0.0, Vector2(s, s), 0.0, r.position))
	var mode := RenderingServer.NINE_PATCH_TILE_FIT if tile else RenderingServer.NINE_PATCH_STRETCH
	RenderingServer.canvas_item_add_nine_patch(to_canvas_item, Rect2(Vector2.ZERO, r.size / s), Rect2(), texture.get_rid(),
		Vector2(margins[0], margins[1]), Vector2(margins[2], margins[3]), mode, mode, draw_center, modulate)
	RenderingServer.canvas_item_add_set_transform(to_canvas_item, Transform2D.IDENTITY)

func _get_draw_rect(rect: Rect2) -> Rect2:
	var s := draw_scale
	return rect.grow_individual(expand[0] * s, expand[1] * s, expand[2] * s, expand[3] * s)
