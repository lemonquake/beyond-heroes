class_name MaterialLibrary
## Shared materials keyed by the asset material-name contract (BH_*). Replaces imported glTF materials with
## textured, consistently lit versions and provides faded variants for camera occlusion.

const TEX := "res://assets/textures/%s_%s.png"

static var _env := {}
static var _char := {}
static var _faded := {}
static var _terrain_shader: Shader

# material name -> [texture set or "", albedo tint, roughness, metallic, uv scale (world triplanar m/tile), emission color, emission energy]
const ENV := {
	"BH_Stone": ["stone_blocks", Color(0.78, 0.76, 0.72), 0.9, 0.0, 0.5, Color.BLACK, 0.0],
	"BH_StoneDark": ["stone_blocks", Color(0.45, 0.44, 0.47), 0.92, 0.0, 0.5, Color.BLACK, 0.0],
	"BH_Brick": ["brick", Color(0.85, 0.8, 0.76), 0.9, 0.0, 0.5, Color.BLACK, 0.0],
	"BH_Cobble": ["cobblestone", Color(0.85, 0.83, 0.8), 0.9, 0.0, 0.4, Color.BLACK, 0.0],
	"BH_Wood": ["wood_planks", Color(0.8, 0.72, 0.62), 0.85, 0.0, 0.6, Color.BLACK, 0.0],
	"BH_WoodDark": ["wood_planks", Color(0.45, 0.38, 0.32), 0.85, 0.0, 0.6, Color.BLACK, 0.0],
	"BH_Bark": ["bark", Color(0.8, 0.76, 0.72), 0.95, 0.0, 0.8, Color.BLACK, 0.0],
	"BH_Leaves": ["", Color(0.30, 0.36, 0.20), 0.85, 0.0, 1.0, Color.BLACK, 0.0],
	"BH_Grass": ["grass", Color(0.8, 0.85, 0.7), 0.95, 0.0, 0.5, Color.BLACK, 0.0],
	"BH_Moss": ["moss", Color(0.85, 0.9, 0.8), 0.95, 0.0, 0.6, Color.BLACK, 0.0],
	"BH_Metal": ["metal_iron", Color(0.7, 0.7, 0.72), 0.45, 0.85, 1.0, Color.BLACK, 0.0],
	"BH_Iron": ["metal_iron", Color(0.45, 0.45, 0.48), 0.55, 0.8, 1.0, Color.BLACK, 0.0],
	"BH_Gold": ["", Color(0.83, 0.64, 0.3), 0.35, 1.0, 1.0, Color.BLACK, 0.0],
	"BH_Cloth": ["cloth", Color(0.55, 0.5, 0.42), 0.95, 0.0, 1.0, Color.BLACK, 0.0],
	"BH_ClothRed": ["cloth", Color(0.55, 0.14, 0.12), 0.95, 0.0, 1.0, Color.BLACK, 0.0],
	"BH_Bone": ["", Color(0.82, 0.78, 0.66), 0.8, 0.0, 1.0, Color.BLACK, 0.0],
	"BH_Candle": ["", Color(0.92, 0.88, 0.75), 0.6, 0.0, 1.0, Color(1.0, 0.8, 0.5), 0.3],
	"BH_Flame": ["", Color(1.0, 0.6, 0.2), 1.0, 0.0, 1.0, Color(1.0, 0.55, 0.15), 6.0],
	"BH_Rune": ["", Color(0.3, 0.8, 1.0), 0.4, 0.0, 1.0, Color(0.35, 0.8, 1.0), 4.0],
	"BH_Corruption": ["", Color(0.4, 0.1, 0.6), 0.5, 0.0, 1.0, Color(0.6, 0.2, 1.0), 3.5],
	"BH_Water": ["", Color(0.1, 0.35, 0.4), 0.05, 0.0, 1.0, Color(0.05, 0.25, 0.28), 0.5],
	"BH_Glass": ["", Color(0.95, 0.8, 0.55), 0.1, 0.0, 1.0, Color(1.0, 0.72, 0.38), 2.2],  # lantern panes, lit from within
	"BH_Thatch": ["thatch", Color(0.8, 0.72, 0.55), 0.95, 0.0, 0.8, Color.BLACK, 0.0],
	"BH_Dirt": ["dirt", Color(0.8, 0.75, 0.7), 0.95, 0.0, 0.5, Color.BLACK, 0.0],
	# bh-003: town buildings and interiors
	"BH_ClothBlue": ["cloth", Color(0.12, 0.24, 0.5), 0.95, 0.0, 1.0, Color.BLACK, 0.0],       # Swordfin Company
	"BH_ClothViolet": ["cloth", Color(0.3, 0.16, 0.42), 0.95, 0.0, 1.0, Color.BLACK, 0.0],    # Lantern Covenant
	"BH_Silver": ["", Color(0.8, 0.82, 0.86), 0.3, 1.0, 1.0, Color.BLACK, 0.0],
	"BH_Plaster": ["", Color(0.78, 0.72, 0.62), 0.95, 0.0, 1.0, Color.BLACK, 0.0],
	"BH_Bottle": ["", Color(0.2, 0.42, 0.25), 0.08, 0.0, 1.0, Color(0.05, 0.12, 0.06), 0.4],
	"BH_Paper": ["", Color(0.86, 0.8, 0.66), 0.9, 0.0, 1.0, Color.BLACK, 0.0],
	"BH_Rope": ["", Color(0.55, 0.45, 0.3), 0.95, 0.0, 1.0, Color.BLACK, 0.0],
}

