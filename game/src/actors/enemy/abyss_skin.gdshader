// bh-042: skins for the Abyss bosses whose downloaded models came without their texture images. Worked out in UV
// space (skinning moves vertices before vertex(), so object space would swim): a cellular stone surface with glowing
// seams between the cells. The lava golem: dark basalt plates, molten seams that pulse. With `albedo_tex` set the
// model's own texture is kept and only darkened, the seams added on top.
shader_type spatial;
render_mode cull_back, diffuse_burley, specular_schlick_ggx;

uniform vec3 stone_color : source_color = vec3(0.07, 0.06, 0.055);
uniform vec3 stone_light : source_color = vec3(0.16, 0.13, 0.11);
uniform vec3 seam_color : source_color = vec3(1.0, 0.36, 0.06);
uniform float seam_energy = 5.0;
uniform float cells = 9.0;
uniform float seam_width = 0.07;
uniform float pulse = 0.35;
uniform float roughness = 0.9;
uniform bool use_albedo = false;
uniform sampler2D albedo_tex : source_color, filter_linear_mipmap, repeat_enable;

vec2 hash2(vec2 p) {
	p = vec2(dot(p, vec2(127.1, 311.7)), dot(p, vec2(269.5, 183.3)));
	return fract(sin(p) * 43758.5453);
}

// distance to the nearest cell border (F2 - F1) and the cell's own value
vec2 cellular(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	float d1 = 8.0;
	float d2 = 8.0;
	float id = 0.0;
	for (int y = -1; y <= 1; y++) {
		for (int x = -1; x <= 1; x++) {
			vec2 g = vec2(float(x), float(y));
			vec2 o = hash2(i + g);
			float d = length(g + o - f);
			if (d < d1) {
				d2 = d1;
				d1 = d;
				id = hash2(i + g + 7.3).x;
			} else if (d < d2) {
				d2 = d;
			}
		}
	}
	return vec2(d2 - d1, id);
}

void fragment() {
	vec2 c = cellular(UV * cells);
	vec2 fine = cellular(UV * cells * 3.7 + 11.0);
	float seam = 1.0 - smoothstep(0.0, seam_width, c.x);
	float fine_seam = (1.0 - smoothstep(0.0, seam_width * 0.6, fine.x)) * 0.35;
	vec3 stone = mix(stone_color, stone_light, c.y * 0.7 + fine.y * 0.3);
	if (use_albedo) {
		stone = texture(albedo_tex, UV).rgb * 0.55;
	}
	float glow = clamp(seam + fine_seam * seam, 0.0, 1.0);
	float beat = 1.0 + pulse * sin(TIME * 2.2 + c.y * 6.2831);
	ALBEDO = mix(stone, seam_color * 0.4, glow);
	EMISSION = seam_color * seam_energy * glow * beat;
	ROUGHNESS = mix(roughness, 0.4, glow);
	METALLIC = 0.0;
}
