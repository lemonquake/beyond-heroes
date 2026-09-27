class_name WeaponLoadout
extends RefCounted
## Resolved combat configuration of the equipped main/sub weapons. Built by Equipment, read by the stat
## calculator, the damage pipeline and the animation layer.

var main_type: WeaponTypeDef
var main_min := 1.0
var main_max := 2.0
var main_crit := 0.05
var main_element := Elements.PHYSICAL
var main_elem_share := 0.0      # fraction of main weapon damage that is elemental (e.g. fire sword)
var main_aps := 1.4             # the main weapon's own attacks per second (ItemBaseDef.weapon_aps)

var off_type: WeaponTypeDef     # a weapon in the sub slot (dual wield) — null for shield/empty
var off_min := 0.0
var off_max := 0.0
var off_element := Elements.PHYSICAL
var off_elem_share := 0.0
var off_aps := 0.0

var has_shield := false
var shield_block := 0.0
var shield_block_strength := 0.0

var dual_wield := false

const DUAL_ATTACK_SPEED_MORE := 0.15   # 15% more attack speed while dual wielding
const DUAL_DAMAGE_PER_HAND := 0.85     # each hand hits for 85% of its weapon damage
const DUAL_DEFENSE_LESS := 0.10        # 10% less defense (no shield, open stance)

const UNARMED_APS := 1.4

## Base attacks per second at 1.0 attack speed: the equipped weapon's own rate; dual wield averages both hands.
func aps() -> float:
	if main_type == null:
		return UNARMED_APS
	if dual_wield and off_aps > 0.0:
		return (main_aps + off_aps) * 0.5
	return main_aps

func is_unarmed() -> bool:
	return main_type == null

func stance() -> StringName:
	if main_type == null:
		return &"unarmed"
	if dual_wield:
		return &"dual"
	return main_type.id

## Weapon for a given combo step. Dual wield alternates: step 0 main, 1 off, 2 main ...
func hand_for_step(step: int) -> int:
	if dual_wield and step % 2 == 1:
		return 1
	return 0

func damage_range(hand: int) -> Vector2:
	if hand == 1 and off_type != null:
		return Vector2(off_min, off_max)
	return Vector2(main_min, main_max)

func element_for(hand: int) -> int:
	return off_element if (hand == 1 and off_type != null) else main_element

func elem_share_for(hand: int) -> float:
	return off_elem_share if (hand == 1 and off_type != null) else main_elem_share

func type_for(hand: int) -> WeaponTypeDef:
	return off_type if (hand == 1 and off_type != null) else main_type
