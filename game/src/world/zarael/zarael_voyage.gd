class_name ZaraelVoyage
## bh-029: Agdao's ship, the Sunwake (Captain Ilsa Rhondar, DataNpcsZarael): sails between Wyman Outpost's Marsh Jetty
## (spawn `jetty`) and Agdao's pier (spawn `pier`) through the loading screen. The first landing at Agdao plays
## Terax's welcome (StoryDirector, `zr_terax_met`).

static func sail(to_zarael: bool) -> void:
	if Game.hero == null:
		return
	if to_zarael:
		Game.set_world_flag(DataZarael.F_SAILED, true)
		Game.travel(&"agdao", &"pier")
	else:
		Game.travel(&"wyman_outpost", &"jetty")
