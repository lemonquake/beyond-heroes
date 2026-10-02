class_name DataBossGuides
## bh-033: short, plain boss guidance. `phases`: one line per phase shown under the boss bar (what this phase asks of
## you); `wipe`: what happened and what to try next, on the death screen while that boss is alive. Mechanics only — no
## story spoilers beyond the boss you are already fighting.
const GUIDES := {
	&"boss_warden": {
		"phases": {1: "Stand before a pillar and sidestep his charge: he breaks it and is stunned.",
			2: "Dark pools and the risen: keep moving and keep a pillar between you and him.",
			3: "His charge now leaves burning ground. When the ring flares, stay close to him or far outside it."},
		"wipe": "His charge breaks the pillar it hits and stuns him. Stand before a pillar, sidestep the red line, then strike. With no pillars left, a wall still stops him.",
	},
	&"rot_mother": {
		"phases": {1: "Rot spreads from her buds. Break a growing bud before it blooms to keep the ground clear.",
			2: "She calls more buds and the ring returns: break the nearest bud, then step out of the ring.",
			3: "Few buds, little ground: clear one, fight from the space it leaves."},
		"wipe": "Her buds rot the ground inside their circles when they bloom. Break each bud while it grows, and fight from clean ground.",
	},
}

static func phase_line(boss_id: StringName, phase: int) -> String:
	return String((GUIDES.get(boss_id, {}) as Dictionary).get("phases", {}).get(phase, ""))

static func wipe_line(boss_id: StringName) -> String:
	return String((GUIDES.get(boss_id, {}) as Dictionary).get("wipe", ""))
