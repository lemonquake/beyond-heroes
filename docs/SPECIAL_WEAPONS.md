# Special weapons and the `alj` code (bh-024)

**Status: waiting for the models.** The request was to turn the models in `models/special_weapon/` into two Legendary
weapons, and to make `alj` give the player both as variants that can be equipped without restrictions. That folder was
not in the repository (no branch had it on 30 September 2026), so the weapons themselves are not in the game yet.

What is already in place:

- **Unbound items** (`ItemInstance.unbound`, saved as `"ub"`): an Unbound piece ignores the level, attribute and
  class-rank requirements everywhere they are checked (equipping, Tempos, auto-loot, merchants' "usable" marks, Lape's
  appraisal). Slot rules still apply (a two-handed weapon still needs both hands). The tooltip says "Unbound: no level,
  attribute or rank requirement".
- **`DataSpecialWeapons`** (`game/src/data/data_special_weapons.gd`): the table the weapons go in. Each row becomes a
  Legendary named unique with its own model and icon; its damage is the weapon type's level curve +15%.
- **`alj`** (Cheats): adds every special weapon to the bag as an Unbound variant. With the table empty it answers
  "no special weapons are in this build yet" and adds nothing.

## Adding the weapons once the models are in the repository

1. Commit the files under `models/special_weapon/` (GLB/FBX/OBJ plus textures).
2. For each weapon, export a GLB in the weapon hand-socket convention of `tools/blender/characters/bh_weapons.py`
   (origin at the grip, long axis +Z in Blender = +Y in Godot) to `game/assets/weapons/special/<id>.glb`.
3. Add its row to `DataSpecialWeapons.ROWS`:
   `[id, name, weapon type, level, attacks per second, element, power id, requirements, lore]`, e.g.
   `[&"sw_example", "Example", &"sword", 40, 1.3, Elements.FIRE, &"relentless", {&"str": 60}, "..."]`.
4. Render its icon (`tools/blender/items/build_items.py -- icons <id>` then `icons_post.game_icon`) to
   `game/assets/ui/icons/items3d/<id>.png`, and re-import (`godot --headless --path game --import`).
5. `alj` then gives both, Unbound.
