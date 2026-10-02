class_name DataGuide
## The first conversation of a new game: the starter Tempo (its name rolled per hero, {tempo}), the Tempo who came through the waypoint with the hero, introduces
## himself, explains what Tempos are and where to bind more (Veyra Ashgrave at the Shrine of the Fallen, grades,
## renowned spirits), then walks the hero through the controls and the first places to visit. Not placed in the world:
## UIRoot.start_intro() opens it on a new game, the Field Guide window (H) replays it.
## Graph format: see Dialogue. {key:<action>} placeholders quote the live key binding (rebinding changes the text).

const ID := &"guide_intro"
const DONE_FLAG := &"intro_guide_done"

static func intro() -> NpcDef:
	var st := DataTempos.STARTER
	var portrait := DataTempos.portrait_path(String(st.portrait))
	if portrait == "":
		portrait = "res://assets/ui/icons/classes/tempo_swordsman.svg"
	# bh-031: the starter Tempo speaks with its own face (an ID shot of its model, PortraitStudio.tempo_portrait)
	var h := Game.hero
	if h != null and Persona.available():
		for t in h.tempos:
			if t is TempoData and ((t as TempoData).tempo_name == Dialogue.starter_name(h) or h.tempos.size() == 1):
				portrait = "tempo:%d" % (t as TempoData).uid
				break
	return NpcDef.make(ID, Dialogue.starter_name(Game.hero), {"title": "Your Tempo  ·  Swordsman", "portrait": portrait, "map": &"",
		"graph": graph()})

static func graph() -> Dictionary:
	var done := {"set_flag": String(DONE_FLAG)}
	return {
		"entries": [[[], "wake"]],
		"nodes": {
			"wake": {"text": [
					"Easy. Easy. The waypoint threw you harder than it threw me. Breathe. You are on the **Sanctuary Terrace** in **Malasugue**, and nothing here wants to eat you.",
					"I am **{tempo}**. I stood a guard's watch on this terrace the night the dead came up the road. I held the shrine long enough for the townsfolk to reach the hearth wards. I did not walk away from it.",
					"When the waypoint woke for you, I felt the pull and came through at your side. I am a **Tempo** now, {hero}. Your Tempo, if you will have me."],
				"choices": [
					{"text": "Tell me everything. I want to know how this works.", "next": "what"},
					{"text": "Keep it short. I have done this before.", "next": "short"},
				]},
			# ---- Tempos
			"what": {"text": [
					"A Tempo is the spirit of a warrior who died fighting the monsters of Jre with a grudge still warm. We cannot fight alone for long. We need a living hero to anchor us.",
					"Bound to you, I carry **half of your strength**. When you grow, I grow. I strike what strikes you, and my **Soul Mend** will close your wounds when you bleed. When I am badly hurt I fall back to tend myself. That is not cowardice.",
					"My health sits under your portrait. Press **{key:tempos}** to open the **Tempo window**: hand me better steel from your bag and see what I can do. A Tempo's gear must be one tier below what you may wear."],
				"next": "where"},
			"where": {"text": [
					"You can carry **two** of us, and one place is still empty. **Veyra Ashgrave**, the Tempo-Caller, keeps the **Shrine of the Fallen** at the quiet end of the **Merchant Quarter**, the square south-east of the plaza. Spirits answer her call, and she binds them for **gold**.",
					"The spirits who answer grow with you. Rise in level, or do great deeds, and stronger **grades** answer instead: more skills, rarer ones, Mystics and Wardens among them. The weaker ones fade.",
					"And a few old names wait at her shrine: **renowned** spirits, with skills no one else has. They answer only a hero strong enough, and they are **not cheap**. Save for them before you go after anything big.",
					"If one of us falls, our token goes cold in your pack. Bring it to Veyra and she will call us back, for a price."],
				"next": "fight"},
			# ---- Controls
			"fight": {"text": [
					"Now, your feet and your blade. **{key:move_up} {key:move_left} {key:move_down} {key:move_right}** to move; you face the cursor. **{key:primary}** attacks, and holding it keeps the chain going. **{key:secondary}** is a heavy blow; with some weapons you can hold it to charge.",
					"**{key:dodge}** is a dodge roll, and for a moment nothing can touch you. With a shield, **{key:guard}** raises your guard. Watch the ground: a **red marking** is where something big is about to land. Get out of it."],
				"next": "skills"},
			"skills": {"text": [
					"Your skills sit on the bar at the bottom, keys **{key:skill_1}** to **{key:skill_6}**. **{key:potion_health}** drinks a health draught, **{key:potion_mana}** a mana draught.",
					"**{key:interact}** talks to people, opens doors and wakes waypoints. Hold **{key:show_loot}** to see everything lying on the ground, and click an item to pick it up. The mouse wheel zooms the view."],
				"next": "windows"},
			"windows": {"text": [
					"The rest you carry in your pack and your head. **{key:inventory}** Inventory, **{key:character}** Character, **{key:skills}** Skills, **{key:talents}** Talents, **{key:tempos}** Tempos, **{key:world_map}** Map. **{key:chat}** opens the chat line; **{key:pause}** closes a window, or pauses.",
					"Each level gives you **skill points** and **talent points**; spend them in those windows. On the Map you can pick a place and **track a route**; the directions show on the right of your screen."],
				"next": "start"},
			"start": {"text": [
					"Where to begin? **Elder Maelis** by the hearth, just down the terrace: she has been waiting three winters for whoever this waypoint chose, and I would not keep her waiting longer. After her, the town: **Anton** sells provisions, **Brannoc** forges, the **Salted Marlin** has beds, and the two guild halls will register you as a hero. The **Guild House** by the plaza posts paid odd jobs for both guilds.",
					"Forget any of this and press **{key:guide}**: the **Field Guide** keeps every key and every lesson, and I will say it all again if you ask. Now come on. I have been dead a long time, and I am bored of standing still."],
				"choices": [
					{"text": "Lead on, {tempo}.", "next": "end", "actions": [done]},
				]},
			"short": {"text": [
					"Good. Then only this: **{key:primary}** attacks, **{key:dodge}** dodges, **{key:skill_1}** to **{key:skill_6}** are your skills, **{key:potion_health}** and **{key:potion_mana}** your draughts, **{key:interact}** talks and opens doors.",
					"I carry half your strength and I mend your wounds. **{key:tempos}** opens my window. A second Tempo can be bound at **Veyra Ashgrave**'s **Shrine of the Fallen**, in the Merchant Quarter; stronger spirits answer as you grow, and a few renowned ones wait for a hero with deep pockets.",
					"Everything else is in the **Field Guide**: press **{key:guide}**. Elder Maelis is by the hearth, down the terrace, and she has an errand for you. Let us go."],
				"choices": [
					{"text": "Let us go.", "next": "end", "actions": [done]},
					{"text": "Actually, tell me everything.", "next": "what"},
				]},
		},
	}

