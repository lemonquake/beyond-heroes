# Procedural assets, shaders, and HUD/UI

## Procedural visual pipeline

For new assets in the guide's default mode, generate geometry, custom materials, and textures in code without external binary asset dependencies. Preserve user-supplied assets and established project constraints. Any departure from this procedural default belongs in the contract, not in a hidden shortcut.

1. **Geometry:** build indexed buffer geometry or the engine equivalent with purposeful silhouette, bevels/extrusions, secondary structures, normals/tangents, UVs, and useful vertex displacement. Primitives can be construction inputs; an unrefined pile of primitives is not the finished quality bar. Check topology, winding, bounds, and collision/render alignment.
2. **Shaders:** implement or extend the engine's material pipeline with appropriate custom shader logic: Fresnel response, metallic/roughness behavior, coherent lighting, and atmosphere/volumetric effects when the brief calls for them. Respect coordinate spaces, color space, shader version, precision, and target-device support. The PDF's Fresnel fragment is only an excerpt; it is not a complete PBR model or directly portable GLSL ES 3.00 implementation.
3. **Textures:** generate diffuse/base-color, roughness, and normal maps with deterministic math, noise, SDFs, Canvas 2D, or engine equivalents. Choose resolution from screen coverage and the memory budget. Verify normal encoding, seams, mipmaps, filtering, and distance behavior. “High resolution” is not permission for unbounded texture allocation.

Use a repeatable preview scene with fixed camera, light rig, background, exposure, and representative gameplay distance. Inspect multiple views and near/far states. Capture actual runtime output after resources are ready. Check shader errors, missing maps, aliasing, overdraw, and resource disposal alongside appearance.

## AAA visual comparison criteria

Use appropriate accessible commercial snapshots, as in the guide's examples of Homeworld, Star Citizen, and Cyberpunk 2077. Match the requested art direction; do not force photorealism onto a deliberately stylized game. A named title supplies neither an image nor an automatic pass.

| Criterion | Evidence to inspect |
| --- | --- |
| Silhouette complexity | Distinct readable form, intentional proportions and secondary detail at gameplay distance; no unfinished primitive assemblage |
| Surface micro-detail | Normal/roughness variation, specular response, coherent material scale and believable transitions |
| Lighting depth | Material-light interaction, appropriate self-shadowing and ambient occlusion, readable depth rather than flat color |
| Cohesion | Consistent palette, detail density, shape language, lighting, and fit with the project's style guide |

Use these as observations in the binary comparison, not four numerical ratings. A polished isolated render cannot certify the assembled game's visual quality, gameplay, or performance. Limit any commercial-quality claim to the criteria, scene, and evidence actually compared.

## Advanced HUD/UI rules

The guide's default HUD has spatial depth, micro-interactions, layered translucent/glass panels, corner details, meaningful telemetry, status indicators, and a clear typographic grid. In that mode, generic flat solid rectangles with no hierarchy/depth fail the visual gate. Where the user explicitly wants a flat/minimal style, record that override and judge against an appropriate benchmark; do not add decorative clutter to defeat the brief.

Bind UI to game state through decoupled events, selectors, or snapshots. UI reads state and emits user intentions; it does not directly mutate simulation internals. Coalesce high-frequency updates, reserve numeric field width, batch reads/writes, and favor compositor-friendly animation where supported. Demonstrate no visible layout shift in representative state transitions and no frame-budget failure caused by layout/reflow. Unsubscribe and release resources on teardown.

Test relevant HUD states: normal play, low health/resources, cooldown/reload, damage/status changes, menus, pause/resume, restart, disabled/unavailable actions, and error/empty states. Every visible control must perform its stated action. Validate pointer, keyboard, and controller input when those are target inputs, including focus visibility and input capture during pause.

Inspect 1080p and 4K plus the target device size. Scale anchors and safe areas without clipped text or overlaps. Use readable sentence/title case for important labels, sufficient contrast over moving backgrounds, and redundant cues for color-coded status. Respect reduced-motion needs. Decorative glass and telemetry must not obscure gameplay or turn into tiny unreadable text.

Use direct labels: Play, Game Setup, Shop, Pause, Resume, Restart, Team, Match Results. Avoid Tactical, Operations, Deploy, Requisition, and Operator as interface labels. Avoid slogans such as “Take a breath,” “Every shot matters,” and “Your arena, your rules.” Funny bot names are an explicit exception to the otherwise plain wording preference.

Keep development/benchmark details in the verification report, not in the player's HUD unless the product is specifically a diagnostic tool.
