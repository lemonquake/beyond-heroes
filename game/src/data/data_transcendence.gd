class_name DataTranscendence
## Class Transcendence: the advancement registry. Four starting families, one first transcendence each (level 60) and
## two mutually exclusive master classes each (level 120). Sixteen identities in all.
##
## A hero's saved `class` stays its starting family (Knight, Hunter = `ranger`, Mage, Shadowblade); the advancement is a
## separate path (HeroData.transcendence_path, ClassTranscendence). Every identity below grants three active skills
## (DataTranscendenceSkills) and three talents (TALENTS) at rank 1, once, and has three gear bases
## (DataTranscendenceGear).
##
## Themes: `primary` is the class colour (labels, card frames, skill page tint, armour); `accent` is the trim colour
## (the second line of a card, armour trim). Base families keep their familiar colours.

const FIRST_LEVEL := 60
const MASTER_LEVEL := 120

## The starting families. `name` is what players read (the Ranger family is shown as Hunter; its id stays `ranger`).
const FAMILIES := {
	&"knight": {"name": "Knight", "primary": Color("#C83A33"), "accent": Color("#E2C48A")},
	&"ranger": {"name": "Hunter", "primary": Color("#4F8C47"), "accent": Color("#D8C48E")},
	&"mage": {"name": "Mage", "primary": Color("#5242C7"), "accent": Color("#C9B8F2")},
	&"shadowblade": {"name": "Shadowblade", "primary": Color("#73339A"), "accent": Color("#C0A6D8")},
}

