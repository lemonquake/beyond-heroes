class_name TradeRules
## Rules of a player-to-player trade (bh-016): what may be offered, whether an offer is still good, and the atomic swap
## each machine performs on its own hero once both players have accepted the same two offers. Pure rules over
## HeroData (no nodes, no network): Net carries the messages, TradeWindow shows them, tests call these directly.
## An offer is {"gold": int, "items": [ItemInstance]}; what arrives from the other player is {"gold": int, "items": [Dictionary]}.

const MAX_ITEMS := 10
const MAX_GOLD := 100000000            # sanity cap on what the other side may claim to offer

## "" when `it` may be put in a trade, otherwise why not.
static func item_error(it: ItemInstance) -> String:
	if it == null:
		return "Nothing there"
	if it.is_protected():
		return "Locked and favorite items are not traded"
	if it.base.is_quest():
		return "Quest items are not traded"
	return ""

## "" when `offer` can be honoured by `hero` right now.
static func offer_error(hero: HeroData, offer: Dictionary) -> String:
	var gold := int(offer.get("gold", 0))
	if gold < 0 or gold > hero.inventory.gold:
		return "You do not have %d gold" % gold
	var items: Array = offer.get("items", [])
	if items.size() > MAX_ITEMS:
		return "A trade holds at most %d items" % MAX_ITEMS
	var seen := {}
	for it in items:
		if seen.has(it):
			return "The same item is offered twice"
		seen[it] = true
		if hero.inventory.index_of(it) < 0:
			return "%s is no longer in your bag" % (it as ItemInstance).display_name()
		var e := item_error(it)
		if e != "":
			return e
	return ""

## "" when `hero`'s bag has room for `incoming` items after their own offered items leave it.
static func fit_error(hero: HeroData, offer: Dictionary, incoming: int) -> String:
	var room := hero.inventory.free_cells()
	for it in offer.get("items", []):
		var index := hero.inventory.index_of(it)
		if index >= 0 and index < hero.inventory.bag_capacity:
			room += 1
	if incoming > room:
		return "Your bag needs room for %d more item%s" % [incoming - room, "" if incoming - room == 1 else "s"]
	return ""

## Sanitise what the other machine sent: {"gold", "items": [dict]} -> {"gold", "items": [ItemInstance]}. Unknown or
## malformed items are dropped; the receiver's own locks and favorites are never inherited.
static func read_incoming(d: Dictionary) -> Dictionary:
	var out := {"gold": clampi(int(d.get("gold", 0)), 0, MAX_GOLD), "items": []}
	for raw in d.get("items", []):
		if out.items.size() >= MAX_ITEMS or not (raw is Dictionary):
			continue
		var it := ItemInstance.from_dict(raw)
		if it == null:
			continue
		it.count = clampi(it.count, 1, maxi(1, it.base.stack_max))
		it.locked = false
		it.favorite = false
		it.junk = false
		out.items.append(it)
	return out

## What travels: {"gold", "items": [dict]}.
static func to_wire(offer: Dictionary) -> Dictionary:
	var items := []
	for it in offer.get("items", []):
		items.append((it as ItemInstance).to_dict())
	return {"gold": int(offer.get("gold", 0)), "items": items}

## "" when the whole exchange can go ahead for `hero` (both checks), else the reason. Changes nothing.
static func swap_error(hero: HeroData, mine: Dictionary, theirs: Dictionary) -> String:
	var e := offer_error(hero, mine)
	if e != "":
		return e
	var trial := hero.inventory.copy()
	for it in mine.get("items", []):
		trial.take(hero.inventory.index_of(it))
	for it in theirs.get("items", []):
		if trial.add((it as ItemInstance).clone()) > 0:
			return "Your bags need more room for this trade"
	return ""

## Perform the exchange on `hero`: their offered items and gold arrive, this hero's leave. Returns "" or why not
## (in which case nothing changed).
static func swap(hero: HeroData, mine: Dictionary, theirs: Dictionary) -> String:
	var e := swap_error(hero, mine, theirs)
	if e != "":
		return e
	for it in mine.get("items", []):
		hero.inventory.remove_item(it)
	hero.inventory.gold += int(theirs.get("gold", 0)) - int(mine.get("gold", 0))
	for it in theirs.get("items", []):
		hero.inventory.add(it)
	hero.inventory.changed.emit()
	return ""

## One line for a summary: "3 items and 120 gold" / "nothing".
static func describe(offer: Dictionary) -> String:
	var n := (offer.get("items", []) as Array).size()
	var g := int(offer.get("gold", 0))
	var parts := []
	if n > 0:
		parts.append("%d item%s" % [n, "" if n == 1 else "s"])
	if g > 0:
		parts.append("%d gold" % g)
	return " and ".join(parts) if not parts.is_empty() else "nothing"
