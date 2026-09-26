class_name AnimDefaults
## Timing metadata used when an animation is missing from res://assets/characters/anim_meta.json (e.g. before the
## character builder has exported it, or for enemy-only clips). The sidecar always wins; these keep gameplay timing
## sane and consistent with the contract (light 0.45-0.75 s, finishers 0.7-0.95 s, heavies 0.9-1.4 s).

const LOOPS := [&"idle", &"idle_look", &"idle_adjust", &"idle_knight", &"idle_mage", &"idle_hurt", &"idle_1h", &"idle_shield",
	&"idle_2h", &"idle_spear", &"idle_dagger", &"idle_bow", &"idle_staff", &"idle_wand", &"idle_dual", &"idle_combat_hurt",
	&"walk", &"run", &"walk_back", &"strafe_l", &"strafe_r", &"run_combat", &"walk_hurt", &"run_hurt", &"bow_draw_hold",
	&"charge_hold", &"block_loop", &"cast_channel", &"whirlwind", &"launch", &"boss_charge"]

static func meta(n: StringName) -> Dictionary:
	var s := String(n)
	match s:
		"walk": return {"length": 1.0, "loop": true, "ground_speed": 1.6, "footsteps": [0.0, 0.5]}
		"run": return {"length": 0.66, "loop": true, "ground_speed": 5.0, "footsteps": [0.0, 0.33]}
		"run_combat": return {"length": 0.66, "loop": true, "ground_speed": 4.8, "footsteps": [0.0, 0.33]}
		"walk_back": return {"length": 1.0, "loop": true, "ground_speed": 1.8, "footsteps": [0.0, 0.5]}
		"strafe_l", "strafe_r": return {"length": 0.8, "loop": true, "ground_speed": 3.2, "footsteps": [0.0, 0.4]}
		"walk_hurt": return {"length": 1.2, "loop": true, "ground_speed": 1.4, "footsteps": [0.0, 0.6]}
		"run_hurt": return {"length": 0.8, "loop": true, "ground_speed": 4.2, "footsteps": [0.0, 0.4]}
		"dodge_roll": return {"length": 0.62, "loop": false, "iframes": [0.04, 0.4], "travel": 4.2, "cancel_after": 0.46, "footsteps": [0.5]}
		"dodge_step": return {"length": 0.42, "loop": false, "iframes": [0.02, 0.24], "travel": 2.4, "cancel_after": 0.3}
		"run_start": return {"length": 0.3, "loop": false}
		"run_stop": return {"length": 0.35, "loop": false}
		"turn_l", "turn_r": return {"length": 0.5, "loop": false}
		"block_impact": return {"length": 0.35, "loop": false, "cancel_after": 0.2}
		"parry": return {"length": 0.45, "loop": false, "cancel_after": 0.25}
		"shield_bash": return {"length": 0.7, "loop": false, "hits": [[0.2, 0.34]], "cancel_after": 0.5}
		"charge_release": return {"length": 0.8, "loop": false, "hits": [[0.14, 0.28]], "cancel_after": 0.55}
		"special_attack": return {"length": 1.0, "loop": false, "hits": [[0.25, 0.38], [0.55, 0.68]], "cancel_after": 0.8}
		"bow_1", "bow_2": return {"length": 0.55, "loop": false, "release": 0.24, "cancel_after": 0.38, "combo_window": [0.3, 0.7]}
		"bow_release": return {"length": 0.5, "loop": false, "release": 0.08, "cancel_after": 0.3}
		"cast_quick": return {"length": 0.55, "loop": false, "release": 0.26, "cancel_after": 0.38}
		"cast_heavy": return {"length": 0.95, "loop": false, "release": 0.52, "cancel_after": 0.7}
		"cast_area": return {"length": 0.85, "loop": false, "release": 0.42, "cancel_after": 0.62}
		"cast_weapon": return {"length": 0.8, "loop": false, "release": 0.4, "cancel_after": 0.6}
		"cast_ultimate": return {"length": 1.3, "loop": false, "release": 0.8, "cancel_after": 1.05}
		"blink": return {"length": 0.4, "loop": false, "release": 0.12, "cancel_after": 0.25}
		"war_cry": return {"length": 1.0, "loop": false, "release": 0.4, "cancel_after": 0.75}
		"leap_slam": return {"length": 1.15, "loop": false, "hits": [[0.72, 0.84]], "cancel_after": 0.95}
		"hit_light", "hit_front", "hit_back", "hit_left", "hit_right", "hit": return {"length": 0.38, "loop": false}
		"hit_heavy": return {"length": 0.55, "loop": false}
		"stagger_small", "stagger": return {"length": 0.7, "loop": false}
		"stagger_heavy": return {"length": 1.1, "loop": false}
		"knockback": return {"length": 1.15, "loop": false}
		"wall_impact": return {"length": 0.9, "loop": false}
		"knockdown": return {"length": 0.9, "loop": false}
		"getup": return {"length": 0.85, "loop": false}
		"death": return {"length": 1.6, "loop": false}
		"revive": return {"length": 1.4, "loop": false}
		"interact_pickup": return {"length": 0.7, "loop": false, "release": 0.35}
		"interact_chest": return {"length": 1.0, "loop": false, "release": 0.5}
		"interact_talk": return {"length": 1.4, "loop": false}
		"interact_teleport": return {"length": 1.0, "loop": false}
		"alert": return {"length": 0.8, "loop": false}
		"taunt": return {"length": 1.4, "loop": false}
		"boss_slam": return {"length": 1.6, "loop": false, "hits": [[0.95, 1.08]], "cancel_after": 1.35}
		"boss_sweep": return {"length": 1.4, "loop": false, "hits": [[0.8, 1.0]], "cancel_after": 1.15}
		"boss_roar": return {"length": 1.8, "loop": false, "release": 0.7}
		"boss_summon": return {"length": 1.6, "loop": false, "release": 0.9}
	if LOOPS.has(n):
		return {"length": 2.0 if s.begins_with("idle") else 1.0, "loop": true}
	# Weapon chains: <weapon>_<step>
	var parts := s.split("_")
	if parts.size() == 2 and parts[1].is_valid_int():
		var step := int(parts[1])
		var base_len := {"sword": 0.55, "gs": 0.8, "axe": 0.62, "spear": 0.6, "dagger": 0.42, "dual": 0.5, "staff": 0.6, "wand": 0.45}.get(parts[0], 0.6)
		var len_: float = base_len * (1.4 if step == 4 else 1.0)
		var hit_a: float = len_ * (0.42 if step == 4 else 0.36)
		var m := {"length": len_, "loop": false, "hits": [[hit_a, hit_a + len_ * 0.16]], "cancel_after": len_ * 0.7,
			"combo_window": [len_ * 0.5, len_ * 1.35]}
		if parts[0] in ["staff", "wand"]:
			m["release"] = hit_a
		return m
	if s.ends_with("_heavy"):
		var hl := {"sword_heavy": 0.95, "gs_heavy": 1.3, "axe_heavy": 1.1, "spear_heavy": 1.0, "dagger_heavy": 0.8, "dual_heavy": 0.95,
			"staff_heavy": 1.0, "wand_heavy": 0.8}.get(s, 1.0)
		var hm := {"length": hl, "loop": false, "hits": [[hl * 0.48, hl * 0.62]], "cancel_after": hl * 0.8}
		if s.begins_with("staff") or s.begins_with("wand"):
			hm["release"] = hl * 0.48
		return hm
	return {"length": 0.7, "loop": false, "hits": [[0.3, 0.4]], "cancel_after": 0.5, "release": 0.3}
