# Contract — UI art: tier emblems, guild banners, portraits (builder F)

Read first: `docs/LORE.md` (sections 5, 6, 8 — tier table, guilds, people, colour rules), `tools/ui_art/bh_svg.py`,
`tools/ui_art/portraits.py`, `tools/ui_art/icons_crests.py`, `tools/ui_art/build_all.py`. Stay inside the existing
ThorVG-safe SVG subset (gradients + paths; Godot rasterizes these SVGs at import). Put new generator code in
`tools/ui_art/bh003_*.py` (you may import the existing modules; do not edit them). Output only to the folders below.

## 1. Tier emblems — `game/assets/ui/tiers/tier_<x>.svg` (x = e, d, c, b, a, s, ss, sss), viewBox 0 0 128 128

One emblem per hero tier; each must be recognisable at **28 px** on the HUD and look rich at 128 px on the character
sheet. Each contains its **letter(s)** (E, D, C, B, A, S, SS, SSS) legibly — bold, centred, high contrast outline.

| tier | material / shape (from LORE) |
|---|---|
| E | Iron ring-shield: dark iron disc with rivets, dull grey |
| D | Bronze kite shield |
| C | Silver crest with one small star above |
| B | Gold laurel shield: gold shield wrapped by laurel branches |
| A | Azure star: an eight-point azure-blue star with silver edge |
| S | Crimson sunburst: crimson and gold rays |
| SS | Twin moon: two crescent moons, violet-silver, over a dark star field |
| SSS | Aether crown: radiant prismatic cyan-white crown with light rays (the rarest; it should feel special) |

Progression must read at a glance: plainer/darker at E, increasingly ornate and luminous up to SSS.
Also `tier_unranked.svg`: a simple hollow grey ring with a dash (for heroes who have not joined a guild).

## 2. Guild banners — `game/assets/ui/guilds/`

- `swordfin_banner.svg` (viewBox 0 0 256 384): hanging swallow-tailed banner, deep sea-blue cloth, **a silver
  swordfish (marlin) leaping over two crossed blades**, silver trim, motto ribbon at the bottom reading
  "STRIKE FIRST. STRIKE TRUE." (text as paths or `<text>` with a common serif font; if `<text>`, keep it short and
  large).
- `lantern_banner.svg` (same size): dusk-violet cloth, **a golden lantern holding an eye-shaped flame**, gold trim,
  motto "WE KEEP THE LIGHT".
- `swordfin_crest.svg` / `lantern_crest.svg` (viewBox 0 0 128 128): the same symbols as compact round crests for the
  HUD / character sheet / name plates.
- `swordfin_banner.png` / `lantern_banner.png` 512×768 raster versions (for 3D cloth banners in the guild halls; use
  the existing raster helpers in `tools/ui_art/rast.py` / `build_raster.py` if suitable, otherwise render the SVG with
  any available rasteriser in Python — cairosvg is NOT guaranteed; PIL drawing of the same design is acceptable).

## 3. NPC portraits — `game/assets/ui/portraits/<id>.svg` (viewBox 0 0 256 256, same style as the existing ones)

New people of Malasugue (see LORE §6 for who they are; show their role in costume and props):

| file | person |
|---|---|
| `innkeeper.svg` | Pilar Abucay, innkeeper — middle-aged woman, headscarf, apron, warm smile, tavern lamplight |
| `bard.svg` | Ciro Balintad, bard — young man, feathered cap, lute neck visible |
| `fisher.svg` | Old Tasyo — very old fisherman, wide woven conical hat, deep wrinkles, sea-grey eyes |
| `veteran.svg` | Venna Kail — retired Class A heroine, scar across the brow, short grey hair, azure star pin |
| `swordfin_master.svg` | Commander Rhea Talvanne — stern woman, blue coat, silver swordfish pin, spear shaft |
| `swordfin_quartermaster.svg` | Dax Mercado — burly bearded man, ledger and blue sash |
| `lantern_master.svg` | Archivist Oren Vale — elderly scholar, violet robes, spectacles, small lantern light |
| `lantern_scribe.svg` | Lio Sanvar — young scribe, ink-stained, quill behind the ear, violet |
| `netmender.svg` | Nena Lagdameo — weathered woman, shell earrings, net over the shoulder |
| `cartographer.svg` | Ibarra Quell — middle-aged man, magnifying lens, rolled maps |
| `widow.svg` | Mirasol Hald — woman in mourning grey, dark hair, a soldier's token on a cord |
| `keeper.svg` | Keeper Tomas Dalisay — shrine-keeper, shaved head, prayer beads, bestiary tome |
| `refugee.svg` | Yusra Ven — young woman, hooded travel cloak, ash on the cloak (from Tambakol) |

Faces vary (age, skin tone from the existing SKIN palettes, hair, jaw); none may look like a recolour of another.

## Evidence

Contact sheets (PNG) of all emblems (at 28 px and 128 px), banners and portraits in
`work/lemondev/bh-003/evidence/ui_art/`, plus `README.md` listing files. Look at them and fix anything unreadable
(especially the letters at 28 px).
