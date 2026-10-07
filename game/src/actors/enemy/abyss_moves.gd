class_name AbyssMoves
## bh-042: the three attack kinds of the Abyss bosses (docs/PLAN_bh-042.md, phase 2), started from
## EnemyTraitsX.start_special at the attack's release:
##   barrage     a bullet pattern (Barrage): radial rings, spirals, aimed fans, walls with a gap, orbits, homing orbs
##   curse_zone  Curse of Stillness (CurseZone): a sigil where nobody can cast a spell for several seconds
##   armor_rip   a hooked lash at one player: on a hit their armour is torn away (`armor_ripped`, -60% Defense, 8 s)
## Other machines in a multiplayer game draw copies (Net.share_skill_fx); hits stay with the boss's owner.

const KINDS := ["barrage", "curse_zone", "armor_rip"]
const RIP_COLOR := Color(0.85, 0.25, 0.2)
## Keys of a barrage attack that travel to other machines (the rest of the attack dictionary is not needed there).
const SHARED_KEYS := ["pattern", "count", "waves", "gap", "turn", "curve", "arms", "duration", "rate", "spin", "spread",
	"width", "spacing", "gap_time", "speed", "reach", "homing", "seek", "seed", "shot_radius"]

static func start(e: Enemy, a: Dictionary, act: TimedAction) -> void:
	var windup := maxf(0.05, act.release_t if act.release_t >= 0.0 else float(a.get("windup", 0.5)))
	match String(a.kind):
		"barrage":
			# a short glow at the boss while it gathers the volley
			FX.spawn(VFXLib.ring_wave(Color(a.get("color", Color(0.3, 0.95, 0.9)), 0.8), 3.0, windup, 0.4), e.global_position)
			act.on_release = func() -> void: barrage(e, a)
		"curse_zone":
			act.on_release = func() -> void: curse_zone(e, a)
		"armor_rip":
			if e.target:
				var d := (e.target.global_position - e.global_position).slide(Vector3.UP)
				var tl := VFXLib.telegraph("line", Vector2(minf(d.length() + 2.0, float(a.get("range", 16.0))), 0.5), windup, Color(RIP_COLOR, 0.6))
				FX.spawn(tl, e.global_position)
				tl.rotation.y = atan2(d.x, d.z)
				e.get_tree().create_timer(windup + 0.05, false).timeout.connect(tl.queue_free)
			act.on_release = func() -> void: armor_rip(e, a)

## A dim light that follows an Abyss boss so the hero can see what they are fighting in the dark (the floors have only
## a handful of torches). Colour from the boss's element; range from its size.
static func presence(e: Enemy) -> void:
	if e == null or e.get_node_or_null("AbyssPresence"):
		return
	var l := OmniLight3D.new()
	l.name = "AbyssPresence"
	var c := Elements.color(e.def.affinity) if e.def.affinity != Elements.PHYSICAL else Color(0.85, 0.8, 0.75)
	l.light_color = c.lerp(Color(1, 1, 1), 0.45)
	l.light_energy = 1.1
	l.omni_range = clampf(e.def.body_height * e.def.model_scale * 2.2, 6.0, 14.0)
	l.shadow_enabled = false
	l.position = Vector3(0, e.def.body_height * e.def.model_scale * 0.9, e.def.body_radius + 1.2)
	e.add_child(l)

## The Abyss moves a boss of level 90+ that was not made for the Abyss learns (Enemy._ready): a Curse of Stillness, an
## Armour Rip and one bullet pattern chosen by its id, in its own element, all from phase 2.
const OVERHAUL_PATTERNS := [
	{"pattern": "radial", "count": 24, "waves": 3, "gap": 0.55, "speed": 8.5},
	{"pattern": "spiral", "arms": 4, "duration": 3.0, "rate": 6.0, "spin": 110.0, "speed": 9.0},
	{"pattern": "fan", "count": 11, "spread": 90.0, "waves": 4, "gap": 0.35, "speed": 11.0},
	{"pattern": "orbit", "count": 20, "waves": 4, "gap": 0.5, "curve": 55.0, "speed": 7.5},
	{"pattern": "wall", "waves": 3, "gap_time": 0.95, "width": 20.0, "spacing": 1.1, "gap": 3.4, "speed": 9.0},
]

static func overhaul(def: EnemyDef) -> Array:
	var el := def.affinity
	var col := Elements.color(el) if el != Elements.PHYSICAL else Color(0.9, 0.85, 0.75)
	var pat: Dictionary = (OVERHAUL_PATTERNS[absi(hash(String(def.id))) % OVERHAUL_PATTERNS.size()] as Dictionary).duplicate()
	pat.merge({"id": &"abyss_barrage", "anim": &"cast_area", "range": 18.0, "mult": 0.42, "element": el, "knockback": 2.0, "poise": 6.0,
		"cooldown": 12.0, "kind": "barrage", "reach": 26.0, "windup": 0.7, "color": col, "phase": 2})
	return [pat,
		{"id": &"abyss_stillness", "anim": &"cast_area", "range": 22.0, "mult": 0.6, "element": el, "knockback": 2.0, "poise": 10.0,
			"cooldown": 18.0, "kind": "curse_zone", "radius": 6.5, "delay": 1.1, "duration": 6.0, "windup": 0.5, "phase": 2},
		{"id": &"abyss_rip", "anim": &"cast_heavy", "range": 16.0, "min_range": 2.0, "mult": 0.9, "element": el, "knockback": 5.0,
			"poise": 20.0, "cooldown": 15.0, "kind": "armor_rip", "speed": 34.0, "windup": 0.7, "phase": 2}]