# Character material names -> [albedo, roughness, metallic, emission, energy, detail texture set]
const CHAR := {
	"BH_Steel": [Color(0.62, 0.63, 0.66), 0.38, 0.9, Color.BLACK, 0.0, "metal_iron"],
	"BH_DarkSteel": [Color(0.22, 0.22, 0.25), 0.45, 0.85, Color.BLACK, 0.0, "metal_iron"],
	"BH_Gold": [Color(0.85, 0.66, 0.32), 0.32, 1.0, Color.BLACK, 0.0, ""],
	"BH_Leather": [Color(0.3, 0.2, 0.14), 0.75, 0.0, Color.BLACK, 0.0, ""],
	"BH_Cloth_Secondary": [Color(0.22, 0.2, 0.18), 0.95, 0.0, Color.BLACK, 0.0, "cloth"],
	"BH_Skin": [Color(0.72, 0.55, 0.45), 0.6, 0.0, Color.BLACK, 0.0, ""],
	"BH_Bone": [Color(0.82, 0.78, 0.66), 0.75, 0.0, Color.BLACK, 0.0, ""],
	"BH_Rust": [Color(0.4, 0.24, 0.15), 0.8, 0.5, Color.BLACK, 0.0, "metal_iron"],
	"BH_Emissive": [Color(0.5, 0.8, 1.0), 0.4, 0.0, Color(0.55, 0.8, 1.0), 3.0, ""],
	"BH_Shadow": [Color(0.08, 0.06, 0.12), 0.9, 0.0, Color(0.2, 0.1, 0.35), 0.8, ""],
	"BH_WeakPoint": [Color(1.0, 0.4, 0.2), 0.3, 0.0, Color(1.0, 0.45, 0.2), 5.0, ""],
	"BH_Wood": [Color(0.42, 0.3, 0.2), 0.8, 0.0, Color.BLACK, 0.0, "wood_planks"],
	"BH_Hair": [Color(0.12, 0.09, 0.07), 0.8, 0.0, Color.BLACK, 0.0, ""],
}

static func _tex(set_name: String, kind: String) -> Texture2D:
	var p := TEX % [set_name, kind]
	return load(p) if ResourceLoader.exists(p) else null

static func env(name: String) -> Material:
	var key := name.get_slice(".", 0)
	if _env.has(key):
		return _env[key]
	if not ENV.has(key):
		return null
	var d: Array = ENV[key]
	var m := StandardMaterial3D.new()
	m.resource_name = key
	m.albedo_color = d[1]
	m.roughness = d[2]
	m.metallic = d[3]
	if d[0] != "":
		m.albedo_texture = _tex(d[0], "albedo")
		var n := _tex(d[0], "normal")
		if n:
			m.normal_enabled = true
			m.normal_texture = n
			m.normal_scale = 1.0
		var r := _tex(d[0], "rough")
		if r:
			m.roughness_texture = r
			m.roughness_texture_channel = BaseMaterial3D.TEXTURE_CHANNEL_RED
		m.uv1_triplanar = true
		m.uv1_world_triplanar = true
		m.uv1_scale = Vector3.ONE * float(d[4])
		m.uv1_triplanar_sharpness = 4.0
	if float(d[6]) > 0.0:
		m.emission_enabled = true
		m.emission = d[5]
		m.emission_energy_multiplier = d[6]
	if key == "BH_Leaves":
		m.albedo_texture = load("res://assets/textures/leaves_atlas.png") if ResourceLoader.exists("res://assets/textures/leaves_atlas.png") else null
		m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
		m.alpha_scissor_threshold = 0.4
		m.cull_mode = BaseMaterial3D.CULL_DISABLED
		m.albedo_color = Color(0.55, 0.62, 0.42)
	if key == "BH_Grass":
		# grass clumps are alpha cards textured with the blade sheet (mesh UVs, not triplanar)
		m.albedo_texture = load("res://assets/textures/grass_blades.png") if ResourceLoader.exists("res://assets/textures/grass_blades.png") else null
		m.uv1_triplanar = false
		m.uv1_world_triplanar = false
		m.uv1_scale = Vector3.ONE
		m.normal_enabled = false
		m.roughness_texture = null
		m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
		m.alpha_scissor_threshold = 0.45
		m.cull_mode = BaseMaterial3D.CULL_DISABLED
		m.albedo_color = Color(0.62, 0.7, 0.45)
		m.backlight_enabled = true
		m.backlight = Color(0.25, 0.3, 0.15)
	if key == "BH_Water":
		m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		m.albedo_color.a = 0.8
	if key in ["BH_Flame", "BH_Rune", "BH_Corruption"]:
		m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_env[key] = m
	return m

