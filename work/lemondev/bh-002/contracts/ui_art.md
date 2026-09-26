# Contract C7: UI art — frames, panels, HUD art, rarity art, icons, portraits (bh-002)

## Context

Beyond Heroes (Godot 4.4.1, 1920x1080 primary, must stay crisp at 3840x2160) needs a complete artistic UI identity that does
NOT look like generic Godot controls. Visual direction: ancient fantasy, mystical technology, arcane energy, **Aether**
(luminous cyan-white energy flowing in engraved channels), heroic mythology, premium dark-fantasy RPG presentation.
Palette already used by the game (`game/src/ui/ui_theme.gd`): near-black warm charcoal panels, bronze `#b88c52` / dim
bronze `#6b5233`, gold `#f5cc75`, parchment `#ebdcbd`, ember `#f2731f`, blood `#b81a1a`, mana blue `#3373f2`, arcane violet
`#9e73ff`; add Aether cyan `#7ff3ff` / `#d8fdff` as the signature accent.

bh-001 made 100+ SVG icons with scripts in `tools/ui_art/` (`bh_svg.py`, `bh_shapes.py`, `bh_frames.py`, `icons_*.py`,
`build_all.py`, `validate.py`, `render_evidence.py`, `godot_render/`). Keep their style for new icons and reuse the scripts.
ThorVG (Godot's SVG importer) does not support filters, masks with complex compositing, CSS, text or external refs.

Raster art: generate with Python 3.12 + numpy/PIL/scipy (installed). Write PNGs with alpha, sRGB. Everything must regenerate
from scripts in `tools/ui_art/` (deterministic seeds). No third-party images, fonts or downloads.

## Owned paths

`tools/ui_art/**`, `game/assets/ui/**` (new files; do not delete existing ones), `work/lemondev/bh-002/evidence/ui_art/**`.
Do NOT run Godot on `game/`. You may run Godot 4.4.1
(`A:\Installer\Godot_v4.4.1-stable_win64.exe\Godot_v4.4.1-stable_win64_console.exe`) on a throwaway project in your scratch
folder (the existing `tools/ui_art/godot_render/` does this for SVG contact sheets).

## Deliverables

All 9-slice textures: author at 2x (so they stay sharp at 4K when the game draws them at 1x-2x), document the patch margins
(in texture pixels) and the intended draw scale in `game/assets/ui/ui_art_manifest.json`:
`{"<relative path>": {"margins": [left, top, right, bottom], "use": "...", "scale": 0.5}}`.
Centers of panel textures must tile or stretch cleanly (subtle noise, no directional features in the center).

### `frames/` (PNG, 9-slice)
- `panel_main.png` — primary window frame: dark carved iron/stone border with bronze filigree, gold corner ornaments with a
  small aether gem in each corner, recessed dark leather/stone center with faint rune texture. ~512x512.
- `panel_inset.png` — recessed inner well (for lists, stat blocks). `panel_header.png` — title banner strip (ornate, wide,
  with center crest area). `panel_tooltip.png` — thin gold-edged tooltip frame. `panel_dialogue.png` — wide dialogue box
  with an ornate top edge. `panel_glass.png` — translucent dark glass HUD plate (for HUD sub-panels: skill bar backing,
  objective tracker) with bevel highlights.
- Buttons (each: `_normal`, `_hover`, `_pressed`, `_disabled`, `_focus`): `button_primary_*` (gold-trimmed, for confirm /
  Play / Buy), `button_*` (standard bronze), `button_menu_*` (main-menu wide banner: hover state has an aether glow line).
- Tabs: `tab_normal.png`, `tab_hover.png`, `tab_selected.png` (selected connects to the panel below).
- Controls: `checkbox_off.png`, `checkbox_on.png`, `slider_track.png`, `slider_fill.png`, `slider_grabber.png`,
  `slider_grabber_hover.png`, `scroll_track.png`, `scroll_grabber.png`, `dropdown_arrow.png`, `lineedit.png`,
  `lineedit_focus.png`, `separator_h.png` (filigree divider), `close_x.png`, `close_x_hover.png`.

### `slots/` (PNG)
- `slot.png`, `slot_hover.png`, `slot_selected.png`, `slot_disabled.png`, `slot_locked.png` — 128x128 inventory cell frames
  (transparent center-ish well so the item icon shows).
- `equip_slot.png` (larger ornate frame, 160x160) and silhouette glyph overlays `glyph_main_weapon.png`,
  `glyph_sub_weapon.png`, `glyph_helm.png`, `glyph_inner_garment.png`, `glyph_armor.png`, `glyph_gloves.png`,
  `glyph_boots.png`, `glyph_accessory.png` (pale engraved silhouettes shown in empty slots).
- `rarity_0.png` … `rarity_9.png` — overlay frames per tier (128x128, transparent center), increasingly ornate and bright:
  0 Beginner (worn grey-brown iron), 1 Common (plain white-grey steel), 2 Basic (green), 3 Advanced (blue), 4 Licensed
  (teal, with a small stamped seal/badge in a corner — faction license), 5 Elite (gold), 6 Master (orange-bronze, engraved),
  7 Mythical (magenta-violet, runic), 8 Legendary (crimson-orange flame filigree), 9 Aether (prismatic cyan-white, crystal
  corners, strongest glow). Also `rarity_glow_<n>.png` soft inner glow for 5–9.
- `skill_slot.png` (hotbar bezel 128x128 with ornate ring), `skill_slot_empty.png`, `cooldown_radial.png` (white radial
  progress mask for TextureProgressBar radial fill, 128x128), `keybind_badge.png` (small plaque for the key label).

### `hud/`
- `orb_frame_hp.png`, `orb_frame_mana.png` — ornate glass-sphere frames (~320x320, transparent interior circle) in the Diablo
  tradition but with Beyond Heroes filigree (HP: crimson/bronze with a lion/sun crest; Mana: blue/silver with a moon/star crest).
- `orb_glass.png` (specular highlight + inner shade overlay to draw above the liquid), `orb_liquid_noise.png` (tileable
  grayscale 256x256 swirl noise for a liquid shader).
- `bar_frame_resource.png` (class resource bar, ornate ends), `bar_frame_xp.png` (long thin XP bar frame, 9-slice),
  `bar_fill.png` (white bar fill with subtle vertical gradient, tinted in game), `bar_frame_boss.png` (large ornate boss
  bar with skull/horn end-caps, 9-slice), `bar_frame_target.png` (small target frame), `pip_empty.png`, `pip_full.png`
  (arcane charge pips).
- `minimap_frame.png` (circular ornate frame ~400x400, transparent center), `minimap_mask.png` (white disc).
- `buff_frame.png`, `debuff_frame.png` (48–64 px icon borders, green-gold vs red), `vignette_lowhp.png` (1920x1080-ish radial
  red vignette, alpha only at the edges), `vignette_dark.png`.
- `loot_beam.png` (vertical soft beam gradient, white, tinted per rarity), `mote.png`, `spark.png`, `ember.png` (particle
  sprites), `cursor_default.png`, `cursor_attack.png`, `cursor_interact.png`, `cursor_talk.png` (32–48 px, hotspot top-left
  documented in the manifest).

### `tree/` (skill/talent tree art)
- Node frames for states `_locked`, `_available`, `_allocated`: `node_minor_*` (small circle), `node_major_*` (octagon),
  `node_keystone_*` (large ornate star/sun frame), `node_skill_*` (square bezel), `node_upgrade_*` (diamond). 
- `connector.png` (tileable horizontal link texture, e.g. a thin engraved channel; the game tints it gold when active),
  `tree_bg_knight.png`, `tree_bg_mage.png` (1600x900 dark atmospheric backdrops: faint constellation/engraving lines, no text).

### `menu/`
- `title_logo.png` — "BEYOND HEROES" wordmark rendered as art (draw the letterforms yourself as vector shapes in a Trajan-like
  engraved style with metallic gradient, bevel and aether glow; no system fonts), with the subtitle area empty; ~1600x420.
- `menu_frame.png` (vertical ornate frame for the menu button column), `vignette_menu.png`, `class_plinth_glow.png`.

### `portraits/` (SVG, viewBox 0 0 256 256, painted-emblem style consistent with the icons)
`knight.svg`, `mage.svg` (heroes, used on HUD and save slots), NPCs: `blacksmith.svg` (burly smith, leather apron, soot),
`merchant.svg` (hooded traveling trader with a gold earring), `elder.svg` (old sage, white beard, aether-lit eyes),
`mystic.svg` (aether seer, veiled, glowing sigil on the brow), `captain.svg` (guard captain in a plumed helm),
`stranger.svg` (hooded silhouette, used for unknown speakers). Busts with a dark vignette background and an ornate frame edge.

### New icons (SVG, same style and conventions as bh-001's `icons/`)
- `icons/items/`: tiered variants `sword_2`, `sword_3`, `greatsword_2`, `greatsword_3`, `axe_2`, `axe_3`, `spear_2`, `spear_3`,
  `dagger_2`, `dagger_3`, `bow_2`, `bow_3`, `staff_2`, `staff_3`, `wand_2`, `wand_3` (2 = refined steel with engraving,
  3 = runed/ancient-tech with faint aether channels), `shield_2` (tower shield), `shield_3` (round sigil buckler),
  `helm_plate_2`, `helm_plate_3`, `helm_hood_2`, `helm_hood_3`, `armor_plate_2`, `armor_plate_3`, `armor_robe_2`, `armor_robe_3`,
  `inner_chain`, `inner_silk`, `gloves_plate_2`, `gloves_cloth_2`, `boots_plate_2`, `boots_cloth_2`, `ring_2`, `ring_3`,
  `amulet_2`, `amulet_3`, `charm_2`, consumables `potion_health_large`, `potion_mana_large`, `elixir_rejuvenation`,
  `scroll_return`, `antidote`, materials/currency `aether_shard`, `frost_crystal`, `storm_essence`, `shadow_silk`,
  `beast_hide`, quest items `quest_seal_key`, `quest_tablet`, `quest_crown_fragment`, `quest_letter`.
  Set pieces — **Aether Guardian** (knight): `set_guardian_helm`, `set_guardian_armor`, `set_guardian_gloves`,
  `set_guardian_boots`, `set_guardian_shield`; **Starbound Sage** (mage): `set_sage_hood`, `set_sage_robe`,
  `set_sage_gloves`, `set_sage_boots`, `set_sage_staff`. Aether uniques: `aether_sword`, `aether_greatsword`,
  `aether_staff`, `aether_wand`, `aether_ring`, `aether_amulet` (prismatic cyan-white energy, crystal motifs).
- `icons/status/`: `poisoned`, `slowed`, `silenced`, `weakened`, `armor_broken`, `windswept`, `empowered`, `fortified`,
  `overcharged`, `resolute`, `badly_hurt`.
- `icons/ui/` (48–64 px glyphs, simple, single-color friendly): `gold`, `aether`, `level`, `xp`, `sort`, `filter`, `search`,
  `lock`, `favorite`, `junk`, `trash`, `split`, `compare`, `settings`, `save`, `load`, `map`, `teleport`, `quest`, `talk`,
  `shop`, `repair`, `buyback`, `back`, `close`, `plus`, `minus`, `check`, `warning`, `info`, `skull`, `crown`.

## Evidence

`work/lemondev/bh-002/evidence/ui_art/`: contact sheets at native and at 0.5x of every raster family on a dark background;
9-slice test renders (each panel/button stretched to 3 sizes, e.g. 300x120, 800x500, 1400x220, composited with PIL) to prove
the margins; SVG contact sheets at 48 px and 128 px (reuse `godot_render/` or `render_evidence.py`); a `validation.txt`
(every file exists, sizes, alpha present, SVG validity per bh-001 rules); `ui_art_manifest.json` complete. Include an honest
self-review of what looks weakest and fix the worst before reporting.