# ---- barrage ----------------------------------------------------------------------------------------------------------

static func barrage(e: Enemy, a: Dictionary) -> Barrage:
	if not e.alive or not e.is_inside_tree():
		return null
	var shot := a.duplicate()
	if String(shot.get("pattern", "")) == "wall" and not shot.has("seed"):
		shot["seed"] = randi() % 100000
	shot["color"] = a.get("color", Elements.color(e._atk_element(a)) if e._atk_element(a) != Elements.PHYSICAL else Color(0.95, 0.85, 0.7))
	var aim := e.forward()
	if e.target and is_instance_valid(e.target):
		aim = (e.target.global_position - e.global_position).slide(Vector3.UP)
	var req := e._attack_request(a)
	req.graze = false                          # an aimed shot: evaded at full odds, never grazed
	var b := Barrage.fire(FX.world, shot, e.global_position, aim, e.target, req, e)
	var sts: Dictionary = a.get("on_hit_status", {})
	if b and not sts.is_empty():
		b.on_hit = func(t: Actor, res: DamageResult) -> void:
			if is_instance_valid(e):
				e.apply_hit_statuses(t, res, sts)
	Audio.play_at(&"arcane_surge", e.global_position, -2.0)
	if Net.is_active():
		var extra := {"c": shot.color}
		for k in SHARED_KEYS:
			if shot.has(k):
				extra[k] = shot[k]
		Net.share_skill_fx("barrage", e.global_position, aim, extra)
	return b

## Another machine's copy: drawn, never hitting.
static func remote_barrage(at: Vector3, dir: Vector3, extra: Dictionary) -> void:
	var a := {}
	for k in SHARED_KEYS:
		if extra.has(k):
			a[k] = extra[k]
	a["pattern"] = String(a.get("pattern", "radial"))
	if not (["radial", "orbit", "spiral", "cross", "fan", "wall", "homing"] as Array).has(a.pattern):
		return
	# bounds: a hostile peer cannot ask for a million shots
	for k in ["count", "waves", "arms"]:
		if a.has(k):
			a[k] = clampi(int(a[k]), 1, 72)
	for k in ["duration", "rate"]:
		if a.has(k):
			a[k] = clampf(float(a[k]), 0.1, 12.0)
	var c: Variant = extra.get("c", Color(0.3, 0.95, 0.9))
	a["color"] = c if c is Color else Color(0.3, 0.95, 0.9)
	Barrage.fire(FX.world, a, at, dir, null, null, null)

# ---- Curse of Stillness ---------------------------------------------------------------------------------------------

static func curse_zone(e: Enemy, a: Dictionary) -> CurseZone:
	if not e.alive or not e.is_inside_tree():
		return null
	var at := e.global_position
	if not a.get("self_centered", false) and e.target and is_instance_valid(e.target):
		at = e.target.global_position
	at = CombatQuery.ground_at(e.get_world_3d(), at)
	var r := float(a.get("radius", 6.0))
	var delay := float(a.get("delay", 1.1))
	var dur := float(a.get("duration", 6.0))
	var z := CurseZone.cast(FX.world, at, r, delay, dur, e._attack_request(a), e)
	if Net.is_active():
		Net.share_skill_fx("curse", at, Vector3.ZERO, {"r": r, "w": delay, "d": dur})
	return z

static func remote_curse(at: Vector3, extra: Dictionary) -> void:
	CurseZone.cast(FX.world, at, clampf(float(extra.get("r", 6.0)), 1.0, 14.0), clampf(float(extra.get("w", 1.0)), 0.1, 3.0),
		clampf(float(extra.get("d", 6.0)), 0.5, 12.0), null, null, BH.LAYER_PLAYER, true)

# ---- Armour Rip -------------------------------------------------------------------------------------------------------

static func armor_rip(e: Enemy, a: Dictionary) -> Projectile:
	var t := e.target
	if not e.alive or t == null or not is_instance_valid(t) or not t.alive:
		return null
	var req := e._attack_request(a)
	req.graze = false
	req.direct_status[&"armor_ripped"] = 600.0          # always takes on a hit; dodging or evading the lash is the answer
	var from := e.center() + e.forward() * (e.body_radius + 0.3)
	var dir := (t.center() - from)
	dir.y = 0.0
	var pr := Projectile.spawn(FX.world, from, dir, float(a.get("speed", 34.0)), req, e, BH.LAYER_PLAYER, Elements.DARK, "orb")
	pr.max_range = float(a.get("range", 16.0)) + 4.0
	pr.radius = 0.55
	pr.hit_sound = &"hit_armor"
	pr.on_hit = func(tt, res, _p) -> void:
		if tt is Actor and res and not res.evaded:
			ripped(tt as Actor)
	return pr

## What a hero sees when the rip lands (also called for a guest when their copy of the status arrives).
static func ripped(t: Actor) -> void:
	if t == null or not is_instance_valid(t):
		return
	FX.text_popup(t.center() + Vector3.UP * 1.0, "Armour Ripped!", RIP_COLOR, 1.3)
	FX.spawn(VFXLib.particles(Color(0.62, 0.62, 0.66, 0.95), 18, 0.9, true, 0.14, 6.0, 160.0, Vector3(0, -9.0, 0), 0.4, false), t.center())
	FX.spawn(VFXLib.light_flash(RIP_COLOR, 3.0, 4.0, 0.25), t.center())
	Audio.play_at(&"break_stone", t.global_position)
	Events.camera_shake.emit(0.3)
