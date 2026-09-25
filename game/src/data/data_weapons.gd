class_name DataWeapons
## The eight weapon types and their stances.

static func _w(id: StringName, name: String, d: Dictionary) -> WeaponTypeDef:
	var w := WeaponTypeDef.new()
	w.id = id
	w.display_name = name
	for k in d:
		w.set(k, d[k])
	w.model = "res://assets/weapons/%s.glb" % id
	w.icon = "res://assets/ui/icons/items/%s.svg" % id
	return w

static func build() -> Array:
	return [
		_w(&"sword", "Sword", {"dual_wieldable": true, "attacks_per_second": 1.45, "reach": 2.4, "arc_degrees": 120.0,
			"crit_chance": 0.06, "impact": 1.0, "knockback": 3.5, "poise_damage": 12.0, "heavy_multiplier": 1.9, "heavy_knockback": 9.0,
			"scaling": {&"str": 0.5, &"dex": 0.5}, "idle_anim": &"idle_combat",
			"light_anims": [&"sword_light_1", &"sword_light_2", &"sword_light_3"], "heavy_anim": &"sword_heavy",
			"dual_light_anims": [&"dual_light_1", &"dual_light_2", &"dual_light_3"], "dual_heavy_anim": &"dual_heavy",
			"swing_sound": &"swing_light", "hit_sound": &"hit_flesh"}),
		_w(&"greatsword", "Greatsword", {"two_handed": true, "attacks_per_second": 0.95, "reach": 3.0, "arc_degrees": 160.0,
			"crit_chance": 0.05, "impact": 1.45, "knockback": 6.0, "poise_damage": 22.0, "heavy_multiplier": 2.2, "heavy_knockback": 14.0,
			"charge_max": 1.2, "charge_bonus": 0.8, "scaling": {&"str": 1.0}, "idle_anim": &"idle_2h",
			"light_anims": [&"gs_light_1", &"gs_light_2"], "heavy_anim": &"gs_heavy",
			"swing_sound": &"swing_heavy", "hit_sound": &"hit_heavy"}),
		_w(&"axe", "Axe", {"dual_wieldable": true, "attacks_per_second": 1.25, "reach": 2.3, "arc_degrees": 110.0,
			"crit_chance": 0.05, "impact": 1.25, "knockback": 4.5, "poise_damage": 16.0, "heavy_multiplier": 2.0, "heavy_knockback": 11.0,
			"scaling": {&"str": 0.8, &"agi": 0.2}, "idle_anim": &"idle_combat",
			"light_anims": [&"axe_light_1", &"axe_light_2"], "heavy_anim": &"axe_heavy",
			"dual_light_anims": [&"dual_light_1", &"dual_light_2", &"dual_light_3"], "dual_heavy_anim": &"dual_heavy",
			"swing_sound": &"swing_heavy", "hit_sound": &"hit_flesh"}),
		_w(&"spear", "Spear", {"two_handed": true, "attacks_per_second": 1.2, "reach": 3.4, "arc_degrees": 40.0,
			"crit_chance": 0.07, "impact": 1.1, "knockback": 4.0, "poise_damage": 14.0, "heavy_multiplier": 1.8, "heavy_knockback": 10.0,
			"charge_max": 0.9, "charge_bonus": 0.6, "scaling": {&"str": 0.5, &"agi": 0.3, &"dex": 0.2}, "idle_anim": &"idle_2h",
			"light_anims": [&"spear_light_1", &"spear_light_2"], "heavy_anim": &"spear_heavy",
			"swing_sound": &"swing_light", "hit_sound": &"hit_flesh"}),
		_w(&"dagger", "Dagger", {"dual_wieldable": true, "attacks_per_second": 2.0, "reach": 1.9, "arc_degrees": 80.0,
			"crit_chance": 0.10, "impact": 0.6, "knockback": 1.5, "poise_damage": 6.0, "heavy_multiplier": 1.7, "heavy_knockback": 5.0,
			"scaling": {&"agi": 0.5, &"dex": 0.5}, "idle_anim": &"idle_combat",
			"light_anims": [&"dagger_light_1", &"dagger_light_2", &"dagger_light_3"], "heavy_anim": &"dagger_heavy",
			"dual_light_anims": [&"dual_light_1", &"dual_light_2", &"dual_light_3"], "dual_heavy_anim": &"dual_heavy",
			"swing_sound": &"swing_dagger", "hit_sound": &"hit_flesh"}),
		_w(&"bow", "Bow", {"two_handed": true, "ranged": true, "projectile_speed": 34.0, "attacks_per_second": 1.1, "reach": 22.0,
			"arc_degrees": 0.0, "crit_chance": 0.08, "impact": 0.8, "knockback": 2.5, "poise_damage": 8.0, "heavy_multiplier": 2.4,
			"heavy_knockback": 9.0, "charge_max": 1.0, "charge_bonus": 1.0, "scaling": {&"dex": 0.8, &"agi": 0.2}, "idle_anim": &"idle_bow",
			"light_anims": [&"bow_release"], "heavy_anim": &"bow_release",
			"swing_sound": &"bow_release", "hit_sound": &"arrow_impact"}),
		_w(&"staff", "Staff", {"two_handed": true, "ranged": true, "projectile_speed": 20.0, "attacks_per_second": 1.0, "reach": 18.0,
			"arc_degrees": 0.0, "crit_chance": 0.05, "impact": 1.1, "knockback": 3.5, "poise_damage": 10.0, "heavy_multiplier": 2.0,
			"heavy_knockback": 8.0, "charge_max": 1.0, "charge_bonus": 0.8, "scaling": {&"int": 0.7, &"wis": 0.3}, "idle_anim": &"idle_staff",
			"light_anims": [&"staff_light_1", &"staff_light_2"], "heavy_anim": &"staff_heavy",
			"swing_sound": &"swing_blunt", "hit_sound": &"hit_heavy"}),
		_w(&"wand", "Wand", {"dual_wieldable": true, "ranged": true, "projectile_speed": 30.0, "attacks_per_second": 1.6, "reach": 18.0,
			"arc_degrees": 0.0, "crit_chance": 0.07, "impact": 0.6, "knockback": 1.5, "poise_damage": 5.0, "heavy_multiplier": 1.6,
			"heavy_knockback": 4.0, "scaling": {&"int": 0.6, &"dex": 0.4}, "idle_anim": &"idle_combat",
			"light_anims": [&"wand_light_1", &"wand_light_2"], "heavy_anim": &"cast_short",
			"dual_light_anims": [&"wand_light_1", &"wand_light_2"], "dual_heavy_anim": &"cast_long",
			"swing_sound": &"cast_lightning", "hit_sound": &"lightning_zap"}),
	]