## The twelve advanced identities. stage 1 = first transcendence (parent = family), stage 2 = master (parent = stage 1).
const CLASSES := {
	# ---- Knight -----------------------------------------------------------------------------------------------------
	&"royal_guard": {"name": "Royal Guard", "family": &"knight", "stage": 1, "parent": &"knight",
		"primary": Color("#527ED6"), "accent": Color("#D8B46A"),
		"role": "Defensive melee and protection",
		"desc": "Holds the line with a shield. Charges through enemies, draws them away from allies, and plants a standard that steadies everyone near it.",
		"limit": "Most of its strength is in defense; Bastion Rush needs a shield.",
		"skills": [&"rg_bastion_rush", &"rg_sovereigns_challenge", &"rg_bulwark_standard"],
		"talents": [&"rg_crown_discipline", &"rg_unbroken_line", &"rg_guardians_resolve"],
		"armor_look": "Royal-blue plate with gold trim, great pauldrons, a crown on the breast, a blue tabard and a short blue cape.",
			"gear": [&"tc_crownward_longsword", &"tc_royal_guard_cuirass", &"tc_oathkeeper_seal"]},
	&"dark_general": {"name": "Dark General", "family": &"knight", "stage": 2, "parent": &"royal_guard",
		"primary": Color("#343444"), "accent": Color("#C9566C"),
		"role": "Aggressive armored melee with Dark damage",
		"desc": "Turns the Knight's armor into a weapon. Wide Dark sweeps weaken enemies, a heavy advance breaks lines, and a zone of Dark pulses spends Valor for a stronger first strike.",
		"limit": "Highest Knight damage; protects allies far less than the Grand Paladin.",
		"skills": [&"dg_dread_cleave", &"dg_warbound_advance", &"dg_black_dominion"],
		"talents": [&"dg_dreadsteel", &"dg_relentless_march", &"dg_iron_tyrant"],
		"armor_look": "Blackened plate with crimson trim, spiked pauldrons, a tall gorget, crimson tassets and a long torn crimson cape.",
			"gear": [&"tc_dreadmarshal_greatsword", &"tc_black_dominion_plate", &"tc_dread_command_signet"]},
	&"grand_paladin": {"name": "Grand Paladin", "family": &"knight", "stage": 2, "parent": &"royal_guard",
		"primary": Color("#E8E0C6"), "accent": Color("#E5BD64"),
		"role": "Light melee and team protection",
		"desc": "Fights with Light and protects the party. A heavy Light strike spends Valor, sanctified ground hurts enemies and heals allies, and an oath cleanses and shields everyone nearby.",
		"limit": "Strong support and defense; less damage than the Dark General.",
		"skills": [&"gp_dawn_verdict", &"gp_sanctified_ground", &"gp_oath_of_mercy"],
		"talents": [&"gp_radiant_steel", &"gp_merciful_oath", &"gp_hallowed_armor"],
		"armor_look": "White plate with gold trim, sun pauldrons, a sun on the breast, a white tabard edged in gold and a long gold cape with a white sun.",
			"gear": [&"tc_dawnstar_longsword", &"tc_sanctified_plate", &"tc_sunward_reliquary"]},
	# ---- Hunter (ranger) --------------------------------------------------------------------------------------------
	&"tracker": {"name": "Tracker", "family": &"ranger", "stage": 1, "parent": &"ranger",
		"primary": Color("#688C53"), "accent": Color("#D5B86A"),
		"role": "Marks, pursuit and traps",
		"desc": "Marks one quarry for its own shots, lays a line of snares, and looses a fan of arrows that strikes each enemy once.",
		"limit": "Rewards focusing one target; its bonuses apply only to its own ranged hits.",
		"skills": [&"tr_quarry_mark", &"tr_snareline", &"tr_trail_volley"],
		"talents": [&"tr_keen_trail", &"tr_patient_aim", &"tr_fieldcraft"],
		"armor_look": "A moss-green riveted jerkin, a bandolier of pouches, a fur-edged hood worn down and a short green cape.",
			"gear": [&"tc_trailkeeper_bow", &"tc_trackers_leathers", &"tc_quarry_compass"]},
	&"wildwarden": {"name": "Wildwarden", "family": &"ranger", "stage": 2, "parent": &"tracker",
		"primary": Color("#39876A"), "accent": Color("#A3CF9C"),
		"role": "Terrain control and nature-themed defense",
		"desc": "Shapes the ground. Briar volleys leave slowing patches, a living thicket roots and wears down enemies, and a refuge shields allies against slows.",
		"limit": "Controls the field and protects allies; lower single-target damage than the Starstrider.",
		"skills": [&"ww_briar_volley", &"ww_living_thicket", &"ww_wardens_refuge"],
		"talents": [&"ww_thorncraft", &"ww_rootbound_guard", &"ww_verdant_reserve"],
		"armor_look": "A deep-green jerkin and skirt, bark pauldrons with leaves, a collar of leaves and a split green cape.",
			"gear": [&"tc_briarheart_bow", &"tc_livingwood_leathers", &"tc_wildroot_pendant"]},
	&"starstrider": {"name": "Starstrider", "family": &"ranger", "stage": 2, "parent": &"tracker",
		"primary": Color("#495DB7"), "accent": Color("#A5DCEC"),
		"role": "Long-range precision and repositioning",
		"desc": "Strikes from far away. A piercing star shot spends Focus, an evasive vault empowers the next shot, and a rain of starlit arrows covers a chosen area.",
		"limit": "Highest Hunter damage at range; little control or protection for allies.",
		"skills": [&"ss_astral_pierce", &"ss_comet_step", &"ss_constellation_rain"],
		"talents": [&"ss_celestial_sight", &"ss_comet_rhythm", &"ss_steady_constellation"],
		"armor_look": "A midnight-blue long coat scattered with silver stars, a star on the breast and a high collar.",
			"gear": [&"tc_starfall_crossbow", &"tc_constellation_leathers", &"tc_comet_lens"]},
	# ---- Mage -------------------------------------------------------------------------------------------------------
	&"arcanist": {"name": "Arcanist", "family": &"mage", "stage": 1, "parent": &"mage",
		"primary": Color("#946BD3"), "accent": Color("#C7D0E6"),
		"role": "Controlled casting, Mana use and spell geometry",
		"desc": "Casts with precision. A piercing lance of Light and Dark, a runic circle that strengthens spells cast inside it, and a ward paid for with Mana.",
		"limit": "Its circle rewards standing still; its ward costs a large amount of Mana.",
		"skills": [&"ar_aether_lance", &"ar_runic_circle", &"ar_mana_ward"],
		"talents": [&"ar_runic_efficiency", &"ar_charge_discipline", &"ar_aether_precision"],
		"armor_look": "A violet robe with silver trim, a rune-stitched stole and an amethyst clasp.",
			"gear": [&"tc_runebound_staff", &"tc_arcanist_vestments", &"tc_runic_focus"]},
	&"archmage": {"name": "Archmage", "family": &"mage", "stage": 2, "parent": &"arcanist",
		"primary": Color("#497EC9"), "accent": Color("#E0E7F3"),
		"role": "Elemental combinations and broad areas",
		"desc": "Combines the elements. A tempest cycles Fire, Water and Lightning, a convergence spends Arcane Charge on one great blast, and Spellweave repeats the next spell.",
		"limit": "Wide elemental damage; less control and less Dark damage than the Void Sovereign.",
		"skills": [&"am_prismatic_tempest", &"am_grand_convergence", &"am_spellweave"],
		"talents": [&"am_elemental_concord", &"am_master_channeling", &"am_prismatic_shelter"],
		"armor_look": "A sapphire robe, a white mantle set with three gems and a long sapphire cape.",
			"gear": [&"tc_prismatic_staff", &"tc_archmage_robes", &"tc_convergence_prism"]},
	&"void_sovereign": {"name": "Void Sovereign", "family": &"mage", "stage": 2, "parent": &"arcanist",
		"primary": Color("#5446A6"), "accent": Color("#B292EA"),
		"role": "Dark gravity control and deliberate burst",
		"desc": "Bends space. A gravity well pulls enemies together, a Dark lance pierces armor and resistance, and a telegraphed rift spends Arcane Charge on a heavy explosion.",
		"limit": "Strong control and burst; slow to set up and almost only Dark damage.",
		"skills": [&"vs_event_horizon", &"vs_null_lance", &"vs_rift_collapse"],
		"talents": [&"vs_void_geometry", &"vs_entropy", &"vs_sovereigns_reserve"],
		"armor_look": "An indigo robe, a tall flared collar, a dark mantle and a torn indigo cape.",
			"gear": [&"tc_eventide_staff", &"tc_riftwoven_robes", &"tc_horizon_core"]},
	# ---- Shadowblade ------------------------------------------------------------------------------------------------
	&"nightstalker": {"name": "Nightstalker", "family": &"shadowblade", "stage": 1, "parent": &"shadowblade",
		"primary": Color("#8655A8"), "accent": Color("#ADB3C6"),
		"role": "Mobile melee, ambushes and Combo control",
		"desc": "Moves through shadow. A lunge that builds Combo, a veil that hides and protects, and an execution finisher that hits marked enemies harder.",
		"limit": "Needs Combo and good positioning; little area damage.",
		"skills": [&"ns_umbral_lunge", &"ns_gloom_veil", &"ns_marked_execution"],
		"talents": [&"ns_ambush_training", &"ns_silent_footwork", &"ns_patient_blade"],
		"armor_look": "A plum leather harness with crossed straps, a cowl, one pauldron and a trailing scarf.",
			"gear": [&"tc_gloamfang_dagger", &"tc_nightstalker_leathers", &"tc_silent_trail_charm"]},
	&"phantom_reaper": {"name": "Phantom Reaper", "family": &"shadowblade", "stage": 2, "parent": &"nightstalker",
		"primary": Color("#7A77C9"), "accent": Color("#BEDDEB"),
		"role": "Precise repositioning and finishing burst",
		"desc": "Strikes and vanishes. Crosses behind enemies, reaps a wide arc with Combo, and leaves afterimages that strike again.",
		"limit": "High burst and evasion; no healing and fragile when caught.",
		"skills": [&"pr_phantom_crossing", &"pr_reapers_arc", &"pr_afterimage_flurry"],
		"talents": [&"pr_ghoststep", &"pr_reaping_edge", &"pr_untouchable_rhythm"],
		"armor_look": "A grey-violet mantle over a dark harness, a crescent clasp and a long pale torn cape.",
			"gear": [&"tc_wraithedge_dagger", &"tc_afterimage_mantle", &"tc_reapers_glass"]},
	&"blood_sovereign": {"name": "Blood Sovereign", "family": &"shadowblade", "stage": 2, "parent": &"nightstalker",
		"primary": Color("#AD4B64"), "accent": Color("#DF9C9C"),
		"role": "Bleeding melee and bounded self-healing",
		"desc": "Lives on what it takes. Rending cuts cause Bleeding, a pact trades Health for damage and lifesteal, and an eclipse finisher heals from the damage it deals.",
		"limit": "Durable in long fights; lower burst than the Phantom Reaper.",
		"skills": [&"bs_crimson_rend", &"bs_sanguine_pact", &"bs_blood_eclipse"],
		"talents": [&"bs_hemomancy", &"bs_sovereigns_hunger", &"bs_crimson_endurance"],
		"armor_look": "A garnet long coat with tails, a crimson sash, a high collar and a blood-moon clasp.",
			"gear": [&"tc_crimson_oath_dagger", &"tc_sanguine_leathers", &"tc_bloodmoon_signet"]},
}

