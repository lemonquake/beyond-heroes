class_name GemSpirits
extends Node3D
## bh-038: every crystal set in a held weapon (or shield) becomes a small spirit that circles it. Three crystals of
## three families make three different spirits; two of the same family make two of the same kind. Each family has its
## own drawn shape, colours, way of moving and trail (DataCrystals.FAMILIES):
##   Ember        a flame-tongue that flickers and licks upward, shedding embers
##   Aqua         a bead of sea-water with a moving highlight and rings that ripple out of it, dripping
##   Nova         a four-point star that turns and twinkles, scattering glints
##   Thundra      a white core in a jagged ring of lightning that re-strikes many times a second; it twitches
##   Vipera       a serpent's eye whose slit pupil narrows and blinks; it weaves up and down; venom drips
##   Bloodrift    a dark heart with glowing veins that beats twice and rests; blood mist sinks from it
##   Essencerift  a violet vortex turning into a black centre; it breathes in and out from the blade
##   Aetherift    a hexagonal shard of shifting rainbow split by a white rift; prismatic motes
##   Sora         a curl of open-sky wind round a cloud-white heart; it races
##   Luna         a pale crescent moon with a faint halo; it drifts slowly
##   Sol          a little sun with two crowns of turning rays; rising sparks
##   Airah        two mint leaves spinning like a seed on the wind; it loops in figure-eights
## The higher a crystal's grade (Fragment .. Orbital), the larger and brighter its spirit. Heroes and their previews
## get the trails; companions get the spirits alone (cheap: one billboard each).

