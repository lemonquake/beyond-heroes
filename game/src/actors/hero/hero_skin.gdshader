shader_type spatial;
render_mode cull_back, diffuse_burley, specular_schlick_ggx;
// bh-023: the hero's skin. One draw call carries everything the creator changes on the body itself:
//   skin colour and pattern, eyes and brows (drawn in the face plane, so they stay sharp at any zoom and size),
//   lip colour, scalp and beard stubble, face markings, the underwear's colour, and the cut-outs where clothing covers
//   the body. The mesh supplies the rest pose: UV2 = (x, 1 - z) in metres, COLOR.g = packed depth, COLOR.r = the front
//   of the head (tools/blender/hero/hero_shapes.py).

uniform sampler2D skin_tex : filter_linear_mipmap, repeat_disable;
uniform sampler2D mask_tex : filter_linear_mipmap, repeat_disable;
// colours are passed as sRGB triplets and converted here (the detail texture is a ratio in sRGB space)
uniform vec3 skin_color = vec3(0.6985, 0.4925, 0.3833);
uniform vec3 underwear_color = vec3(0.09, 0.09, 0.10);
uniform int pattern = 0;
uniform vec3 pattern_color = vec3(0.12, 0.08, 0.06);
uniform float pattern_amount = 1.0;
uniform float pattern_scale = 1.0;
uniform vec3 hair_color = vec3(0.13, 0.09, 0.07);
uniform float scalp_shade = 0.0;
uniform float stubble = 0.0;
uniform vec3 lip_color = vec3(0.62, 0.32, 0.30);
uniform float lip_amount = 0.0;
uniform int eye_style = 0;
uniform vec3 eye_color = vec3(0.30, 0.22, 0.14);
uniform vec3 sclera_color = vec3(0.93, 0.92, 0.90);
uniform float eye_size = 1.0;
uniform float eye_spacing = 0.0;
uniform float eye_height = 0.0;
uniform float eye_tilt = 0.0;
uniform float eye_glow = 0.0;
uniform int brow_style = 0;
uniform vec3 brow_color = vec3(0.12, 0.08, 0.06);
uniform float brow_thick = 1.0;
uniform float brow_tilt = 0.0;
uniform float brow_height = 0.0;
uniform int marking = 0;
uniform vec3 marking_color = vec3(0.55, 0.08, 0.06);
// clothing cut-outs in the rest pose (from, to): sleeves and gloves along the arms (|x|), garments and boots by height
uniform vec2 hide_sleeve = vec2(9.0, 9.0);
uniform vec2 hide_glove_l = vec2(9.0, 9.0);
uniform vec2 hide_glove_r = vec2(9.0, 9.0);
uniform vec2 hide_z1 = vec2(9.0, 9.0);
uniform vec2 hide_z2 = vec2(9.0, 9.0);
uniform vec2 hide_boot_l = vec2(9.0, 9.0);
uniform vec2 hide_boot_r = vec2(9.0, 9.0);
uniform float opacity = 1.0;
uniform float decay = 0.0;

const vec2 EYE = vec2(0.0335, 1.687);
const float BROW_Z = 1.708;
const float Y_PACK = 0.32;

varying vec3 rest;
varying float face;

vec3 lin(vec3 c) {
	return pow(max(c, vec3(0.0)), vec3(2.2));
}

vec3 hash3(vec3 p) {
	p = vec3(dot(p, vec3(127.1, 311.7, 74.7)), dot(p, vec3(269.5, 183.3, 246.1)), dot(p, vec3(113.5, 271.9, 124.6)));
	return fract(sin(p) * 43758.5453123);
}

float vnoise(vec3 p) {
	vec3 i = floor(p);
	vec3 f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	float n = mix(
		mix(mix(hash3(i).x, hash3(i + vec3(1, 0, 0)).x, f.x), mix(hash3(i + vec3(0, 1, 0)).x, hash3(i + vec3(1, 1, 0)).x, f.x), f.y),
		mix(mix(hash3(i + vec3(0, 0, 1)).x, hash3(i + vec3(1, 0, 1)).x, f.x), mix(hash3(i + vec3(0, 1, 1)).x, hash3(i + vec3(1, 1, 1)).x, f.x), f.y),
		f.z);
	return n;
}