## Signature traits: one always-on mechanic per advanced identity that makes it recognisable in a fight, each with
## its own visible mark that other players see too (ClassSignature). A master keeps its first transcendence's trait, so
## a master hero has two. They are earned with the class (never ranked, never points) and run on the hero's machine.
## `mark` names what the trait looks like; `nums` are the values the text and the runtime share.
const SIGNATURES := {
	&"royal_guard": {"name": "Royal Aegis", "desc": "Each block adds a crest (up to {max}; they fade {fade} s after your last block). With {max} crests your next weapon attack is a Royal Retort: it deals {bonus}% more damage and sends a shield wave {reach} m ahead that deals {wave}% weapon damage and staggers.",
		"nums": {"max": 3, "fade": 10.0, "bonus": 30.0, "reach": 4.0, "wave": 80.0}},
	&"dark_general": {"name": "Conqueror's Dread", "desc": "Defeating an enemy, or spending Valor on a skill, adds Dread (up to {max}, {dur} s): each Dread gives {dmg}% more damage and {dr}% less damage taken.",
		"nums": {"max": 5, "dur": 10.0, "dmg": 2.0, "dr": 2.0}},
	&"grand_paladin": {"name": "Dawnbringer", "desc": "Every {hits}th weapon hit breaks the dawn around you ({radius} m): enemies take {pct}% weapon damage as Light, and you and your allies inside recover {heal}% of Maximum HP. At most once every {icd} s.",
		"nums": {"hits": 5, "radius": 4.0, "pct": 60.0, "heal": 2.0, "icd": 3.0}},
	&"tracker": {"name": "Hunter's Opening", "desc": "Your first arrow, bolt or javelin to strike an enemy at full health is a critical hit and deals {bonus}% more damage.",
		"nums": {"bonus": 25.0}},
	&"wildwarden": {"name": "Rooted Stance", "desc": "Stand still for {delay} s in a fight and roots hold you: +{def}% Defense, +{kb}% Knockback Resistance, and your arrows and bolts Slow what they hit for {slow} s. Moving breaks the roots.",
		"nums": {"delay": 1.0, "def": 10.0, "kb": 30.0, "slow": 2.0}},
	&"starstrider": {"name": "Star Chart", "desc": "Each arrow, bolt or javelin that strikes an enemy more than {far} m away adds a star (up to {max}; they fade {fade} s after the last). With {max} stars your next shot is a Shooting Star: {bonus}% more damage, and it pierces every enemy in line (enemies after the first take {falloff}%).",
		"nums": {"far": 10.0, "max": 5, "fade": 12.0, "bonus": 60.0, "falloff": 60.0}},
	&"arcanist": {"name": "Runescript", "desc": "Each spell you pay Mana for writes a rune (up to {max}, {dur} s): your spells deal {per}% more damage for each rune.",
		"nums": {"max": 3, "dur": 8.0, "per": 4.0}},
	&"archmage": {"name": "Elemental Attunement", "desc": "Every damaging spell you pay Mana for turns your attunement Fire > Ice > Lightning and sends an attuned bolt at the first enemy it strikes: {pct}% of that hit as the attuned element. The bolt cannot repeat, echo or trigger other effects.",
		"nums": {"pct": 20.0}},
	&"void_sovereign": {"name": "Collapse", "desc": "An enemy defeated by your spell collapses: enemies within {radius} m are pulled up to {pull} m toward it (walls stop the pull; bosses are not pulled) and take {pct}% of the defeating hit as Dark damage. At most once every {icd} s.",
		"nums": {"radius": 4.0, "pull": 1.5, "pct": 30.0, "icd": 2.0}},
	&"nightstalker": {"name": "From the Shadows", "desc": "After a dodge, your next weapon attack within {window} s strikes from the shadows: {bonus}% more damage and +{combo} Combo.",
		"nums": {"window": 2.0, "bonus": 25.0, "combo": 1}},
	&"phantom_reaper": {"name": "Soul Harvest", "desc": "Each enemy you defeat releases a soul: +{combo} Combo and Phantom Crossing recovers {cd} s sooner. At most once a second.",
		"nums": {"combo": 1, "cd": 2.0, "icd": 1.0}},
	&"blood_sovereign": {"name": "Blood Price", "desc": "When an enemy dies while Bleeding, its blood bursts: enemies within {radius} m start Bleeding at {share}% of its bleed, and you recover {heal}% of Maximum HP. At most once a second.",
		"nums": {"radius": 3.0, "share": 40.0, "heal": 2.0, "icd": 1.0}},
}

