class_name DataCutscenes
## bh-021: the cutscenes of the main story (src/cinema/scenes/). skip_all is false only for the_three (the author's
## rule: the introduction of Aljay and Roydo can be skipped scene by scene, never as a whole).
##   prologue       a new game: Jre, the Holy War, the waypoint waking; the hero arrives on the Sanctuary Terrace
##   shard          Wyman Outpost: Sir Aldric's reliquary, the Dusk-Piercer Shard, a glimpse of the dragon helm
##   the_three      Olivar: Paul David's tale — Roydo, Paul David and Aljay; the Weeping Causeway; the betrayal
##   kethrax_intro  the Drowned Tollhouse: Kethrax drags his chains out of the marsh
##   chain_breaks   Kethrax falls; on the Black Spire one of Aljay's chains snaps

const SCRIPTS := {
	&"prologue": "res://src/cinema/scenes/cs_prologue.gd",
	&"shard": "res://src/cinema/scenes/cs_shard.gd",
	&"the_three": "res://src/cinema/scenes/cs_the_three.gd",
	&"kethrax_intro": "res://src/cinema/scenes/cs_kethrax_intro.gd",
	&"chain_breaks": "res://src/cinema/scenes/cs_chain_breaks.gd",
	# bh-029: Zarael — Terax on Agdao's pier, and the Dawn Engine waking
	&"terax_welcome": "res://src/cinema/scenes/cs_terax_welcome.gd",
	&"dawn_current": "res://src/cinema/scenes/cs_dawn_current.gd",
}

static func make(id: StringName) -> Cutscene:
	if not SCRIPTS.has(id):
		return null
	var c: Cutscene = (load(SCRIPTS[id]) as GDScript).new()
	c.id = id
	return c

static func ids() -> Array:
	return SCRIPTS.keys()
