# Beyond Heroes icon inventory — 27 October 2026

Observed from the live Godot database and actual UIArt resolution. Initial baseline ran with Godot 4.7.2 and empty stderr. A later extended dump overlapped border integration and encountered an unregistered IconBorders class; re-import is required before final runtime validation.

## Content counts

| Family | Entries |
| --- | ---: |
| attributes | 6 |
| classes | 16 |
| elements | 9 |
| items | 1630 |
| signature_traits | 12 |
| skills | 95 |
| status | 111 |
| tempo_classes | 5 |
| tempo_skills | 54 |
| tree_nodes | 278 |
| ui | 32 |
| upgrades | 12 |
| weapon_types | 14 |

## Artwork plan

519 new painted icons across 15 equal 6 × 6 sheets. Each cell has its own exact row/column description in plan.json; original images remain in sheets/. Existing 1536 PNG item renders remain in use, and their baseline SHA-256 hashes are recorded in registry.json.

All 457 existing SVG icon routes are covered, including currently unused files. Four hero skills previously reused a different skill artwork: Gravity Pull, Spike Tentacle, Dark Arts and Mana Siphon. All 54 Tempo skills now receive distinct identity routes, including 22 previously falling back to hero skill icons. Twelve advanced class crests, twelve signature traits and twelve weapon upgrades receive new artwork.

The base classes, passive/talent nodes, skill upgrades, statuses, attributes, elemental identities and interface markers are included. Repeated ranks use live overlays or textual rank labels rather than a separate baked image. Statuses with the same visual effect intentionally share a symbol; potion effects use their potion artwork.

## Reproduction

```text
python tools/official_icons.py plan
# Copy built-in image outputs to output/official-icons-20261027/sheets/sheet-01.png ... sheet-15.png
python tools/official_icons.py pack
python tools/official_icons.py pack --check
python tools/official_icons.py audit
```

Packaging only crops exact equal cells and resizes to 256 × 256. It does not synthesize artwork or remove transparency. The packaged manifest records route mapping, skill and Tempo identity mapping, upgrades, signatures, source image/cell/box and hashes.

## Remaining validation

Generation, runtime routing, import, visual review, target builds and final packaged audit are owned by the integration lead. No final verification or build is claimed by this scan.