## A signature's value.
static func sig(id: StringName, key: String) -> float:
	return float((SIGNATURES.get(id, {}) as Dictionary).get("nums", {}).get(key, 0.0))

## A signature's text with its numbers filled in.
static func signature_text(id: StringName) -> String:
	var s: Dictionary = SIGNATURES.get(id, {})
	if s.is_empty():
		return ""
	var text := String(s.desc)
	for k in s.nums:
		text = text.replace("{%s}" % k, StatDefs._num(float(s.nums[k])))
	return text

const TALENT_ICON := "res://assets/ui/icons/talents/%s.svg"
const F := StatModifier.Op.FLAT
const I := StatModifier.Op.INC
const M := StatModifier.Op.MORE

## Each ranked transcendence talent grows by `TAIL` of its first rank per extra level (rank 25 = 7x rank 1).
const TAIL := 0.25

## Hard caps of the flag effects below (after every rank and item bonus).
const CAPS := {&"rg_block_valor": 12.0, &"dg_march": 0.06, &"dg_iron_tyrant": 0.15, &"gp_barrier": 0.25,
	&"tr_trap_dur": 0.25, &"ww_area": 0.25, &"ww_rootbound": 0.10, &"potion_heal": 0.25, &"ss_far": 0.25,
	&"ss_comet_rhythm": 0.5, &"ss_focus_hold": 0.5, &"ar_charge_linger": 2.0, &"am_concord": 0.2,
	&"am_shelter": 0.10, &"vs_area": 0.15, &"ar_mana_eff": 0.15, &"rg_unbroken": 0.25, &"vs_entropy": 0.25, &"ns_ambush": 0.08, &"pr_finisher": 0.25,
	&"pr_rhythm": 0.25, &"bs_bleed": 0.4, &"bs_hunger": 0.25}

