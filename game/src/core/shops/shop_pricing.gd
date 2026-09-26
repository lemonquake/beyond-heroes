class_name ShopPricing
## The one place merchant prices are computed.
##
##   value        = ItemInstance.base_value()             (base value x rarity x item level x affixes/powers x quality)
##   buy price    = ceil(value x markup x specialty x reputation)          per unit
##   sell price   = floor(value x 0.25 x sell_rate x specialty x reputation) per unit, never above the buy price
##   buyback      = exactly what the merchant paid you
##
## specialty:  a merchant who deals in the item's category sells it 10% cheaper and pays 20% more for it.
## reputation: relationship -100..100 moves prices by up to ±10% (reputation-ready; dialogue can change it).
## Level scaling lives in base_value (ilvl), so the same formula stays sane from level 1 to the cap.

const SELL_FRACTION := 0.25
const SPECIALTY_BUY := 0.9
const SPECIALTY_SELL := 1.2
const REPUTATION_SWING := 0.10

static func reputation_factor(rel: int) -> float:
	return clampf(float(rel) / 100.0, -1.0, 1.0) * REPUTATION_SWING

static func buy_price(item: ItemInstance, shop: ShopDef, rel := 0) -> int:
	var v := item.base_value() * shop.markup
	if shop.is_specialty(item):
		v *= SPECIALTY_BUY
	v *= 1.0 - reputation_factor(rel)
	return maxi(1, ceili(v))

static func sell_price(item: ItemInstance, shop: ShopDef, rel := 0) -> int:
	if not item.base.sellable:
		return 0
	var v := item.base_value() * SELL_FRACTION * shop.sell_rate
	if shop.is_specialty(item):
		v *= SPECIALTY_SELL
	v *= 1.0 + reputation_factor(rel)
	var unit := maxi(1, floori(v))
	return mini(unit, buy_price(item, shop, rel))

## Prices for a stack. `discount` (0..1) is a guild privilege at this merchant (GuildRules.shop_discount).
static func buy_total(item: ItemInstance, shop: ShopDef, count: int, rel := 0, discount := 0.0) -> int:
	var unit := buy_price(item, shop, rel)
	if discount > 0.0:
		unit = maxi(1, ceili(float(unit) * (1.0 - clampf(discount, 0.0, 0.9))))
	return unit * maxi(1, count)

static func sell_total(item: ItemInstance, shop: ShopDef, rel := 0) -> int:
	return sell_price(item, shop, rel) * item.count

## Purchases at or above this share of the hero's gold (or this absolute amount) ask for confirmation.
static func needs_confirmation(price: int, gold: int) -> bool:
	return price >= 500 or (gold > 0 and float(price) >= float(gold) * 0.4)