const SHADER := """
shader_type spatial;
render_mode blend_mix, unshaded, depth_draw_never, shadows_disabled, fog_disabled, cull_disabled;
uniform int mode = 0;
uniform vec4 c1 : source_color = vec4(1.0);
uniform vec4 c2 : source_color = vec4(1.0);
uniform float strength = 1.0;
uniform float seed = 0.0;

float h21(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float n2(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	return mix(mix(h21(i), h21(i + vec2(1.0, 0.0)), f.x), mix(h21(i + vec2(0.0, 1.0)), h21(i + vec2(1.0, 1.0)), f.x), f.y);
}
vec2 rot(vec2 p, float a) { float c = cos(a); float s = sin(a); return vec2(c * p.x - s * p.y, s * p.x + c * p.y); }
vec3 hue(float h) { return clamp(abs(fract(h + vec3(0.0, 0.6667, 0.3333)) * 6.0 - 3.0) - 1.0, 0.0, 1.0); }

void vertex() {
	// a billboard that keeps its node's scale
	float s = length(MODEL_MATRIX[0].xyz);
	MODELVIEW_MATRIX = VIEW_MATRIX * mat4(INV_VIEW_MATRIX[0] * s, INV_VIEW_MATRIX[1] * s, INV_VIEW_MATRIX[2] * s, MODEL_MATRIX[3]);
	MODELVIEW_NORMAL_MATRIX = mat3(MODELVIEW_MATRIX);
}

void fragment() {
	vec2 p = UV * 2.0 - 1.0;
	p.y = -p.y;
	float r = length(p);
	float a = atan(p.y, p.x);
	float t = TIME + seed * 7.0;
	vec3 col = vec3(0.0);
	float al = 0.0;
	float halo = exp(-r * r * 6.0);
	if (mode == 0) {
		// Ember: a flame-tongue, round below, licking upward, flickering
		vec2 q = p + vec2(0.0, 0.18);
		float fl = n2(vec2(q.x * 3.0 + seed, q.y * 2.5 - t * 5.0));
		float w = mix(0.46, 0.04, clamp((q.y + 0.4) / 1.25, 0.0, 1.0));
		float body = smoothstep(w, w * 0.35, abs(q.x + (fl - 0.5) * 0.3 * (q.y + 0.45)))
			* smoothstep(0.95, 0.35, q.y + fl * 0.35) * smoothstep(-0.62, -0.32, q.y);
		float core = smoothstep(0.32, 0.0, length(q * vec2(1.4, 1.0) + vec2(0.0, 0.08)));
		col = mix(c2.rgb, c1.rgb, body) * body * 1.6 + vec3(1.0, 0.92, 0.6) * core * 1.6 + c1.rgb * halo * 0.5;
		al = max(max(body, core), halo * 0.45);
	} else if (mode == 1) {
		// Aqua: a bead of water, a highlight that rolls over it, rings rippling outward
		float bead = smoothstep(0.46, 0.42, r);
		vec3 water = mix(c2.rgb, c1.rgb, 0.5 + 0.6 * p.y) * (0.75 + 0.35 * n2(p * 3.0 + vec2(t * 0.6, t * 0.4)));
		vec2 hp = p - vec2(-0.15 + 0.05 * sin(t * 1.3), 0.17);
		float hl = smoothstep(0.12, 0.0, length(hp * vec2(1.0, 1.6)));
		float rim = smoothstep(0.06, 0.0, abs(r - 0.43));
		float ph = fract(t * 0.55);
		float ring = smoothstep(0.035, 0.0, abs(r - (0.45 + ph * 0.5))) * (1.0 - ph);
		col = water * bead * 1.2 + vec3(1.0) * hl * 1.6 + c1.rgb * (rim * 0.9 + ring * 1.3) + c1.rgb * halo * 0.3;
		al = max(max(bead * 0.9, hl), max(ring, halo * 0.35));
	} else if (mode == 2) {
		// Nova: a four-point star turning slowly, twinkling, with fainter diagonal points
		vec2 q = rot(p, t * 0.6);
		float tw = 0.75 + 0.25 * sin(t * 7.0) * sin(t * 3.1);
		float main_r = max(smoothstep(0.07, 0.0, abs(q.x)) * smoothstep(0.95, 0.0, abs(q.y)),
			smoothstep(0.07, 0.0, abs(q.y)) * smoothstep(0.95, 0.0, abs(q.x)));
		vec2 d = rot(q, 0.785398);
		float diag = max(smoothstep(0.04, 0.0, abs(d.x)) * smoothstep(0.5, 0.0, abs(d.y)),
			smoothstep(0.04, 0.0, abs(d.y)) * smoothstep(0.5, 0.0, abs(d.x)));
		float core = smoothstep(0.22, 0.0, r);
		col = mix(c1.rgb, vec3(1.0), 0.5) * (main_r * tw * 1.8 + diag * 0.9) + vec3(1.0) * core * 2.0 + c1.rgb * halo * 0.45;
		al = clamp(main_r * tw + diag * 0.7 + core + halo * 0.4, 0.0, 1.0);
	} else if (mode == 3) {
		// Thundra: a white-hot core in a jagged ring of lightning that strikes anew ~14 times a second
		float step_t = floor(t * 14.0);
		float j = n2(vec2(a * 2.5 + step_t * 3.7, step_t)) - 0.5;
		float j2 = n2(vec2(a * 6.0 - step_t * 1.3, step_t * 0.7)) - 0.5;
		float bolt = smoothstep(0.045, 0.0, abs(r - 0.34 - j * 0.28 - j2 * 0.08));
		float spoke = smoothstep(0.03, 0.0, abs(rot(p, step_t * 2.1).x + (n2(vec2(r * 8.0, step_t)) - 0.5) * 0.12))
			* step(0.15, r) * smoothstep(0.75, 0.3, r) * step(0.5, h21(vec2(step_t, 3.0)));
		float core = smoothstep(0.24, 0.05, r);
		col = mix(c1.rgb, vec3(1.0), 0.55) * (bolt + spoke) * 2.0 + vec3(1.0, 1.0, 0.92) * core * 1.8 + c1.rgb * halo * 0.5;
		al = clamp(bolt + spoke + core + halo * 0.35, 0.0, 1.0);
	} else if (mode == 4) {
		// Vipera: a serpent's eye — a gold-green iris with a dark slit pupil that narrows, widens and blinks, set in
		// a dark lid, with a venom-green glow round it
		float lid = mix(0.36, 0.03, step(0.93, fract(t * 0.23 + seed)));     // a blink every few seconds
		float ex = p.x / 0.5;
		float edge = lid * sqrt(max(0.0, 1.0 - ex * ex));
		float eye = smoothstep(0.02, -0.02, abs(p.y) - edge) * step(abs(ex), 1.0);
		float outline = smoothstep(0.05, 0.0, abs(abs(p.y) - edge - 0.03)) * step(abs(ex), 1.05);
		float pw = 0.045 + 0.035 * sin(t * 1.7);
		float pupil = smoothstep(0.012, -0.012, abs(p.x) - pw * sqrt(max(0.0, 1.0 - p.y * p.y / 0.13)));
		float rad = length(p / vec2(0.5, 0.36));
		float fib = 0.75 + 0.35 * n2(vec2(a * 9.0, rad * 3.0));
		vec3 iris = mix(vec3(1.0, 0.85, 0.2), c1.rgb, smoothstep(0.1, 0.8, rad)) * fib;
		iris = mix(iris, c2.rgb, smoothstep(0.75, 1.0, rad));
		vec3 eyec = mix(iris * 1.5, vec3(0.02, 0.03, 0.0), pupil);
		col = eyec * eye + c2.rgb * outline * (1.0 - eye) * 0.6 + c1.rgb * halo * 0.6 * (1.0 - eye);
		al = max(eye, max(outline * 0.9, halo * 0.45));
	} else if (mode == 5) {
		// Bloodrift: a dark-red heart with glowing veins; it beats twice, then rests
		float ph = fract(t * 0.9);
		float beat = exp(-ph * 26.0) + 0.7 * exp(-max(ph - 0.18, 0.0) * 26.0) * step(0.18, ph);
		float rr = r / (1.0 + beat * 0.14);
		float orb = smoothstep(0.44, 0.39, rr);
		float v = n2(p * 4.5 + vec2(seed * 3.0, 0.0));
		float vein = smoothstep(0.08, 0.0, abs(v - 0.5)) * orb;
		float rim = smoothstep(0.08, 0.0, abs(rr - 0.41));
		vec3 heart = mix(c1.rgb * 0.55, c2.rgb, smoothstep(0.0, 0.4, rr));
		col = heart * orb + c1.rgb * (vein * (1.6 + beat * 3.0) + rim * (1.4 + beat * 1.5)) + c1.rgb * halo * (0.6 + beat * 0.9);
		al = max(orb, max(rim, halo * (0.55 + beat * 0.4)));
	} else if (mode == 6) {
		// Essencerift: a vortex of violet turning into a black centre
		float sp = sin(a * 3.0 + log(max(r, 0.02)) * 9.0 + t * 5.0);
		float arms = smoothstep(0.2, 1.0, sp) * smoothstep(0.62, 0.3, r) * smoothstep(0.05, 0.16, r);
		float hole = smoothstep(0.17, 0.08, r);
		float rim = smoothstep(0.05, 0.0, abs(r - 0.5)) * 0.8;
		col = mix(c1.rgb, vec3(0.92, 0.88, 1.0), arms * 0.4) * arms * 1.8 + c1.rgb * (rim + halo * 0.4) + c2.rgb * hole * 0.1;
		al = clamp(arms + hole + rim + halo * 0.35, 0.0, 1.0);
	} else if (mode == 7) {
		// Aetherift: a hexagonal shard of shifting rainbow, split by a white rift
		vec2 q = abs(rot(p, t * 0.4));
		float hex = max(q.x * 0.866 + q.y * 0.5, q.y);
		float shard = smoothstep(0.47, 0.44, hex);
		float edge = smoothstep(0.05, 0.0, abs(hex - 0.45));
		// facets: each of the six wedges its own hue, drifting round
		float wedge = floor((atan(q.y, q.x) + 3.14159) / 1.0472);
		vec3 rainbow = hue(t * 0.2 + wedge / 6.0 + r * 0.4) * (0.55 + 0.35 * smoothstep(0.45, 0.0, r));
		float rift = smoothstep(0.04, 0.0, abs(p.x + 0.08 * sin(p.y * 9.0 + t * 3.0))) * smoothstep(0.45, 0.1, abs(p.y));
		col = rainbow * shard * 1.25 + vec3(1.0) * (edge * 1.1 + rift * 1.8) + rainbow * halo * 0.5;
		al = clamp(shard * 0.8 + edge + rift + halo * 0.4, 0.0, 1.0);
	} else if (mode == 8) {
		// Sora: a curl of open-sky wind racing round a cloud-white heart
		float curl = 0.0;
		for (int i = 0; i < 2; i++) {
			float off = float(i) * 3.14159;
			float rr = 0.24 + 0.16 * fract((a + off - t * 4.0) / 6.28318);
			float seg = smoothstep(0.045, 0.0, abs(r - rr)) * smoothstep(0.0, 0.7, fract((a + off - t * 4.0) / 6.28318));
			curl += seg;
		}
		float cloud = smoothstep(0.24, 0.05, r) * (0.7 + 0.3 * n2(p * 6.0 + vec2(t, 0.0)));
		col = mix(c1.rgb, vec3(1.0), 0.35) * curl * 1.7 + vec3(0.95, 0.98, 1.0) * cloud * 1.4 + c1.rgb * halo * 0.45;
		al = clamp(curl + cloud + halo * 0.4, 0.0, 1.0);
	} else if (mode == 9) {
		// Luna: a pale crescent moon, a faint halo, one glint
		vec2 q = rot(p, 0.35 * sin(t * 0.5));
		float disc = smoothstep(0.42, 0.38, length(q));
		float bite = smoothstep(0.37, 0.33, length(q - vec2(0.17, 0.07)));
		float moon = disc * (1.0 - bite);
		float shade = 0.75 + 0.25 * n2(q * 7.0);
		float glint = smoothstep(0.05, 0.0, length(p - vec2(0.3, 0.32))) * (0.5 + 0.5 * sin(t * 2.3));
		col = mix(c1.rgb, vec3(1.0), 0.45) * moon * shade * 1.6 + vec3(1.0) * glint * 1.5 + c1.rgb * halo * 0.45;
		al = clamp(moon + glint + halo * 0.4, 0.0, 1.0);
	} else if (mode == 10) {
		// Sol: a little sun with two crowns of rays turning opposite ways
		float disc = smoothstep(0.25, 0.21, r);
		float rays1 = pow(0.5 + 0.5 * cos(a * 12.0 + t * 1.6), 5.0) * smoothstep(0.8, 0.24, r) * step(0.2, r);
		float rays2 = pow(0.5 + 0.5 * cos(a * 7.0 - t * 2.3), 7.0) * smoothstep(0.62, 0.24, r) * step(0.2, r);
		col = vec3(1.0, 0.97, 0.85) * disc * 2.0 + mix(c1.rgb, c2.rgb, 0.4) * (rays1 + rays2) * 1.7 + c1.rgb * halo * 0.55;
		al = clamp(disc + rays1 + rays2 + halo * 0.45, 0.0, 1.0);
	} else {
		// Airah: two mint leaves spinning like a seed on the wind
		vec2 q = rot(p, t * 5.0);
		float leaves = 0.0;
		float vein = 0.0;
		for (int i = 0; i < 2; i++) {
			vec2 l = (i == 0 ? q : -q) - vec2(0.0, 0.25);
			float d = length(l * vec2(2.6, 1.15));
			leaves += smoothstep(0.32, 0.27, d);
			vein += smoothstep(0.02, 0.0, abs(l.x)) * step(d, 0.3);
		}
		float seed_c = smoothstep(0.1, 0.05, r);
		col = mix(c2.rgb, c1.rgb, 0.65) * leaves * 1.4 + vec3(1.0) * (vein * 0.6 + seed_c * 1.6) + c1.rgb * halo * 0.45;
		al = clamp(leaves + seed_c + halo * 0.4, 0.0, 1.0);
	}
	al *= smoothstep(1.0, 0.85, r);
	ALBEDO = col * strength;
	ALPHA = clamp(al, 0.0, 1.0);
}
"""