static func cap(flag: StringName, value: float) -> float:
	return minf(value, float(CAPS.get(flag, INF)))

## The talents, by id. kind minor = ranked (rank 1 + diminishing tail), major = one rank (a fixed bounded effect).
## mods: [[stat, op, value at rank 1]], flags: {flag: value at rank 1}. desc uses {m0}, {m1} (mod values) and {f0}
## (flag value), filled in by `talent_text`.
const TALENTS := {
	# Block Strength reaches its 100% cap from Strength alone at high levels, so Crown Discipline also adds a little
	# Block Chance (the 75% cap still applies) and never becomes an empty node.
	&"rg_crown_discipline": {"name": "Crown Discipline", "kind": "minor", "mods": [[&"block_strength", F, 0.03], [&"block_chance", F, 0.01]],
		"desc": "+{m0}% Block Strength (at most 100%) and +{m1}% Block Chance (at most 75%)."},
	# the knockback part works after Knockback Resistance, which Strength alone caps (80%) by level 300
	&"rg_unbroken_line": {"name": "Unbroken Line", "kind": "minor", "mods": [[&"poise", I, 0.04]], "flags": {&"rg_unbroken": 0.03},
		"desc": "+{m0}% Poise, and blows push you back {f0}% less far after Knockback Resistance (at most 25%)."},
	&"rg_guardians_resolve": {"name": "Guardian's Resolve", "kind": "major", "flags": {&"rg_block_valor": 4.0},
		"desc": "Each successful block gives {f0} extra Valor (at most once every 0.5 s)."},
	&"dg_dreadsteel": {"name": "Dreadsteel", "kind": "minor", "mods": [[&"dmg_dark", I, 0.03], [&"phys_damage", F, 0.03]],
		"desc": "+{m0}% increased Dark damage and +{m1}% Physical damage (one shared damage budget)."},
	&"dg_relentless_march": {"name": "Relentless March", "kind": "minor", "flags": {&"dg_march": 0.012},
		"desc": "{f0}% more Movement Speed while in combat (at most 6%)."},
	&"dg_iron_tyrant": {"name": "Iron Tyrant", "kind": "major", "flags": {&"dg_iron_tyrant": 0.08},
		"desc": "Spending 20 or more Valor on a skill grants a barrier of {f0}% of Maximum HP for 6 s. Once every 15 s."},
	&"gp_radiant_steel": {"name": "Radiant Steel", "kind": "minor", "mods": [[&"dmg_light", I, 0.03], [&"phys_damage", F, 0.02]],
		"desc": "+{m0}% increased Light damage and +{m1}% Physical damage."},
	&"gp_merciful_oath": {"name": "Merciful Oath", "kind": "minor", "mods": [[&"healing", I, 0.03]], "flags": {&"gp_barrier": 0.03},
		"desc": "+{m0}% increased healing, and your barriers are {f0}% stronger (at most 25%)."},
	&"gp_hallowed_armor": {"name": "Hallowed Armor", "kind": "minor", "mods": [[&"defense", I, 0.03], [&"res_light", F, 0.02], [&"res_dark", F, 0.02]],
		"desc": "+{m0}% Defense, +{m1}% Light Resistance and +{m2}% Dark Resistance (resistance caps still apply)."},
	&"tr_keen_trail": {"name": "Keen Trail", "kind": "minor", "mods": [[&"accuracy", I, 0.03], [&"crit_chance", F, 0.006]],
		"desc": "+{m0}% Accuracy and +{m1}% Critical Chance."},
	&"tr_patient_aim": {"name": "Patient Aim", "kind": "minor", "mods": [[&"focus_gain", I, 0.04]],
		"desc": "+{m0}% Focus gained (Focus still builds only at a safe distance or from ranged hits)."},
	&"tr_fieldcraft": {"name": "Fieldcraft", "kind": "minor", "mods": [[&"trap_damage", I, 0.04]], "flags": {&"tr_trap_dur": 0.04},
		"desc": "+{m0}% trap damage; snares hold {f0}% longer (at most 25%)."},
	&"ww_thorncraft": {"name": "Thorncraft", "kind": "minor", "mods": [[&"trap_damage", I, 0.03]], "flags": {&"ww_area": 0.03},
		"desc": "+{m0}% trap damage; your Wildwarden areas deal {f0}% more damage (at most 25%)."},
	&"ww_rootbound_guard": {"name": "Rootbound Guard", "kind": "major", "flags": {&"ww_rootbound": 0.10},
		"desc": "{f0}% more Defense while you stand in your own Living Thicket or Warden's Refuge (one bonus, however many overlap)."},
	&"ww_verdant_reserve": {"name": "Verdant Reserve", "kind": "minor", "mods": [[&"max_hp", I, 0.02]], "flags": {&"potion_heal": 0.03},
		"desc": "+{m0}% Maximum HP; health draughts restore {f0}% more (at most 25%)."},
	&"ss_celestial_sight": {"name": "Celestial Sight", "kind": "minor", "flags": {&"ss_far": 0.03},
		"desc": "Your projectiles deal {f0}% more damage to enemies more than 12 m away (at most 25%). Reach is unchanged."},
	&"ss_comet_rhythm": {"name": "Comet Rhythm", "kind": "major", "flags": {&"ss_comet_rhythm": 0.4},
		"desc": "A critical hit shortens every skill cooldown by {f0} s, at most once per second."},
	&"ss_steady_constellation": {"name": "Steady Constellation", "kind": "minor", "flags": {&"ss_focus_hold": 0.05},
		"desc": "Focus fades {f0}% slower out of combat (at most 50%). It never builds out of combat."},
	# its own multiplier on paid spells: Wisdom alone reaches the 30% Mana cost reduction cap at high levels
	&"ar_runic_efficiency": {"name": "Runic Efficiency", "kind": "minor", "flags": {&"ar_mana_eff": 0.015},
		"desc": "Spells cost {f0}% less Mana, on top of Mana cost reduction (at most 15%; a spell never costs less than half)."},
	&"ar_charge_discipline": {"name": "Charge Discipline", "kind": "minor", "flags": {&"ar_charge_linger": 0.25},
		"desc": "Arcane Charge lasts {f0} s longer before it fades (at most 2 s)."},
	&"ar_aether_precision": {"name": "Aether Precision", "kind": "minor", "mods": [[&"crit_chance", F, 0.006], [&"crit_damage", F, 0.03]],
		"desc": "+{m0}% Critical Chance and +{m1}% Critical Damage."},
	&"am_elemental_concord": {"name": "Elemental Concord", "kind": "minor", "flags": {&"am_concord": 0.03},
		"desc": "Spells deal {f0}% more damage to enemies with two or more different elemental ailments (counted once; at most 20%)."},
	&"am_master_channeling": {"name": "Master Channeling", "kind": "minor", "mods": [[&"cast_speed", I, 0.015]],
		"desc": "+{m0}% Cast Speed."},
	&"am_prismatic_shelter": {"name": "Prismatic Shelter", "kind": "major", "flags": {&"am_shelter": 0.10},
		"desc": "Spending Arcane Charge grants +{f0}% to every Resistance for 4 s. Once every 12 s. Resistance caps still apply."},
	&"vs_void_geometry": {"name": "Void Geometry", "kind": "minor", "flags": {&"vs_area": 0.02},
		"desc": "Void Sovereign areas are {f0}% larger (at most 15%)."},
	&"vs_entropy": {"name": "Entropy", "kind": "minor", "flags": {&"vs_entropy": 0.03},
		"desc": "Your Dark damage is {f0}% higher against Cursed enemies (at most 25%)."},
	&"vs_sovereigns_reserve": {"name": "Sovereign's Reserve", "kind": "minor", "mods": [[&"max_mana", I, 0.03], [&"mana_regen", I, 0.03]],
		"desc": "+{m0}% Maximum Mana and +{m1}% Mana Regeneration."},
	&"ns_ambush_training": {"name": "Ambush Training", "kind": "minor", "flags": {&"ns_ambush": 0.01},
		"desc": "+{f0}% Critical Chance for 3 s after Stealth ends (at most 8%)."},
	# dodge distance rather than Movement Speed, which a Shadowblade already has at its cap from level 130
	&"ns_silent_footwork": {"name": "Silent Footwork", "kind": "minor", "mods": [[&"evasion", I, 0.03], [&"dodge_distance", I, 0.03]],
		"desc": "+{m0}% Evasion and +{m1}% Dodge Distance."},
	&"ns_patient_blade": {"name": "Patient Blade", "kind": "minor", "flags": {&"combo_linger": 0.25},
		"desc": "Combo lasts {f0} s longer before it fades (all Combo lingering together at most 4 s)."},
	&"pr_ghoststep": {"name": "Ghoststep", "kind": "minor", "mods": [[&"dodge_cooldown", F, -0.03]],
		"desc": "Dodge recovers {m0} s faster (never below 0.3 s)."},
	&"pr_reaping_edge": {"name": "Reaping Edge", "kind": "minor", "flags": {&"pr_finisher": 0.03},
		"desc": "Finishers deal {f0}% more damage (at most 25%)."},
	&"pr_untouchable_rhythm": {"name": "Untouchable Rhythm", "kind": "major", "flags": {&"pr_rhythm": 0.25},
		"desc": "A dodge grants {f0}% more Evasion for 1.5 s. Once every 6 s."},
	&"bs_hemomancy": {"name": "Hemomancy", "kind": "minor", "flags": {&"bs_bleed": 0.04},
		"desc": "Bleeding you cause deals {f0}% more damage (at most 40%)."},
	&"bs_sovereigns_hunger": {"name": "Sovereign's Hunger", "kind": "minor", "flags": {&"bs_hunger": 0.03},
		"desc": "Life Leech and Bloodsucker heal {f0}% more (at most 25%; Life Leech never returns more than 30% of a hit)."},
	&"bs_crimson_endurance": {"name": "Crimson Endurance", "kind": "minor", "mods": [[&"max_hp", I, 0.02], [&"healing", I, 0.02]],
		"desc": "+{m0}% Maximum HP and +{m1}% increased healing. Bloodcurse still reduces healing as usual."},
}

