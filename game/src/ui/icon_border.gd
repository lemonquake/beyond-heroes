class_name IconBorder
extends Resource
## A replaceable cosmetic frame. Artwork and gameplay information remain separate layers.

@export var style_id: StringName = &"aether_forged"
@export var display_name := "Aether Forged"
@export_file("*.png", "*.svg", "*.webp") var texture_path := "res://assets/ui/borders/aether_forged.png"
## Normalized opening in the frame: left, top, width, height. Supports asymmetric frames.
@export var aperture := Rect2(0.09, 0.09, 0.82, 0.82)
@export var tint := Color.WHITE

func is_valid() -> bool:
	return style_id != &"" and not display_name.strip_edges().is_empty() and aperture.position.x >= 0.0 and aperture.position.y >= 0.0 and aperture.size.x > 0.0 and aperture.size.y > 0.0 and aperture.end.x <= 1.0 and aperture.end.y <= 1.0

func content_rect(bounds: Rect2) -> Rect2:
	return Rect2(bounds.position + aperture.position * bounds.size, aperture.size * bounds.size)

func texture() -> Texture2D:
	return UIArt.tex(texture_path) if texture_path != "" else null