// nearest and second-nearest cell distances, and the nearest cell's random value
vec3 worley(vec3 p) {
	vec3 i = floor(p);
	vec3 f = fract(p);
	float d1 = 8.0;
	float d2 = 8.0;
	float id = 0.0;
	for (int x = -1; x <= 1; x++) {
		for (int y = -1; y <= 1; y++) {
			for (int z = -1; z <= 1; z++) {
				vec3 g = vec3(float(x), float(y), float(z));
				vec3 h = hash3(i + g);
				float d = length(g + h - f);
				if (d < d1) {
					d2 = d1;
					d1 = d;
					id = h.z;
				} else if (d < d2) {
					d2 = d;
				}
			}
		}
	}
	return vec3(d1, d2, id);
}

void vertex() {
	rest = vec3(UV2.x, COLOR.g * 2.0 * Y_PACK - Y_PACK, 1.0 - UV2.y);
	face = COLOR.r;
}

// One eye. q is in the eye's own frame (metres, +x toward the ear). Returns premultiplied colour + coverage in a,
// glow in `emit`.
vec4 draw_eye(vec2 q, float side, float aa, out float emit) {
	emit = 0.0;
	float w = 0.0150;
	float hu = 0.0062;
	float hl = 0.0042;
	float pu = 0.75;
	float pl = 0.9;
	float iris = 0.0052;
	float lid = 0.0011;
	if (eye_style == 1) { w = 0.0135; hu = 0.0095; hl = 0.0078; pu = 0.5; pl = 0.5; iris = 0.0062; }
	else if (eye_style == 2) { w = 0.0160; hu = 0.0040; hl = 0.0027; pu = 0.8; iris = 0.0048; }
	else if (eye_style == 3) { hu = 0.0036; hl = 0.0046; lid = 0.0019; }
	else if (eye_style == 4) { hu = 0.0054; hl = 0.0030; pu = 1.2; lid = 0.0015; }
	else if (eye_style == 5) { hu = 0.0108; hl = 0.0064; pu = 0.55; pl = 0.6; iris = 0.0082; }
	else if (eye_style == 6) { w = 0.0156; hu = 0.0068; hl = 0.0046; iris = 0.0060; }
	if (eye_style == 7) {           // dots
		float d = length(q) - 0.0042;
		return vec4(vec3(0.02), 1.0) * smoothstep(aa, -aa, d);
	}
	float t = clamp(q.x / w, -1.0, 1.0);
	float env = 1.0 - t * t;
	// the outer corner sits a little higher than the inner one
	float skew = q.x * 0.10;
	float top = hu * pow(env, pu) + skew;
	float bot = -hl * pow(env, pl) + skew;
	if (eye_style == 9) {           // closed, smiling
		float d = abs(q.y - (hu * 0.8 * env - hu * 0.3)) - 0.0010;
		float a = smoothstep(aa, -aa, d) * smoothstep(w, w - aa * 2.0, abs(q.x));
		return vec4(vec3(0.03, 0.02, 0.02), 1.0) * a;
	}
	float inside = smoothstep(-aa, aa, top - q.y) * smoothstep(-aa, aa, q.y - bot) * smoothstep(w, w - aa, abs(q.x));
	vec3 col = sclera_color * mix(1.0, 0.62, smoothstep(top - 0.0035, top, q.y));
	vec2 ic = vec2(0.0, (top + bot) * 0.5 - skew + 0.0004 + q.x * 0.0);
	vec2 d2 = q - ic;
	float r = length(d2);
	float in_iris = smoothstep(iris + aa, iris - aa, r);
	vec3 icol = eye_color * mix(1.25, 0.55, smoothstep(iris * 0.35, iris, r));
	icol = mix(icol, eye_color * 0.25, smoothstep(iris * 0.82, iris, r));
	if (eye_style == 8) {           // glowing, no pupil
		icol = eye_color * 1.4;
		emit = in_iris;
	} else {
		vec2 pd = d2;
		if (eye_style == 6) { pd.x *= 3.6; }
		float pr = iris * (eye_style == 6 ? 0.8 : 0.44);
		icol = mix(icol, vec3(0.01), smoothstep(pr + aa, pr - aa, length(pd)));
		// one highlight, on the same side for both eyes
		vec2 hp = d2 - vec2(-0.30 * side, 0.34) * iris;
		icol = mix(icol, vec3(1.0), 0.9 * smoothstep(iris * 0.24 + aa, iris * 0.24 - aa, length(hp)));
		if (eye_style == 5) {
			hp = d2 - vec2(0.28 * side, -0.30) * iris;
			icol = mix(icol, vec3(1.0), 0.7 * smoothstep(iris * 0.13 + aa, iris * 0.13 - aa, length(hp)));
		}
		emit = in_iris * eye_glow;
	}
	col = mix(col, icol, in_iris);
	// lash line along the upper lid, heavier toward the outer corner; a faint lower lid
	float lash = lid * (0.7 + 0.6 * smoothstep(-w, w, q.x));
	float upper = smoothstep(lash + aa, lash - aa, abs(q.y - top - lash * 0.4)) * smoothstep(w + 0.001, w - aa, abs(q.x));
	float lower = 0.45 * smoothstep(0.0006 + aa, 0.0006 - aa, abs(q.y - bot)) * smoothstep(w, w - aa * 2.0, abs(q.x));
	vec4 o = vec4(col, 1.0) * inside;
	float line = max(upper, lower * (1.0 - inside * 0.5));
	o = mix(o, vec4(vec3(0.035, 0.025, 0.02), 1.0), line);
	emit *= inside;
	return o;
}

