class_name IdPicture
## bh-031: keeps the hero's ID picture (HeroData.id_pic) an ID shot of their own model: their look and what they
## wear right now. Re-shot when either changes (requests that arrive while a shot is being taken are merged into one
## more shot). Without a profile picture this is the face on the HUD, the Character window, the party frames, the
## save cards and what other players see.

static var _busy := false
static var _pending: HeroData
static var _last := {}              # hero instance id -> signature of the last shot

## The look and worn gear that the picture shows (a new shot only when this changes).
static func signature(hero: HeroData) -> int:
	var worn := []
	for slot in HeroWear.SLOTS:
		var it := hero.equipment.get_item(slot) if hero.equipment else null
		worn.append(String(it.base.id) if it and it.base else "")
	return hash([HeroLook.signature(hero.look), worn])

static func refresh(hero: HeroData, force := false) -> void:
	if hero == null or not Persona.available() or DisplayServer.get_name() == "headless":
		return
	if not force and not hero.id_pic.is_empty() and int(_last.get(hero.get_instance_id(), 0)) == signature(hero):
		return
	_pending = hero
	if _busy:
		return
	_busy = true
	while _pending != null:
		var h := _pending
		_pending = null
		var sig := signature(h)
		var img := await PortraitStudio.render_hero(h.look, h.equipment, ProfilePicture.SIZE)
		if img == null:
			continue
		h.id_pic = img.save_jpg_to_buffer(0.88)
		_last[h.get_instance_id()] = sig
		if h == Game.hero:
			Events.profile_picture_changed.emit(0)
			if h.profile_pic.is_empty() and Net.is_active():
				Net.send_profile_picture_all()
	_busy = false
