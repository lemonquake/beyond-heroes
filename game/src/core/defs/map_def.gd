class_name MapDef
extends Resource
## A handcrafted map. The scene is produced by a builder script (src/world/maps/*.gd).

@export var id: StringName
@export var display_name: String
@export var subtitle: String
@export var builder: String                  # script path extending MapBuilder
@export var level_min := 1
@export var level_max := 1
@export var is_town := false
@export var music := &""
@export var ambience := &""
@export var footstep_surface := &"stone"
@export var reverb := 0.0                    # 0..1 wet amount for the environment reverb bus
@export var world_map_pos := Vector2.ZERO    # position on the world map UI (0..1)
@export var waypoint := true                 # has a waypoint shrine usable from the world map once discovered
@export var loading_hint := ""