## family -> [shader mode, secondary colour, orbit radius, revolutions per second, trail: [amount, lifetime, size,
##            velocity, spread, gravity]]
const LOOK := {
	&"ember": [0, Color(0.95, 0.12, 0.02), 0.17, 0.42, [9, 0.55, 0.05, 0.25, 30.0, Vector3(0, 0.9, 0)]],
	&"aqua": [1, Color(0.02, 0.2, 0.55), 0.18, 0.3, [6, 0.7, 0.045, 0.05, 20.0, Vector3(0, -1.6, 0)]],
	&"nova": [2, Color(1.0, 0.8, 0.4), 0.2, 0.36, [7, 0.6, 0.04, 0.15, 180.0, Vector3.ZERO]],
	&"thundra": [3, Color(0.75, 0.75, 1.0), 0.16, 0.55, [8, 0.22, 0.035, 0.9, 180.0, Vector3.ZERO]],
	&"vipera": [4, Color(0.04, 0.25, 0.02), 0.19, 0.3, [6, 0.7, 0.045, 0.05, 15.0, Vector3(0, -1.8, 0)]],
	&"bloodrift": [5, Color(0.3, 0.0, 0.04), 0.17, 0.28, [7, 0.8, 0.07, 0.08, 40.0, Vector3(0, -0.5, 0)]],
	&"essencerift": [6, Color(0.02, 0.0, 0.06), 0.2, 0.34, [7, 0.5, 0.04, 0.0, 180.0, Vector3.ZERO]],
	&"aetherift": [7, Color(1.0, 1.0, 1.0), 0.21, 0.32, [8, 0.7, 0.04, 0.2, 180.0, Vector3(0, 0.3, 0)]],
	&"sora": [8, Color(0.85, 0.95, 1.0), 0.22, 0.7, [7, 0.45, 0.05, 0.05, 180.0, Vector3.ZERO]],
	&"luna": [9, Color(0.4, 0.35, 0.8), 0.21, 0.18, [5, 1.0, 0.04, 0.04, 180.0, Vector3(0, -0.15, 0)]],
	&"sol": [10, Color(1.0, 0.45, 0.1), 0.19, 0.32, [8, 0.6, 0.045, 0.3, 25.0, Vector3(0, 0.6, 0)]],
	&"airah": [11, Color(0.15, 0.6, 0.35), 0.2, 0.5, [6, 0.6, 0.04, 0.12, 180.0, Vector3(0, 0.15, 0)]],
}
## Billboard size (m) and brightness per grade: Fragment, Shard, Crystalline, Orbital.
const SIZE := [0.1, 0.12, 0.145, 0.17]
const STRENGTH := [0.85, 1.0, 1.15, 1.3]