# ---- Lookups -------------------------------------------------------------------------------------------------------

static func is_family(id: StringName) -> bool:
	return FAMILIES.has(id)

static func is_advanced(id: StringName) -> bool:
	return CLASSES.has(id)

## Any of the sixteen identities.
static func is_identity(id: StringName) -> bool:
	return FAMILIES.has(id) or CLASSES.has(id)

static func info(id: StringName) -> Dictionary:
	if CLASSES.has(id):
		return CLASSES[id]
	return FAMILIES.get(id, {})

static func family_of(id: StringName) -> StringName:
	if FAMILIES.has(id):
		return id
	return StringName(CLASSES[id].family) if CLASSES.has(id) else &""

static func stage_of(id: StringName) -> int:
	return int(CLASSES[id].stage) if CLASSES.has(id) else (0 if FAMILIES.has(id) else -1)

static func parent_of(id: StringName) -> StringName:
	return StringName(CLASSES[id].parent) if CLASSES.has(id) else &""

static func name_of(id: StringName) -> String:
	var d := info(id)
	return String(d.get("name", String(id).capitalize()))

## The identities that advance directly from `id` (a family has one, a first transcendence two, a master none).
static func children_of(id: StringName) -> Array:
	var out := []
	for k in CLASSES:
		if StringName(CLASSES[k].parent) == id:
			out.append(k)
	out.sort_custom(func(a, b): return String(a) < String(b))
	return out