## Replace every surface material on an environment scene with the library version when the name matches.
static func apply_environment(root: Node) -> void:
	if root is MeshInstance3D:
		var mi: MeshInstance3D = root
		if mi.mesh:
			for i in mi.mesh.get_surface_count():
				var mat := mi.mesh.surface_get_material(i)
				var nm := mat.resource_name if mat else ""
				var rep := env(nm)
				if rep:
					mi.set_surface_override_material(i, rep)
	for c in root.get_children():
		apply_environment(c)

static func apply_character(meshes: Array, primary: Color) -> void:
	for mi: MeshInstance3D in meshes:
		if mi.mesh == null:
			continue
		for i in mi.mesh.get_surface_count():
			var mat := mi.mesh.surface_get_material(i)
			var nm := mat.resource_name.get_slice(".", 0) if mat else ""
			var rep := _palette_mat(nm, mat) if "__" in nm else _char_mat(nm, primary)
			if rep:
				mi.set_surface_override_material(i, rep)

## Palette materials ("BH_Emissive__ghoul_brute"): each enemy/townsfolk model exports its own colours. The shared
## surface setup (roughness, metalness, detail normal textures) comes from CHAR by base name; the colours come from
## the imported material, so every model keeps its palette. Unknown base names ("BH_Fur__dire_wolf") keep the imported
## PBR values entirely.
static func _palette_mat(nm: String, src: Material) -> Material:
	if _char.has(nm):
		return _char[nm]
	var base := nm.get_slice("__", 0)
	var imported := src as BaseMaterial3D
	var m := StandardMaterial3D.new()
	var d: Array = CHAR.get(base, [])
	if base == "BH_Cloth_Primary":
		d = [Color.WHITE, 0.9, 0.0, Color.BLACK, 0.0, "cloth"]
	if not d.is_empty():
		m.roughness = d[1]
		m.metallic = d[2]
		if d[5] != "":
			var n := _tex(d[5], "normal")
			if n:
				m.normal_enabled = true
				m.normal_texture = n
				m.normal_scale = 0.5
				m.uv1_scale = Vector3.ONE * 2.0
	if imported:
		m.albedo_color = imported.albedo_color
		if d.is_empty():
			m.roughness = imported.roughness
			m.metallic = imported.metallic
		if imported.emission_enabled:
			m.emission_enabled = true
			m.emission = imported.emission
			m.emission_energy_multiplier = clampf(imported.emission_energy_multiplier, 1.0, 4.0)
	elif not d.is_empty():
		m.albedo_color = d[0]
	m.rim_enabled = true
	m.rim = 0.25
	m.rim_tint = 0.6
	_char[nm] = m
	return m

static func _char_mat(nm: String, primary: Color) -> Material:
	var key := nm
	if nm == "BH_Cloth_Primary":
		key = "%s_%s" % [nm, primary.to_html(false)]
	if _char.has(key):
		return _char[key]
	var m := StandardMaterial3D.new()
	if nm == "BH_Cloth_Primary":
		m.albedo_color = primary
		m.roughness = 0.9
		m.albedo_texture = _tex("cloth", "albedo")
		m.uv1_scale = Vector3.ONE * 3.0
	elif CHAR.has(nm):
		var d: Array = CHAR[nm]
		m.albedo_color = d[0]
		m.roughness = d[1]
		m.metallic = d[2]
		if float(d[4]) > 0.0:
			m.emission_enabled = true
			m.emission = d[3]
			m.emission_energy_multiplier = d[4]
		if d[5] != "":
			var n := _tex(d[5], "normal")
			if n:
				m.normal_enabled = true
				m.normal_texture = n
				m.normal_scale = 0.5
				m.uv1_scale = Vector3.ONE * 2.0
	else:
		return null
	m.rim_enabled = true
	m.rim = 0.25
	m.rim_tint = 0.6
	_char[key] = m
	return m