static var _shader_res: Shader
static var _mats := {}
static var _quads := {}

var length := 0.9
var trails := true
var _spirits: Array[Node3D] = []
var _fams: Array[StringName] = []
var _t := 0.0

## The spirits for `gems` (an item's gem list; empty entries are skipped). `length`: how far along the weapon's +Y
## they circle. `trails`: whether each spirit leaves its particle trail.
static func make(gems: Array, weapon_length := 0.9, with_trails := true) -> GemSpirits:
	var g := GemSpirits.new()
	g.name = "GemSpirits"
	g.length = weapon_length
	g.trails = with_trails
	for id in gems:
		if String(id) == "":
			continue
		var fam := DataCrystals.family_of(StringName(id))
		if fam == &"" or not LOOK.has(fam):
			continue
		g._add(fam, maxi(0, DataCrystals.grade_of(StringName(id))))
	return g

func count() -> int:
	return _spirits.size()

func families() -> Array[StringName]:
	return _fams.duplicate()

func _add(fam: StringName, grade: int) -> void:
	var look: Array = LOOK[fam]
	var s := Node3D.new()
	s.name = "Spirit_%s_%d" % [fam, _spirits.size()]
	add_child(s)
	var mi := MeshInstance3D.new()
	mi.name = "Orb"
	mi.mesh = quad(grade)
	mi.material_override = material(fam, grade)
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	mi.gi_mode = GeometryInstance3D.GI_MODE_DISABLED
	s.add_child(mi)
	if trails:
		var tr: Array = look[4]
		var c: Color = (DataCrystals.FAMILIES[fam] as Dictionary).color
		var p := LootFx.small_particles(Color(c.lerp(Color.WHITE, 0.25), 0.8), int(tr[0]) + grade, float(tr[1]),
			float(tr[2]) * (0.85 + 0.1 * grade), float(tr[3]), float(tr[4]), tr[5], 0.02)
		p.name = "Trail"
		p.local_coords = false
		p.visibility_aabb = AABB(Vector3(-2, -2, -2), Vector3(4, 4, 4))
		s.add_child(p)
	_spirits.append(s)
	_fams.append(fam)

