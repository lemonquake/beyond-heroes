# bh-029 textures + UI art brief (Builder T1)

You make the new textures and 2D art for the Godot 4.7 game Beyond Heroes (`A:\Python\beyond-heroes`) for its new
island, **Zarael** — read `work/lemondev/bh-029/contract.md` first (story, theme, material names, house rules).
Everything is procedural Python (numpy / scipy / PIL; SVG for portraits): deterministic, no third-party images.

## 1. Texture sets (`tools/textures/gen_zarael_textures.py`)
Follow `tools/textures/texlib.py` and `gen_textures.py` exactly (1024² tileable, outputs
`game/assets/textures/<set>_albedo.png`, `<set>_normal.png`, `<set>_rough.png`; look at how `sunstone`, `basalt`,
`marble`, `fungal_stone` are made and how the normal/rough maps are derived). Copy a sibling `.import` for each new
PNG (change paths, delete the `uid=` line). Albedo must stay **mid-value and fairly desaturated** — the game tints and
lights them; earlier sets that came out neon-bright had to be darkened. Sets:

| set | look |
|---|---|
| `glyph_stone` | pale weathered limestone blocks (running bond, irregular), every third course a carved band of stepped-fret / abstract glyph relief (normal map carries the carving), chipped arrises, faint lichen. Tiles at 2 m in the world. |
| `jade_stone` | polished green jade slabs with cloudy veins and fine gold-wire inlay lines between slabs. |
| `obsidian` | black volcanic glass flags with conchoidal fracture highlights and thin molten-copper seams in the joints (low albedo; low roughness on the glass). |
| `lime_plaster` | lime plaster over stone: trowel strokes, hairline cracks, flaked patches showing stone; neutral warm off-white (the game tints it ochre or red). |
| `terrace_paving` | fitted irregular paving stones with an occasional square glyph tile and a thin inlaid wire line every few metres; grit in the joints. Used for plazas and terrain paths. |
| `turquoise_mosaic` | small irregular turquoise/teal tesserae with dark grout, a few shell-white and red pieces. |
| `jungle_floor` | jungle ground: dark loam, broad fallen leaves, roots, seeds, moss patches (terrain). |
| `red_clay` | packed red-ochre clay ground with cracks, pebbles and dry grass tufts (terrain). |
| `blackwire_soil` | corrupted ground: cracked dark red-brown earth with thin violet-red veins in the cracks and glassy grit (keep the veins thin and dim — the game adds emission elsewhere). |
| `cliff_ochre` | layered ochre/red sandstone cliff, horizontal strata, erosion streaks (terrain rock). |

Evidence: a contact sheet `work/lemondev/bh-029/evidence/textures/sheet.png` (each set tiled 2x2, plus a lit sphere/
plane preview if easy) and `textures.md`.

## 2. Portraits (`tools/ui_art/bh029_portraits.py`)
Match the existing portrait style: read `tools/ui_art/bh019_portraits.py` / `bh018_portraits.py` and look at
`game/assets/ui/portraits/*.svg` (same frame, size, palette treatment). Make SVGs (+ `.import` copied from a sibling):
- `terax.svg` — Terax, Warden of Agdao: a powerful veteran in jade-and-obsidian armour with a tall feather crest, a
  bronze gauntlet wound with glowing gold wire on one arm, a scar, calm hard eyes. Neutral presentation (no gender cues
  needed).
- `wirekeeper.svg` — Wirekeeper Halvessa Orn: older engineer-priestess, turquoise mosaic collar, wire-wound headdress,
  spectacles of polished crystal.
- `ilsa.svg` — Captain Ilsa Rhondar of Agdao's ship: weathered sea captain, braided hair, sea coat, copper earring.
- `agdao_porter.svg`, `agdao_vendor.svg`, `agdao_elder.svg` — Agdao townsfolk (a porter with a tumpline, a market
  vendor with a woven headwrap, an elder with a cane and feather stole).

## 3. The Zarael atlas (`tools/ui_art/bh029_atlas.py` → `game/assets/ui/atlas/zarael_atlas.png`)
Read `tools/ui_art/salmonan_atlas.py` if present (grep for `salmonan_atlas`) and match the Salmonan atlas's painted
style and size (2000 x 1700 px, no text, no roads baked in). Zarael: an island elongated west→east. **Agdao** on the
south-west coast (a harbour and stepped hillside), the **Coilwood** jungle north and east of it, the **Glasswire Barrens**
(red cracked plain with violet glints) east of the jungle, a deep **gorge** running north–south across the island's
middle with the **Bridge of Death** crossing it, and the **Heart Citadel** on high ground east of the gorge. Mountains on
the north coast, sea around. Report the pixel centre of each region in the 1000 x 850 atlas coordinate space (half the
art size) so the Orchestrator can place the maps.

## Rules
- Write ONLY: your scripts, the listed PNG/SVG files + their `.import`, your evidence dir, scratch under
  `work/lemondev/bh-029/scratch/t1/`. No game code, no Godot on `game/`.
- No lettering in textures or the atlas. No Filipino or real-culture names.
- Final message: list every file written, the atlas region centres, and anything the Orchestrator must know.