float draw_brow(vec2 q, float aa) {
	if (brow_style == 6) {
		return 0.0;
	}
	float len_out = 0.0215;
	float len_in = 0.0165;
	float th = 0.0030;
	float arch = 0.0030;
	float taper = 0.3;
	if (brow_style == 1) { arch = 0.0004; taper = 0.7; th = 0.0027; }
	else if (brow_style == 2) { arch = 0.0068; th = 0.0024; taper = 0.25; }
	else if (brow_style == 3) { th = 0.0048; arch = 0.0022; taper = 0.6; len_out = 0.0235; }
	else if (brow_style == 4) { th = 0.0013; arch = 0.0038; taper = 0.4; }
	else if (brow_style == 5) { len_in = 0.040; th = 0.0034; arch = 0.0014; taper = 0.7; }
	th *= brow_thick;
	float mid = (len_out - len_in) * 0.5;
	float half_len = (len_out + len_in) * 0.5;
	float t = clamp((q.x - mid) / half_len, -1.0, 1.0);
	// the arch peaks two thirds of the way out, then the tail drops and thins
	float yc = arch * (1.0 - pow(abs(t - 0.25) / 1.25, 2.0) * 1.6);
	float width = th * mix(1.0, taper, smoothstep(-0.1, 1.0, t)) * mix(0.72, 1.0, smoothstep(-1.0, -0.55, t));
	float dx = max(abs(q.x - mid) - (half_len - width), 0.0);
	float d = length(vec2(dx, q.y - yc)) - width;
	return smoothstep(aa + 0.0004, -aa - 0.0003, d);
}