## One shared material per family and grade: every spirit uses the same shader (compiled once).
static func material(fam: StringName, grade: int) -> ShaderMaterial:
	var key := "%s|%d" % [fam, grade]
	if _mats.has(key):
		return _mats[key]
	if _shader_res == null:
		_shader_res = Shader.new()
		_shader_res.code = SHADER
	var look: Array = LOOK[fam]
	var m := ShaderMaterial.new()
	m.shader = _shader_res
	m.set_shader_parameter("mode", int(look[0]))
	m.set_shader_parameter("c1", (DataCrystals.FAMILIES[fam] as Dictionary).color)
	m.set_shader_parameter("c2", look[1])
	m.set_shader_parameter("strength", STRENGTH[clampi(grade, 0, 3)])
	m.set_shader_parameter("seed", float(hash(fam) % 97) / 97.0)
	m.render_priority = 2
	_mats[key] = m
	return m

static func quad(grade: int) -> QuadMesh:
	var g := clampi(grade, 0, 3)
	if not _quads.has(g):
		var q := QuadMesh.new()
		q.size = Vector2.ONE * SIZE[g] * 2.0
		_quads[g] = q
	return _quads[g]

func _ready() -> void:
	_t = randf() * 10.0
	_place(0.0)

func _process(delta: float) -> void:
	_place(delta)