## [family, stage 1, stage 2] up to and including `id`.
static func ancestry(id: StringName) -> Array:
	var out := []
	var cur := id
	var guard := 0
	while cur != &"" and guard < 4:
		out.push_front(cur)
		cur = parent_of(cur)
		guard += 1
	return out if not out.is_empty() and FAMILIES.has(out[0]) else []

## Every identity of a family, in order (family, first transcendence, masters).
static func family_members(family: StringName) -> Array:
	if not FAMILIES.has(family):
		return []
	var out := [family]
	for c in children_of(family):
		out.append(c)
		out.append_array(children_of(c))
	return out

## Which identity grants `content_id` (a granted skill or talent id), or &"".
static func owner_of(content_id: StringName) -> StringName:
	if _owner_cache.is_empty():
		for k in CLASSES:
			for s in CLASSES[k].skills:
				_owner_cache[s] = k
			for t in CLASSES[k].talents:
				_owner_cache[t] = k
	return _owner_cache.get(content_id, &"")

static var _owner_cache := {}

static func level_for_stage(stage: int) -> int:
	return FIRST_LEVEL if stage <= 1 else MASTER_LEVEL

## Text of a talent at a rank: {m0} {m1} = mod values, {f0} = flag value, as percentages where they are fractions.
static func talent_text(id: StringName, rank: int) -> String:
	var t: Dictionary = TALENTS.get(id, {})
	if t.is_empty():
		return ""
	var r := TreeDef.rank_power(maxi(rank, 1), 1, TAIL)
	var text := String(t.desc)
	var mods: Array = t.get("mods", [])
	for i in mods.size():
		var v := float(mods[i][2]) * r
		var st := StringName(mods[i][0])
		var shown := StatDefs._num(absf(v)) if st == &"dodge_cooldown" else StatDefs._num(absf(v) * 100.0)
		text = text.replace("{m%d}" % i, shown)
	var fl: Dictionary = t.get("flags", {})
	for f in fl:
		var v := cap(f, float(fl[f]) * r)
		var shown := StatDefs._num(v) if f in [&"rg_block_valor", &"ss_comet_rhythm", &"ar_charge_linger", &"combo_linger"] else StatDefs._num(v * 100.0)
		text = text.replace("{f0}", shown)
	return text
