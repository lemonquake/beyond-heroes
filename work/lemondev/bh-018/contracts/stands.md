# bh-018 contract — shop stands and crafting stations (environment kit)

The user rejected the bh-017 Merchant Rows: seven identical striped market awnings in a grid, trade objects hung from
iron sign-poles, lantern stands scattered like clutter. Every shopkeeper now gets **their own purpose-built stand** that
tells you the trade at a glance *from the game camera*, without any lettering. This is the art the user will judge; put
real design effort into silhouette, storytelling props and material contrast.

## Hard rules (from earlier user feedback on this game)
- Medieval, hand-made, weathered, lived-in. No text or letters anywhere, no neon/emissive outlines, no flat colour
  rectangles or UI-looking placards, no striped awnings, no structure without a purpose, no sign-poles with hanging
  objects. The *trade's own goods displayed on and around the stand* are the sign.
- Each stand's **roof shape, roof material and silhouette must differ clearly** from every other stand (the camera sees
  mostly roofs). Vary: lean-to, conical tent, hexagonal pavilion, gabled slate, copper sheet, domed kiosk, wagon hoop
  cover, wall tent, canvas fly ...
- Nothing a shopkeeper's head pokes through; nothing floating; everything touches the ground or hangs from something.

## Technical contract
- Blender 5.2 environment kit (`tools/blender/environment/kit.py`, read `README.md` there and look at `assets_town.py`,
  `assets_town2.py`, `assets_guildhouse.py` for idioms). Register with `@asset("<name>", "market")`. `import market_common`
  first (it adds the extra `BH_*` materials: ClothGreen/Ochre/Teal/Cream/Black, Velvet, Leather, Copper, Verdigris, Slate,
  GemRed/Amber/Aqua/Green/Gold/Violet, Coals, plus Brass/Silver/Paper/Rope/Bottle). Use **only** `BH_*` names from
  `kit.MATERIALS` (the game swaps materials by name; vertex tint is ignored in game, so colour must come from the
  material choice).
- Metres, Z-up, origin at the bottom centre of the footprint, `return dict(recenter=False)`. **Front (customer side)
  faces Blender -Y** (Godot +Z). Stay inside the given footprint (W along X, D along Y); height ≤ 5 m (a chimney may reach 6).
- **Game camera**: fixed, from the front (-Y side), pitched 54° down, 10–24 m away, night lighting (dark blue ambient,
  warm lantern pools). Design for that view: the front and the displayed goods must read from above-front.
- **Sockets** (`k.sockets.append((name, (x, y, z)))`):
  - `npc` — floor point (z = 0) where the shopkeeper stands. Keep a free 0.9 m circle. The shopkeeper is 1.85 m tall and
    must be **visible from the camera**: from the head (z 1.8) the ray toward the camera rises 1.38 m per metre toward -Y;
    it must not hit the roof. (Lift the front edge of the roof, keep the npc near the front, or stand them in the open.)
    Roof ≥ 2.4 m above the npc spot.
  - `customer` — floor point in front where the hero stands to trade (clear, reachable, ~1.2–1.8 m in front of npc).
  - `light_a` (and optionally `light_b`) — where a warm point light goes (inside a lantern / over the goods).
  - Station/forge extras where listed: `use` (floor point where the hero uses the station), `flame` (coal bed / brazier
    fire), `smoke` (chimney top).
- **Collision**: `k.col_box` / `k.col_mesh` for counters, walls, posts, barrels, wagon body — so heroes walk around, not
  through. Leave the npc spot, the customer spot and a walkable path between them free. No collision above 2.2 m needed.
- Budget ≤ 15k triangles per stand. Deterministic (use `k.r`).
- Build: `"C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b --factory-startup --python
  tools/blender/environment/build_assets.py -- <names>` → `game/assets/environment/<name>.glb`.
- Evidence: EEVEE renders of each stand — (1) the game view: camera at -Y, 54° down, ~9 m, lens ~45 mm equivalent, dim
  blue night ambient + a warm point light at `light_a`; (2) a 3/4 daylight view. Save to
  `work/lemondev/bh-018/evidence/stands/<name>_game.png` and `<name>_34.png` (≥ 960 px wide). You may reuse
  `render_lib.py` helpers. Look at your own renders and fix what reads badly before you finish.
- Do not edit game code (`game/src/**`), other builders' files, `kit.py`, `market_common.py` or `build_assets.py`.

## Who stands where (the Orchestrator places them; you only build)
Malasugue (Merchant Quarter), Olivar (Market Row), Wyman Outpost (Quartermaster Row).