# ---- Bestiary (bh-010): how to beat the newer monsters, in plain words (Field Guide / Keeper Thadric pages) ----------

## monster id -> [short title, what it does, how to beat it]
const BESTIARY := {
	&"necromancer": ["Necromancer", "Raises the freshly fallen as Risen, throws bone spears and wraps its friends in a Bone Ward.",
		"Kill it first. Every body it reaches becomes another fighter; a green ring on a corpse means one is about to stand up."],
	&"goblin_summoner": ["Goblin Summoner", "Beats a drum that makes goblins faster, and calls more skulkers up through a smoking burrow.",
		"Chase it down. It runs when it is alone and hurt, so cut it off before it reaches the others."],
	&"orc_shaman": ["Orc Shaman", "Plants a War Totem that makes every orc near it hit harder, and throws lightning that jumps between you and your Tempos.",
		"Smash the totem: it cannot move and breaks quickly. Keep your Tempos apart so the lightning cannot jump."],
	&"frost_revenant": ["Frost Revenant", "A frozen knight. Standing close chills you, it throws fans of ice and freezes the ground.",
		"Fire melts its guard. When it falls, a blue circle appears: step out before it shatters."],
	&"plague_bloater": ["Plague Bloater", "Spews bile in a cone and glows green when badly hurt. On death it bursts into a toxic cloud.",
		"When it starts swelling, back away. Lure other monsters next to it: the cloud hurts them too."],
	&"bandit_bombardier": ["Bandit Bombardier", "Lobs bombs that land, fizz, then explode. Badly hurt, it lights its powder keg and runs at you.",
		"Leave the red circles before the fuse ends. When the keg is lit, run the other way or finish it from range."],
	&"mire_troll": ["Mire Troll", "Heals very fast between blows.",
		"Burn it! Fire stops the healing for about four seconds. Hit it hard while it cannot heal."],
	&"rune_golem": ["Rune Golem", "Its rune core glows Fire, Ice or Lightning and changes every few seconds.",
		"Read the colour on its health bar. It is immune to that element and weak to the opposite one: Ice against Fire, Fire against Ice, Earth against Lightning."],
	&"broodmother": ["Broodmother", "A giant spider. Its web sticks you to the ground (no dodging), its bite poisons, and it lays spiderlings.",
		"Do not stand still in its line of fire. Kill the spiderlings fast, then focus the mother."],
	&"treasure_mimic": ["Mimic", "Looks like a treasure chest until you come close. Then it bites, and its tongue drags you in.",
		"A chest that sits a little crooked is worth a poke from range. Beaten, it pays well: extra gold and a good item."],
	&"spiderling": ["Spiderling", "A broodmother's hatchling.", "Weak alone. Sweep them up with an attack that hits many."],
	&"war_totem": ["War Totem", "An orc totem that makes nearby orcs stronger.", "Break it. It does not fight back."],
}

static func bestiary_entry(id: StringName) -> Array:
	return BESTIARY.get(id, [])
