# Contract: UI art — icons and emblems (bh-001 / C7a)

Hand-author SVG (and generate with Python scripts where useful) into `game/assets/ui/`. Scripts in `tools/ui_art/`.
Do not touch other folders; do not run Godot on `game/`.

Style: dark-fantasy painted-emblem look rendered in vector: rich gradients (radial/linear), rim highlights, inner shadows via
layered paths, subtle glows, strong readable silhouettes at 48 px and still attractive at 128 px. Coherent palette per element.
No text inside icons. No generic clip-art look; each icon should read like an ARPG ability/item icon (think a framed
painted emblem). ViewBox `0 0 128 128`. Include a full-bleed dark background with a vignette in skill/talent icons (item icons
use transparent background). Avoid SVG features Godot's ThorVG importer does not support (no filters like feGaussianBlur,
no masks with complex compositing, no CSS, no text, no external refs). Use gradients, opacity, and stacked paths for glows.

## Files (names are a contract)

`icons/skills/`: knight — `cleave`, `shield_bash`, `leap_slam`, `whirlwind`, `war_cry`, `judgment`, `ground_fissure`,
`iron_bulwark`; mage — `firebolt`, `frost_nova`, `chain_lightning`, `blink`, `meteor`, `tidal_wave`, `gale_burst`,
`arcane_surge`, `shadow_curse`, `radiant_ward`, `stone_spear`.
`icons/talents/`: `crit`, `fire_res`, `sword_mastery`, `block_mana`, `crit_cooldown`, `burning_spread`, `frozen_impact`,
`armor`, `vitality`, `valor`, `heavy_hands`, `bulwark`, `counter`, `momentum`, `arcane_mind`, `mana_flow`, `elemental_focus`,
`conduit`, `permafrost`, `pyromancy`, `storm`, `tides`, `shadow`, `radiance`, `keystone_juggernaut`, `keystone_unbreakable`,
`keystone_archmage`, `keystone_elemental_overload`, `minor_str`, `minor_agi`, `minor_int`, `minor_wis`, `minor_spi`, `minor_dex`.
`icons/items/`: `sword`, `greatsword`, `axe`, `spear`, `dagger`, `bow`, `staff`, `wand`, `shield`, `helm_plate`, `helm_hood`,
`inner_garment` (padded gambeson / silk undershirt), `armor_plate`, `armor_robe`, `gloves_plate`, `gloves_cloth`, `boots_plate`,
`boots_cloth`, `ring`, `amulet`, `charm`, `potion_health`, `potion_mana`, `mat_iron_shard`, `mat_arcane_dust`, `mat_ember_core`,
`mat_bone_fragment`, `gold`.
`icons/elements/`: `physical`, `fire`, `ice`, `lightning`, `earth`, `wind`, `water`, `light`, `dark`.
`icons/status/`: `burning`, `chilled`, `frozen`, `shocked`, `staggered`, `wet`, `cursed`, `purged`, `bleeding`, `stunned`,
`valor`, `arcane_charge`, `guard`, `haste`, `regen`, `shielded`.
`icons/attributes/`: `strength`, `agility`, `intelligence`, `wisdom`, `spirit`, `dexterity`.
`icons/classes/`: `knight`, `mage` (larger crest-like emblems, 256 viewBox allowed).
`emblem/`: `logo_emblem.svg` — a heraldic emblem (crossed sword and staff behind a cracked crest with a radiant core) used behind
the title text on the main menu (text is rendered by the game, not in the SVG). `ornament_divider.svg` (horizontal filigree
divider, 512x32), `ornament_corner.svg` (corner filigree 64x64, top-left orientation).

## Evidence

`work/lemondev/bh-001/evidence/ui_art/`: contact sheet PNGs rendering all icons at 48 px and 128 px on a dark background
(rasterize with a Python SVG renderer you can run locally, e.g. `cairosvg` if installed, or Blender's SVG import, or write a
minimal rasterizer; if none works, say so). `validation.txt`: each file parsed as XML, viewBox present, no forbidden elements.
