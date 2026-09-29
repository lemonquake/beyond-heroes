# Weapon art contract

Baseline: 8cde5d1. Pass budget: eight; initial build is pass 1.

Frozen before first candidate render: add ten distinct designs for each of bow,
crossbow, dagger, sword and axe (50 new item bases), with their own held meshes
and matching inventory icons. Existing bow IDs must retain stats/save compatibility
while receiving improved silhouettes. All new items join normal level-gated loot,
crafting and shop pools through DataItems.bases; no special fixed rarity is required.

Geometry uses existing Blender mesh and Godot material pipeline, origin at grip,
long axis Blender +Z / Godot +Y. Crossbow type and pose owned by mechanics builder.
Each family must show ten different silhouette/construction treatments (not color
swaps). Required review: fixed studio contact sheet, actual runtime equipment
captures, import availability, nonzero geometry and correct range of dimensions.
Budget: <= 12,000 triangles per individual weapon; icons 128 px RGBA, source 256 px.
Material variety must remain coherent with existing game's medieval fantasy art.

Benchmark: existing project assets at baseline for local regression; commercial
reference unavailable, so commercial superiority gate remains UNVERIFIED.
Builder self-checks cannot grant independent acceptance. Integration owned by root.