## Each spirit circles the weapon's +Y axis at its own phase (evenly spread), height (spread along the blade) and its
## family's pace and manner of moving.
func _place(delta: float) -> void:
	_t += delta
	var n := _spirits.size()
	if n == 0:
		return
	for i in n:
		var fam := _fams[i]
		var look: Array = LOOK[fam]
		var rad := float(look[2])
		var phase := TAU * float(i) / float(n)
		var ang := phase + _t * TAU * float(look[3])
		var h := length * (0.3 + 0.6 * (float(i) + 0.5) / float(n))
		var pos := Vector3.ZERO
		match fam:
			&"ember":
				h += sin(_t * 3.1 + phase) * 0.05
			&"aqua":
				rad += sin(_t * 2.0 + phase) * 0.02
				h += sin(_t * 1.4 + phase) * 0.04
			&"thundra":
				# it twitches: a small jump to a new offset many times a second
				var k := floorf(_t * 9.0 + phase)
				rad += (fposmod(sin(k * 12.9898) * 43758.5453, 1.0) - 0.5) * 0.05
				h += (fposmod(sin(k * 78.233) * 12543.1, 1.0) - 0.5) * 0.05
			&"vipera":
				h += sin(ang * 3.0) * 0.07
			&"bloodrift":
				h += sin(_t * 1.1 + phase) * 0.03
			&"essencerift":
				rad *= 0.75 + 0.35 * (0.5 + 0.5 * sin(_t * 1.6 + phase))
			&"sora":
				h += sin(ang * 2.0) * 0.04
			&"luna":
				h += sin(_t * 0.7 + phase) * 0.05
			&"airah":
				# a figure-eight round the blade
				rad *= 1.0 + 0.35 * sin(ang * 2.0)
				h += sin(ang * 2.0) * 0.08
		pos = Vector3(cos(ang) * rad, h, sin(ang) * rad)
		_spirits[i].position = pos