void fragment() {
	// clothing cut-outs
	float ax = abs(rest.x);
	vec2 glove = rest.x > 0.0 ? hide_glove_l : hide_glove_r;
	if ((ax > hide_sleeve.x && ax < hide_sleeve.y) || (ax > glove.x && ax < glove.y)) {
		discard;
	}
	if (ax < 0.27) {
		vec2 boot = rest.x > 0.0 ? hide_boot_l : hide_boot_r;
		if ((rest.z > hide_z1.x && rest.z < hide_z1.y) || (rest.z > hide_z2.x && rest.z < hide_z2.y) || (rest.z > boot.x && rest.z < boot.y)) {
			discard;
		}
	}
	if (opacity < 0.999) {
		float dn = fract(52.9829189 * fract(dot(FRAGCOORD.xy, vec2(0.06711056, 0.00583715))));
		if (dn > opacity) {
			discard;
		}
	}
	vec3 detail = texture(skin_tex, UV).rgb * 2.0;
	vec4 mk = texture(mask_tex, UV);
	vec3 skin = skin_color * detail;
	float metal = 0.0;
	float rough = 0.62;
	vec3 emit = vec3(0.0);
	float body = 1.0 - mk.r;

	if (pattern != 0) {
		vec3 p = rest * 18.0 * pattern_scale;
		float m = 0.0;
		vec3 pc = pattern_color;
		if (pattern == 1) {             // stripes
			float f = sin(rest.z * 60.0 * pattern_scale + 5.0 * vnoise(p * 0.45) + abs(rest.x) * 14.0);
			m = smoothstep(0.25, 0.55, f);
		} else if (pattern == 2) {      // spots
			vec3 wv = worley(p * 0.9);
			m = smoothstep(0.36, 0.28, wv.x) * step(0.35, wv.z);
		} else if (pattern == 3) {      // scales
			vec3 wv = worley(p * 2.2);
			float edge = smoothstep(0.02, 0.12, wv.y - wv.x);
			skin *= mix(0.78, 1.12, wv.z);
			m = 1.0 - edge;
			rough = 0.42;
		} else if (pattern == 4) {      // cracked stone
			vec3 wv = worley(p * 0.8);
			float g = dot(skin, vec3(0.333));
			skin = mix(skin, vec3(g) * vec3(0.95, 0.97, 1.0), 0.85 * pattern_amount);
			m = 1.0 - smoothstep(0.0, 0.06, wv.y - wv.x);
			rough = 0.9;
		} else if (pattern == 5) {      // chequers
			vec3 c = floor(rest * 22.0 * pattern_scale);
			m = mod(c.x + c.y + c.z, 2.0);
		} else if (pattern == 6) {      // two halves
			m = step(0.0, rest.x * (rest.z > 0.98 ? 1.0 : -1.0));
		} else if (pattern == 7) {      // stars
			vec3 wv = worley(p * 1.6);
			m = smoothstep(0.10, 0.04, wv.x) * step(0.45, wv.z);
			emit += pc * m * 1.5 * body;
		} else if (pattern == 8) {      // molten cracks
			vec3 wv = worley(p * 0.7);
			float crack = 1.0 - smoothstep(0.0, 0.09, wv.y - wv.x);
			skin *= mix(1.0, 0.45, pattern_amount);
			m = crack;
			emit += pc * crack * 3.0 * body * pattern_amount;
		} else if (pattern == 9) {      // cast metal
			float g = dot(detail, vec3(0.333));
			skin = pc * (0.55 + 0.45 * g);
			metal = 1.0;
			rough = 0.28;
			m = 0.0;
		} else if (pattern == 10) {     // camouflage
			float n1 = vnoise(p * 0.35);
			float n2 = vnoise(p * 0.35 + 17.0);
			m = smoothstep(0.52, 0.56, n1);
			skin = mix(skin, skin * 0.55, smoothstep(0.55, 0.6, n2) * pattern_amount);
		} else if (pattern == 11) {     // spectral
			float fres = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), 2.0);
			skin = mix(skin, pc, 0.6 * pattern_amount);
			emit += pc * (0.35 + 1.6 * fres) * pattern_amount * body;
			m = 0.0;
		}
		skin = mix(skin, pc, m * pattern_amount);
	}

	// scalp and beard stubble: short hair as a tint with a little grain
	float grain = vnoise(rest * 520.0);
	float sc = mk.g * scalp_shade;
	float st = mk.b * stubble * 0.8;
	float hairy = clamp(max(sc, st), 0.0, 1.0);
	// thin growth shows as separate hairs, dense growth as a solid coat
	hairy *= mix(smoothstep(0.25, 0.75, grain), 1.0, hairy * hairy);
	skin = mix(skin, hair_color * (0.8 + 0.4 * grain), hairy);
	skin = mix(skin, mix(lip_color * detail, lip_color, 0.35), mk.a * lip_amount);
	vec3 col = mix(skin, underwear_color * (0.45 + 0.55 * detail.g), mk.r);

	// the face: eyes, brows and markings, drawn in the rest-pose face plane
	float eglow = 0.0;
	if (face > 0.01) {
		vec2 fp = rest.xz;
		float aa = max(fwidth(fp.x), fwidth(fp.y)) * 0.9 + 0.00012;
		if (marking != 0) {
			float mm = 0.0;
			if (marking == 1) {                 // a band across the eyes
				mm = 0.85 * smoothstep(0.0135, 0.0115, abs(fp.y - EYE.y - eye_height)) * smoothstep(0.084, 0.078, abs(fp.x));
			} else if (marking == 2) {          // cheek stripes
				float u = abs(fp.x) - 0.036 - (fp.y - 1.650) * 0.55;
				mm = 0.9 * smoothstep(0.003, 0.002, abs(mod(u + 0.004, 0.009) - 0.0045) - 0.0008) * smoothstep(0.015, 0.012, abs(u - 0.005))
					* smoothstep(0.013, 0.010, abs(fp.y - 1.652));
			} else if (marking == 3) {          // rosy cheeks
				mm = 0.55 * smoothstep(0.019, 0.006, length(vec2(abs(fp.x) - 0.050, fp.y - 1.647)));
			} else if (marking == 4) {          // freckles
				vec3 wv = worley(vec3(fp * 520.0, 1.0));
				mm = 0.6 * smoothstep(0.22, 0.12, wv.x) * step(0.4, wv.z) * smoothstep(0.075, 0.03, length(vec2(fp.x * 0.8, fp.y - 1.660)));
			} else if (marking == 5) {          // a painted nose and cheeks
				mm = smoothstep(0.0125, 0.0110, length(vec2(fp.x, fp.y - 1.6535)));
				mm = max(mm, 0.7 * smoothstep(0.014, 0.011, length(vec2(abs(fp.x) - 0.052, fp.y - 1.642))));
			} else if (marking == 6) {          // brow dot and chin lines
				mm = smoothstep(0.0042, 0.0032, length(vec2(fp.x, fp.y - 1.728)));
				mm = max(mm, smoothstep(0.0016, 0.0009, abs(abs(fp.x) - 0.006)) * smoothstep(0.017, 0.014, abs(fp.y - 1.592)));
				mm = max(mm, smoothstep(0.0016, 0.0009, abs(fp.x)) * smoothstep(0.013, 0.010, abs(fp.y - 1.588)));
			} else if (marking == 7) {          // a scar through the left eye
				float u = fp.x - 0.036 + (fp.y - 1.690) * 0.28;
				mm = 0.8 * smoothstep(0.0016, 0.0008, abs(u)) * smoothstep(0.030, 0.026, abs(fp.y - 1.690));
			}
			col = mix(col, marking_color, mm * face);
		}
		for (int i = 0; i < 2; i++) {
			float side = i == 0 ? 1.0 : -1.0;
			// brows ride up with bigger eyes
			vec2 bq = fp - vec2(side * (0.0365 + eye_spacing * 0.8), BROW_Z + brow_height + eye_height + (eye_size - 1.0) * 0.0068);
			bq.x *= side;
			float cb = cos(brow_tilt);
			float sb = sin(brow_tilt);
			bq = vec2(cb * bq.x + sb * bq.y, -sb * bq.x + cb * bq.y);
			float ba = draw_brow(bq / mix(1.0, eye_size, 0.45), aa / mix(1.0, eye_size, 0.45));
			col = mix(col, brow_color * (0.8 + 0.4 * vnoise(vec3(fp * 900.0, 3.0))), 0.92 * ba * face);
			vec2 q = fp - vec2(side * (EYE.x + eye_spacing), EYE.y + eye_height);
			q.x *= side;
			float ce = cos(eye_tilt);
			float se = sin(eye_tilt);
			q = vec2(ce * q.x + se * q.y, -se * q.x + ce * q.y);
			// the socket: a soft shadow that seats the eye in the face
			if (eye_style != 7 && eye_style != 9) {
				float socket = smoothstep(2.1, 0.9, length(q / (eye_size * vec2(0.0150, 0.0085))));
				col = mix(col, col * vec3(0.62, 0.56, 0.56), 0.42 * socket * face);
			}
			float em;
			vec4 e = draw_eye(q / eye_size, side, aa / eye_size, em);
			col = mix(col, e.rgb / max(e.a, 0.001), e.a * face);
			eglow = max(eglow, em * face);
			if (e.a * face > 0.5) {
				rough = 0.25;
				metal = 0.0;
			}
		}
	}
	vec3 albedo = lin(col);
	if (decay > 0.0) {
		float g = dot(albedo, vec3(0.299, 0.587, 0.114));
		albedo = mix(mix(albedo, vec3(g), decay * 0.6), vec3(0.021, 0.018, 0.014), decay * 0.55);
	}
	ALBEDO = albedo;
	ROUGHNESS = rough;
	METALLIC = metal;
	SPECULAR = 0.35;
	RIM = 0.05;
	RIM_TINT = 0.5;
	EMISSION = (lin(emit) + lin(eye_color) * eglow * (eye_style == 8 ? 3.0 : 2.0)) * (1.0 - decay);
}