## Dithered see-through variant used when geometry blocks the camera's view of the player.
static func faded(mat: Material) -> Material:
	if mat == null:
		return null
	if _faded.has(mat):
		return _faded[mat]
	var f: Material = mat.duplicate()
	if f is BaseMaterial3D:
		f.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_HASH
		f.albedo_color.a = 0.28
	_faded[mat] = f
	return f

static func terrain_shader() -> Shader:
	if _terrain_shader:
		return _terrain_shader
	_terrain_shader = Shader.new()
	_terrain_shader.code = """
shader_type spatial;
// Splat terrain: vertex color R = dirt/path, G = moss/forest floor, B = cobble/stone path; slope -> rock cliff.
uniform sampler2D tex_grass : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D tex_dirt : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D tex_moss : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D tex_path : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D tex_rock : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D nrm_grass : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D nrm_dirt : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D nrm_rock : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D nrm_path : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
uniform float scale = 0.25;
uniform vec4 tint : source_color = vec4(1.0);
varying vec3 wpos;
varying vec3 wnrm;
void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	wnrm = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}
vec4 tri(sampler2D t, vec3 p, vec3 n) {
	vec3 w = pow(abs(n), vec3(4.0));
	w /= (w.x + w.y + w.z);
	return texture(t, p.zy) * w.x + texture(t, p.xz) * w.y + texture(t, p.xy) * w.z;
}
void fragment() {
	vec2 uv = wpos.xz * scale;
	float slope = 1.0 - clamp((wnrm.y - 0.55) / 0.3, 0.0, 1.0);
	vec4 c = COLOR;
	vec3 grass = texture(tex_grass, uv).rgb;
	vec3 dirt = texture(tex_dirt, uv * 1.1).rgb;
	vec3 moss = texture(tex_moss, uv * 0.9).rgb;
	vec3 path = texture(tex_path, uv * 1.4).rgb;
	vec3 rock = tri(tex_rock, wpos * scale * 0.8, wnrm).rgb;
	float noise = texture(tex_dirt, uv * 0.07).r;
	float r = smoothstep(0.35, 0.65, c.r + (noise - 0.5) * 0.5);
	float g = smoothstep(0.35, 0.65, c.g + (noise - 0.5) * 0.4);
	float b = smoothstep(0.4, 0.6, c.b + (noise - 0.5) * 0.3);
	vec3 col = mix(grass, moss, g);
	col = mix(col, dirt, r);
	col = mix(col, path, b);
	col = mix(col, rock, slope);
	vec3 n = texture(nrm_grass, uv).rgb;
	n = mix(n, texture(nrm_dirt, uv * 1.1).rgb, r);
	n = mix(n, texture(nrm_path, uv * 1.4).rgb, b);
	n = mix(n, tri(nrm_rock, wpos * scale * 0.8, wnrm).rgb, slope);
	ALBEDO = col * tint.rgb;
	NORMAL_MAP = n;
	ROUGHNESS = mix(0.95, 0.8, b);
}
"""
	return _terrain_shader

static func terrain_material(grass := "grass", dirt := "dirt", moss := "forest_floor", path := "cobblestone", rock := "rock_cliff", tint := Color.WHITE) -> ShaderMaterial:
	var m := ShaderMaterial.new()
	m.shader = terrain_shader()
	m.set_shader_parameter("tex_grass", _tex(grass, "albedo"))
	m.set_shader_parameter("tex_dirt", _tex(dirt, "albedo"))
	m.set_shader_parameter("tex_moss", _tex(moss, "albedo"))
	m.set_shader_parameter("tex_path", _tex(path, "albedo"))
	m.set_shader_parameter("tex_rock", _tex(rock, "albedo"))
	m.set_shader_parameter("nrm_grass", _tex(grass, "normal"))
	m.set_shader_parameter("nrm_dirt", _tex(dirt, "normal"))
	m.set_shader_parameter("nrm_rock", _tex(rock, "normal"))
	m.set_shader_parameter("nrm_path", _tex(path, "normal"))
	m.set_shader_parameter("tint", tint)
	return m
