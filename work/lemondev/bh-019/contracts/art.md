# bh-019 art contract — Lape the Ancient, practice dummies, the Vault

Same hard rules and technical contract as `work/lemondev/bh-018/contracts/stands.md` (read it fully: medieval, weathered,
no lettering, no neon, no sign-poles, nothing floating, front faces Blender -Y, sockets, collision, game camera, evidence).
Environment assets go in `tools/blender/environment/assets_bh019.py` (register with `@asset("<name>", "market")`,
`import market_common` first). Evidence to `work/lemondev/bh-019/evidence/art/`.

## 1. stand_lape — "Lape the Ancient", appraiser of relics (Malasugue). Footprint 3.8 × 3.0, height ≤ 4.2.
Lape is a mysterious, very old black-hooded figure with a huge magic staff. Players bring him up to three items; he
appraises them and offers one of three special-crafted pieces of equipment, or gold. His stand must feel **ancient and
uncanny**, unlike every other stand (see the bh-018 renders in `work/lemondev/bh-018/evidence/stands/`):
- Two **gnarled, twisted dead-wood poles** (BH_Bark / BH_WoodDark) leaning slightly, a **sagging, tattered drape** of dark
  charcoal cloth (BH_ClothBlack, torn hems, a few holes) slung between them and pegged back to the ground with rope — an
  irregular, organic silhouette, no straight roof edge.
- A low, heavy **appraisal table** of black oak with a worn velvet cloth (BH_Velvet); set into its front edge, **three
  brass-rimmed offering dishes** in a row (BH_Brass rims, dark velvet beds) — the three trade slots, clearly readable from
  the camera. A **large brass balance** at one end, a lit candle cluster (BH_Candle + BH_Flame) at the other, an
  **open ancient tome** and a magnifying loupe.
- Behind the table, a crooked shelf/cabinet of dusty relics: an old dented helm, a sealed iron casket, a bundle of
  scrolls, an antlered beast skull (BH_Bone), a tarnished crown, a few jars; one small glowing relic (BH_GemViolet) as the
  only magical accent. A hanging brass **censer** on a chain from a pole (small).
- Ground: a threadbare round rug (BH_ClothRed or BH_Velvet), a few scattered old coins, a stool.
- Sockets: `npc` behind the table, centre (Lape is 1.9 m and his staff reaches 2.6 m: keep ≥ 2.8 m clear above the npc
  spot and a 0.9 m circle free), `customer` ~1.6 m in front of the table, `light_a` at the candles, `light_b` optional.
- ≤ 15k triangles. Collision on the table, shelf, poles.

## 2. practice_dummy — a straw training dummy (one per safe town). Footprint 1.3 × 1.3, height ~2.0.
A sturdy vertical post in a **cross-shaped timber foot** (four braced feet on the ground), a **straw-stuffed sack body**
(BH_Thatch / BH_Cloth, rope bindings) on the post, a horizontal **arm beam** through the shoulders, a **dented iron
practice helm** on the sack head, a **battered round wooden shield** strapped to the left arm, a few arrows stuck in the
torso, straw tufts poking out, a rough painted target circle on the chest done as a **separate darker cloth patch**
(no emissive). Must read instantly as "hit me" from the camera.
- **Two objects in the GLB** (the game wobbles the body when hit): `dummy_base` (the foot + the bottom 0.35 m of post)
  and `dummy_body` (everything above, parented or not — export as a separate mesh node named exactly `dummy_body`,
  with its **origin at the top of the base (0, 0, 0.35)** so a rotation about its origin tilts it like a spring post).
  If the kit merges everything into one mesh, extend it minimally *inside your file* (e.g. build the body as a second
  asset `practice_dummy_body` with origin at its pivot) and say so.
- Sockets: `use` at (0, -1.6, 0) (where a hero stands to hit it), `hit` at the chest centre (for damage numbers).
- Collision: a box/cylinder around the post and foot (≈ 0.5 m wide) so heroes cannot walk through.
- ≤ 4k triangles.

## 3. stand_vault — the Hero's Vault (one per safe town; shared storage across all of the player's heroes).
Footprint 3.0 × 2.4, height ≤ 3.4. A **squat stone strongroom**: heavy ashlar block (BH_Stone / BH_StoneDark) with a
slightly battered base, a lead/slate roof slab (BH_Slate), and in its front face a **big round iron vault door**
(BH_Iron) — thick rim, radial bolts, a spoked wheel handle in the middle, massive hinges on one side — set slightly
recessed in a stone surround. Two **iron-bound treasure chests** (BH_WoodDark + BH_Iron + a little BH_Gold coin spill)
in front at either side of the door, one with its lid ajar, a lantern on a wall bracket (light_a), iron bars on a small
high window, moss at the foot. Reads as "safe storage" instantly.
- Sockets: `use` ~1.5 m in front of the door, `light_a` in the lantern.
- Collision on the whole block and the chests. ≤ 10k triangles.

## 4. Lape the Ancient — character model (tools/blender/characters/town_lape.py → game/assets/characters/lape.glb)
A townsfolk character built like the other `town_*.py` modules (same skeleton, same `TOWN_CLIPS` idle set so the game's
`idle`, `idle_look`, `idle_adjust` exist). Very tall and slightly stooped (~1.9 m), in a **floor-length black robe**
(near-black, charcoal hem slightly tattered) with a **deep pointed hood** that hides the face in shadow — only a long
**white beard** spilling from the hood and two faint pale eyes (small, BH_Emissive, subtle). Long sleeves hiding the
hands except bony fingers. A rope belt with small pouches, a pendant of an old key. He holds, in his right hand, a
**really big gnarled magic staff** (~2.6 m, taller than him by 0.7 m): twisted dark wood, the head a tangle of roots
cradling a **glowing violet orb** (BH_Emissive / gem), a few hanging charms and a tattered ribbon. The staff must be part
of the skinned model (on the right hand/`weapon.R`), and stay in the hand through the idle clips.
Build: `"C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b --factory-startup --python build.py -- lape`
(the `town_` prefix is auto-discovered; check `build_chars.py`). Evidence: a front and 3/4 render.
