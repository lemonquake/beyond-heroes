# Contract — enemy models (builders A, B, C)

Read first: `docs/LORE.md` (sections 3, 7, 8), `tools/blender/characters/README.md`, `char_knight.py` (a complete
example of the modeling DSL), `bh_body.py`, `bh_mesh.py`, `bh_skeleton.py` (`proportions()`), `bh_materials.py`.

## Deliverable per humanoid enemy

1. `tools/blender/characters/enemy_<id>.py` — a character module with:
   - `PROPS = proportions(scale, **overrides)` — body proportions (shared skeleton; only lengths change). Keep the
     standard bone names. Height comes from the proportions; the game can also scale the model (`model_scale` in
     `data_enemies.gd`, set by the orchestrator), so **model at the creature's true size** (goblin ~1.2 m, ogre ~3 m)
     and tell the orchestrator the final standing height.
   - `PALETTE = "<id>"` and `PALETTE_COLORS = {"BH_Name": (base_rgb_linear, metallic, roughness, emission_rgb|None,
     emission_strength, 1.0), ...}` — the enemy's own colours. Every material is exported as `BH_Name__<id>` and the
     game keeps these colours (only roughness/normal detail comes from the shared table). Available base names:
     `BH_Steel BH_DarkSteel BH_Gold BH_Leather BH_Cloth_Primary BH_Cloth_Secondary BH_Skin BH_Bone BH_Rust
     BH_Emissive BH_Shadow BH_WeakPoint BH_Wood BH_Hair BH_Aether BH_Fur BH_Flesh BH_Stone BH_Bronze BH_Horn BH_Ichor`.
     Colours are **linear** (Blender); keep albedo in a believable range (no pure black / white) so the game's lights
     read them. Emissives are the enemy's "eyes"/runes/embers: small, deliberate.
   - `CLIPS = [...]` — the attack/extra clips this enemy uses (listed below). All enemies automatically also get the
     base set (idles, locomotion, reactions, `death`, `death_back`, `death_fwd`, `death_crumple`, `revive`, `alert`,
     `taunt`, `charge_hold`, `cast_channel`, `block_loop`, `block_impact`).
   - `build(body)` — adds the parts. **The weapon(s) are part of the mesh**, rigidly weighted to `weapon.R` /
     `weapon.L` (socket frame: +Y = blade/shaft forward, +Z = back of the hand; see `bh_weapons.py` builders — you may
     call them or build your own unique weapon in socket space). Shields go on `weapon.L` facing outward (-Y in socket
     space per the existing shield builder).
   - optional `EXTRA_BONES` + `secondary(anim, frames)` for capes, tails, loincloths, chains (see the knight's cape).
2. Export: `cd tools/blender/characters && python3 build.py -- <id>` → `game/assets/characters/<id>.glb`.
   (`build.py` only rewrites `anim_meta.json` for heroes; do not pass `meta` or `all`.)
3. Preview evidence: `python3 preview_enemy.py <id> --iso` (rest, 4 views + gameplay camera) and
   `python3 preview_enemy.py <id> --clips <idle stance>,<main attack>,death_crumple --frames 0,0.45,1` →
   copy the PNGs to `work/lemondev/bh-003/evidence/enemies/`. **Look at every sheet you produce** and fix what reads
   badly (floating parts, weapon not in the fist, limbs through armor, unreadable silhouette at the iso camera).
4. A short section in `work/lemondev/bh-003/evidence/enemies/<id>.md`: final height, tri count, materials, clip list,
   distinctive features, known issues.

## Budgets

- Triangles: fodder/ranged 6k–12k, elites/brutes 10k–16k, boss ≤ 24k. The game camera sees enemies from ~20–30 m at
  a high pitch: **silhouette and big shapes matter most**; skip rivets that vanish at that distance.
- Parts must be rigid to one bone or smoothly weighted (use the body weight helpers); nothing may detach or float when
  animated. Check `death_crumple` and one attack in the preview.
- Export time per enemy should stay under ~2 minutes (vertex-AO bake is per vertex; don't exceed the budget).

## The roster (design brief — make each one unmistakable at gameplay distance)

`attack clips` are the names the game plays; they must be in `CLIPS`. Idle stance clip in brackets.

### Builder A — undead + construct (bone/verdigris palette, cyan-green grave-light eyes; see LORE)

| id | Look | Size | attack clips |
|---|---|---|---|
| `hollow_soldier` | Skeleton in a rotten garrison surcoat and a dented kettle helm; exposed ribcage and spine between armour pieces; rusted arming sword with notched edge; one pauldron missing; faint teal glow in the eye sockets. | 1.8 m, gaunt (thin limbs = bones) | `sword_1 sword_2 sword_heavy` [idle_1h] |
| `bonewarden` | Heavier skeleton in rusted half-plate; **its tower shield is its own coffin lid** (wood planks, iron bands, a nameplate) on the left arm; a heavy axe; helm with a broken visor; chains hanging from the belt. | 1.9 m, broad | `shield_bash axe_1` [idle_shield] |
| `grave_archer` | Hooded skeleton with a tattered moss-green hood and cloak, a bone-and-sinew longbow in the left hand, a quiver of black-fletched arrows; bare skull jaw. | 1.8 m, lean | `bow_release bow_draw_hold` [idle_bow] |
| `boss_warden` | **Morthar, the Hollow Warden**: a towering armoured knight whose ornate oath-plate is split open over a hollow, violet-glowing chest cavity; a cracked crown-helm with tall horn-like crest; a torn royal cape (cape bones); a huge greatsword with runes; the back of the armour carries a glowing rune (his weak point, `BH_WeakPoint`). | ~2.0 m model (the game scales ×2.2) | `boss_sweep boss_slam boss_charge cast_heavy boss_roar boss_summon` [idle_2h] |
| `aether_sentinel` | Ancient temple guardian of stone and bronze: blocky stone torso segments floating slightly apart with bronze bands, a glowing cyan Aether core in the chest (`BH_Aether`), a stone slab shield on the left arm and a bronze-headed maul; no face, just a visor slit with light. | ~2.0 m model (game ×1.25), massive | `gs_1 boss_slam cast_heavy` [idle_shield] |

### Builder B — Ashen Circle, corrupted, bandits

| id | Look | Size | attack clips |
|---|---|---|---|
| `ashen_cultist` | Ash-grey robes with ember-orange trim, a deep hood, a cracked ceramic **ash-mask**; one hand wrapped and charred; a short ritual staff topped with a burning brazier-cage (ember emissive); cords of burnt paper prayers. | 1.75 m | `cast_quick cast_area` [idle_staff] |
| `ashen_acolyte` | Lighter-built than the cultist: grey robe, bare head with ash-painted face, a long **censer on a chain** (ember glow) and a hymn-book; red sash. Must read as "support/healer" next to the cultist. | 1.7 m | `cast_quick cast_area cast_weapon` [idle_staff] |
| `ghoul_brute` | Huge hunched man bloated and twisted by grave-moss: grey-green skin (`BH_Skin` palette), moss growing on the back and shoulders, one arm swollen into a club of bone and flesh, torn trousers and a rope belt with a cleaver; tiny sickly green eyes. Forward-leaning hunch (use proportions + spine offsets in the mesh). | ~2.0 m model (game ×1.35) | `axe_2 boss_slam boss_charge devour` [idle_2h] |
| `shade_stalker` | Thin figure wrapped in smoke-black cloth strips (`BH_Shadow`), face hidden by a wrapped hood with two violet eye-slits, long curved daggers in both hands, cloth strips trailing from arms (extra bones optional). Must read as fast and wrong. | 1.8 m, very lean | `dagger_heavy dagger_1` [idle_dagger] |
| `bandit_cutthroat` | Road bandit: patched leather jerkin, a faded red scarf over the lower face, bandolier of throwing knives, a curved knife in the right hand and a short dagger in the left; bare arms with bandages. | 1.75 m | `dagger_1 dual_2 wand_1` [idle_dagger] |
| `bandit_marksman` | Bandit archer: wide-brim leather hat, green-brown hooded cape, bracer, a recurve bow in the left hand, arrow quiver on the hip. | 1.75 m | `bow_release bow_draw_hold` [idle_bow] |

### Builder C — greenskins, beast, Aether creature

| id | Look | Size | attack clips |
|---|---|---|---|
| `goblin_skulker` | Small, big-eared, big-nosed goblin with mottled olive skin, a scavenged dented helmet too big for it, a sack of loot on its back, a notched knife, and **fire-pots** (clay jars with a burning rag) on the belt. Long arms, bowed legs (proportions). | ~1.15 m | `dagger_1 dagger_2 cast_quick` [idle_dagger] |
| `orc_reaver` | Tall green-grey tusked orc raider: bone-and-leather armour, a spiked shoulder guard on one side, red war-paint across the eyes, topknot, a heavy two-bladed war-axe held in the right hand; Sulvane red cloth tied on the arm (mercenary token, see LORE). | ~2.0 m, broad shoulders | `axe_1 axe_3 axe_heavy war_cry` [idle_2h] |
| `ogre_crusher` | Enormous pot-bellied ogre with tiny head, underbite, patchy hair, a broken iron **slave collar with a hanging chain** (the orcs drive it), a tree-trunk club with iron bands; loincloth. Arms long enough to reach the knees. | ~3.0 m (model at true size) | `gs_1 boss_slam cast_heavy boss_roar` [idle_2h] |
| `dire_wolf` | **Quadruped** — see below. Big grey-black wolf with a ragged mane, pale eyes with faint Aether glint, scars. Shoulder height ~0.95 m, length ~1.9 m. | | own clips (below) |
| `aether_wisp` | **Floating Aether creature** — see below. A pale-cyan crystalline core inside three orbiting shard-rings and trailing light-ribbons. ~1.2 m tall. | | procedural in-game |

#### dire_wolf (quadruped pipeline, builder C owns `tools/blender/creatures/**`)

The humanoid skeleton cannot be used. Build a wolf armature (spine chain, neck, head, jaw, tail chain, four legs with
3–4 segments each), a skinned mesh (automatic or authored weights), and **baked in-place clips** with these exact
names (30 fps): `idle` (loop), `idle_look`, `walk` (loop), `run` (loop), `run_combat` (loop, same as run is fine),
`hit_light`, `hit_heavy`, `stagger_small`, `knockback`, `death`, `death_back`, `alert`, `wolf_bite`, `wolf_pounce`,
`wolf_howl`, `devour` (loop, feeding on the ground). Export `game/assets/characters/dire_wolf.glb` (Y-up glTF, one
glTF animation per clip, like `build.py`'s exporter). The wolf faces −Y in Blender (= +Z in Godot).

Write `game/assets/characters/creature_meta.json` with the same schema as `anim_meta.json`:
`{"fps": 30, "animations": {"wolf_bite": {"length": s, "loop": false, "hits": [[t0, t1]]}, ...}}` for **every**
wolf clip (hits for `wolf_bite` and `wolf_pounce` = the seconds where the jaws close / the body lands; lengths for all;
`ground_speed` in m/s for `walk`/`run`). The game uses these for timing.

#### aether_wisp (static model, animated in engine)

Export `game/assets/characters/aether_wisp.glb` with **separate named mesh nodes**: `core` (at origin, ~0.25 m
radius, `BH_Aether__aether_wisp`), `ring_1`, `ring_2`, `ring_3` (shard rings of 5–7 crystal shards each, radius
0.45–0.7 m, centred on the core; each ring a separate node so the game can spin it), and `ribbons` (3 thin trailing
light-ribbon strips hanging below, `BH_Emissive__aether_wisp`). Origin 0 = the creature's centre; the game floats it.
No armature.

## What the orchestrator does with your output

Imports the GLBs in Godot, sets `model_scale`, wires clips to the enemy AI, and adds runtime VFX (blood/hit
materials, deaths, decay). Report anything the orchestrator must know (heights, clip quirks) in your `<id>.md`.
