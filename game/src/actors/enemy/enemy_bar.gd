class_name EnemyBar
extends Node3D
## Floating health bar above an enemy (billboard shader quad) plus, for elites, a name plate with their modifiers.
## Shown for a few seconds after the enemy is hit, always while an elite is engaged, never for bosses (HUD bar).

const SHOW_TIME := 4.0

var enemy: Enemy
var _quad: MeshInstance3D
var _mat: ShaderMaterial
var _label: Label3D
var _note: Label3D
var _visible_t := 0.0
var _shown_hp := 1.0
var _lag_hp := 1.0

static var _shader: Shader

func setup(e: Enemy) -> void:
	enemy = e

func _ready() -> void:
	if _shader == null:
		_shader = Shader.new()
		_shader.code = """
shader_type spatial;
render_mode unshaded, cull_disabled, depth_draw_never, depth_test_disabled, shadows_disabled;
uniform float fill = 1.0;
uniform float lag = 1.0;
uniform float shield = 0.0;
uniform vec4 fill_color : source_color = vec4(0.85, 0.12, 0.1, 1.0);
uniform float alpha = 1.0;
void vertex() {
	MODELVIEW_MATRIX = VIEW_MATRIX * mat4(INV_VIEW_MATRIX[0], INV_VIEW_MATRIX[1], INV_VIEW_MATRIX[2], MODEL_MATRIX[3]);
}
void fragment() {
	vec2 uv = UV;
	float border = step(uv.x, 0.012) + step(0.988, uv.x) + step(uv.y, 0.12) + step(0.88, uv.y);
	vec3 bg = vec3(0.04, 0.03, 0.03);
	vec3 c = bg;
	if (uv.x < lag) c = vec3(0.95, 0.85, 0.55);
	if (uv.x < fill) c = fill_color.rgb * (0.75 + 0.25 * (1.0 - uv.y));
	if (uv.x < shield && uv.y < 0.35) c = vec3(0.6, 0.75, 1.0);
	c = mix(c, vec3(0.55, 0.42, 0.25), clamp(border, 0.0, 1.0));
	ALBEDO = c;
	ALPHA = alpha * 0.95;
}
"""
	_quad = MeshInstance3D.new()
	var q := QuadMesh.new()
	var w := 1.1 if not enemy.is_elite else 1.5
	q.size = Vector2(w, 0.12 if not enemy.is_elite else 0.15)
	_quad.mesh = q
	_mat = ShaderMaterial.new()
	_mat.shader = _shader
	_mat.render_priority = 5
	if enemy.is_elite:
		_mat.set_shader_parameter("fill_color", Color(0.95, 0.55, 0.12))
	_quad.material_override = _mat
	_quad.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(_quad)
	position = Vector3(0, enemy.body_height * enemy.def.model_scale * (1.12 if enemy.is_elite else 1.0) + 0.45, 0)
	if enemy.is_elite:
		_label = Label3D.new()
		_label.text = enemy.display_name if not enemy.is_miniboss() else "%s\n%s" % [enemy.display_name, enemy.miniboss.get("title", "Champion")]
		_label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		_label.no_depth_test = true
		_label.fixed_size = true
		_label.pixel_size = 0.0009
		_label.font = UITheme.body_bold()
		_label.font_size = 26
		_label.outline_size = 8
		_label.outline_modulate = Color(0, 0, 0, 0.9)
		_label.modulate = BH.rarity_color(BH.Rarity.ELITE) if not enemy.is_miniboss() else Color(1.0, 0.66, 0.3)
		if enemy.is_miniboss():
			_label.font_size = 30
		_label.position = Vector3(0, 0.28, 0)
		_label.render_priority = 6
		add_child(_label)
	visible = false

func touch() -> void:
	_visible_t = SHOW_TIME

func _process(delta: float) -> void:
	if enemy == null or not is_instance_valid(enemy) or enemy.is_boss:
		visible = false
		return
	_visible_t -= delta
	var noted: bool = enemy.ext != null and enemy.brain.is_engaged() and not enemy.ext.bar_note().is_empty()
	var show := Settings.show_enemy_bars and (_visible_t > 0.0 or noted or (enemy.is_elite and enemy.brain.is_engaged()) or Game.hover_target == enemy \
		or (enemy.is_miniboss() and Game.player != null and is_instance_valid(Game.player) and (Game.player as Node3D).global_position.distance_to(enemy.global_position) < 18.0))
	visible = show
	if not show:
		return
	var f := clampf(enemy.hp / maxf(1.0, enemy.max_hp()), 0.0, 1.0)
	_shown_hp = f
	_lag_hp = maxf(f, move_toward(_lag_hp, f, delta * 0.6))
	_mat.set_shader_parameter("fill", _shown_hp)
	_mat.set_shader_parameter("lag", _lag_hp)
	_mat.set_shader_parameter("shield", clampf(enemy.shield_hp / maxf(1.0, enemy.max_hp()), 0.0, 1.0))
	_update_note()

## bh-010: one short line under the bar for the new monsters' states (the Rune Golem's current immunity, a burned
## troll, a lit powder keg, a swelling bloater).
func _update_note() -> void:
	var note: Array = enemy.ext.bar_note() if enemy.ext else []
	if note.is_empty():
		if _note:
			_note.visible = false
		return
	if _note == null:
		_note = Label3D.new()
		_note.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		_note.no_depth_test = true
		_note.fixed_size = true
		_note.pixel_size = 0.0008
		_note.font = UITheme.body_bold()
		_note.font_size = 22
		_note.outline_size = 7
		_note.outline_modulate = Color(0, 0, 0, 0.9)
		_note.position = Vector3(0, -0.2, 0)
		_note.render_priority = 6
		add_child(_note)
	_note.visible = true
	_note.text = String(note[0])
	_note.modulate = note[1]
