class_name SafeCallable
## bh-030 crash fix. A lambda keeps a raw pointer to the object it was written in: an Enemy, the Player, a skill node.
## Projectiles, delayed blasts, shockwaves, orbs and traps outlive the one that made them. Once that owner is freed,
## even `is_valid()` on its lambda reads freed memory. The engine reports "slot >= slot_max" (a garbage object id)
## or "Trying to call a lambda with an invalid instance", and sometimes the whole game crashes. This happened with
## many monsters dying at once under area spells, while their own blasts and the spells' orbs were still in the air.
##
## Effects record the owner's id when the callback is assigned (the owner is alive then) and test that id before they
## touch the callable at all.

## The id of the object a callable is bound to (0 for static functions). Call this while the owner is alive.
static func owner_of(cb: Callable) -> int:
	return 0 if cb.is_null() else cb.get_object_id()

## Whether the callable may be called: its owner (when it has one) still exists, and only then the callable itself.
static func alive(cb: Callable, owner: int) -> bool:
	if cb.is_null():
		return false
	if owner != 0 and not is_instance_id_valid(owner):
		return false
	return cb.is_valid()
