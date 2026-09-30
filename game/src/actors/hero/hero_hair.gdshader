shader_type spatial;
render_mode cull_disabled, diffuse_burley, specular_schlick_ggx;
// bh-023: the hero's hair and beard. Vertex colour R = how freely a vertex sways (0 at the roots), G = a per-lock
// shade so neighbouring locks differ a little (tools/blender/hero/hero_hair.py).

uniform vec3 hair_color = vec3(0.17, 0.11, 0.08);      // sRGB
uniform float sway = 1.0;
uniform float opacity = 1.0;
uniform float decay = 0.0;

varying float shade;

void vertex() {
	float w = COLOR.r * sway;
	float t = TIME * 1.7 + VERTEX.y * 5.0;
	VERTEX.x += sin(t) * 0.012 * w;
	VERTEX.z += cos(t * 0.8 + 1.3) * 0.010 * w;
	shade = COLOR.g;
}

void fragment() {
	if (opacity < 0.999) {
		float dn = fract(52.9829189 * fract(dot(FRAGCOORD.xy, vec2(0.06711056, 0.00583715))));
		if (dn > opacity) {
			discard;
		}
	}
	if (!FRONT_FACING) {
		NORMAL = -NORMAL;
	}
	vec3 c = pow(hair_color * mix(0.74, 1.12, shade), vec3(2.2));
	if (decay > 0.0) {
		float g = dot(c, vec3(0.299, 0.587, 0.114));
		c = mix(mix(c, vec3(g), decay * 0.6), vec3(0.021, 0.018, 0.014), decay * 0.55);
	}
	ALBEDO = c;
	ROUGHNESS = 0.52;
	SPECULAR = 0.4;
	RIM = 0.2;
	RIM_TINT = 0.7;
}
