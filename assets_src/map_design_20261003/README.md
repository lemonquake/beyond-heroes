# Map design asset library

Downloaded on 3 October 2026: **114 distinct GLB source objects** by Kenney, licensed CC0-1.0.
48 nature, 26 furniture, 20 coastal/harbour, and 20 additional dungeon objects (16 graveyard + 4 dungeon kit).

This library is for Claude Code's implementation of Salmonan, Zarael/Agdao, interiors and dungeon atmosphere.
Read [the complete brief](../../docs/CLAUDE_MAP_DESIGN_AND_DUNGEON_ASSETS.txt), [object descriptions](ASSET_DESCRIPTIONS.txt),
[the CSV catalog](asset_catalog.csv) and [the manifest](manifest.json).

## Verification

All 114 pass their recorded static source policies, have verified canonical package hashes,
and have self-contained GLB buffer/image dependencies. Source geometry spans 16–2282 triangles;
the model files total 2,545,532 bytes (~2.43 MiB).
17 models contain multiple meshes and require careful preparation for the current batching loader.
This proves source suitability and file integrity. Engine integration, artistic adaptation and FPS remain pending.

## Contents

- `canonical/.game-dev/packages/`: selected immutable models with provenance, hashes, policies and receipts.
- `licenses/`: original license documents, including permission for commercial use.
- `downloads.json`: exact original creator ZIP URLs and SHA-256 hashes.
- `manifest.json` and `asset_catalog.csv`: exact model/package paths, descriptions and intended use.
- `requests/` and `evidence/`: curation settings, inspections, validation and verification results.
- `previews/` and `contact_sheets/`: creator previews, labelled with actual source geometry counts.
- `sources/`: full downloaded archives and alternate formats, kept locally and Git-ignored.

The source previews have not been recoloured to the game. Use shared timber/stone/fabric materials,
correct scale/pivots, and a lit material treatment before integration. Do not import modern appliances.
Do not rename or overwrite existing environment objects. Unused models should stay out of runtime exports.

## Reproduce

```powershell
python tools/download_map_asset_sources.py
python tools/curate_map_assets.py --cli "<installed game-dev dist/cli.js>"
python tools/document_map_asset_curation.py
```

The downloader checks archive hashes and refuses to overwrite differing existing files.
The local Windows wrapper works around directory-fsync EPERM in game-dev 1.0.2 without changing installed tools.
The final numbered inventory is embedded in the Claude brief; only that text file is needed to start the handoff.
