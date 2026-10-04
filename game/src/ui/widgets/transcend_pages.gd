class_name TranscendPages
## Class Transcendence helpers shared by the Skills and Talents windows: which advancements a hero can preview (locked)
## and the plain hint shown above a preview.

## The identities whose pages a hero may preview: the next advancement (both masters after the first one).
static func preview_ids(hero: HeroData) -> Array:
	if hero == null:
		return []
	return ClassTranscendence.valid_next_choices(hero)

static func preview_hint(hero: HeroData, id: StringName) -> String:
	var why := ClassTranscendence.can_transcend(hero, id)
	if why == "":
		return "Visit the Grand Master in the Guild House to become a %s." % DataTranscendence.name_of(id)
	return "%s. Then visit the Grand Master in the Guild House." % why
