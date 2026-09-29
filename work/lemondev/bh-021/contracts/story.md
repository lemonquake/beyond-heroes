# bh-021 — The Forsaken Hero: new main story, cutscenes, legends

Author request (29 Sep 2026): redefine the storyline and main quests; overhaul the starting quest and what follows.
The hero is ordered to **Wyman Outpost** to retrieve something, then to **Olivar** to meet **Paul David**, a comrade of
**Aljay, the Forsaken Hero** and **Roydo, the Righteous Hammer**. All three are **Class SX** (above SSS), level 200+, with
special effects on their names and ranks. Paul David gives the quest to defeat a **commander of the Forsaken army** that
abducted Aljay. While Paul David speaks of Aljay and Roydo the game shows their epic models (Aljay: black + crimson
dragon-like armour, blood-red aura, giant lance; Roydo: holy hero, giant hammer). Aljay was consumed by darkness but his
heart never faltered and he fought on for Malasugue; he, Roydo and Paul David were betrayed. Very cinematic; the
Aljay/Roydo cutscene cannot be skipped as a whole, only scene by scene. Real textures, real models, custom animations.

Names supplied by the author and used as given: Aljay, Roydo, Paul David, Wyman Outpost, Olivar, Malasugue.
Every other new name is invented (no Filipino words — standing user rule).

## 1. Lore (added to docs/LORE.md §10)

**Class SX — "Beyond".** The rank beyond heroes. The Accord minted it once, for three people, and then struck it from
the Registry. Emblem: a split crown with a rising blade of light between the halves, crimson-to-gold.

**The Dawnbreakers** — Aljay, Roydo and Paul David, three heroes of Malasugue who climbed past SSS.

| | Aljay, the Forsaken Hero | Roydo, the Righteous Hammer | Paul David, the Tempest Blade |
|---|---|---|---|
| Rank / level | Class SX · Lv 287 | Class SX · Lv 264 | Class SX · Lv 251 |
| Look | Black + crimson dragon-scale plate, horned dragon helm, glowing red eye-slits, tattered crimson cape; blood-red aura | White-gold holy plate, sunburst pauldrons, white tabard, braided beard, sun-crested helm; golden light | Weathered storm-blue long coat over mail, grey at the temples, scar, longsword at the hip; a black chain-brand on his sword hand |
| Weapon | **Dusk-Piercer**, a 3.4 m lance of black steel and Tyrant bone, crimson veins | **Dawnmaul**, a giant warhammer with a sun-disc head | **Stormwake**, a long straight blade with an azure edge |

- **Twelve winters ago — the Night of Black Wings.** A Sulvane war-Tyrant, **Vharzul the Dusk Tyrant**, fell on Malasugue.
  Aljay drove his lance through its heart. Its blood — the wrath of the Age of Wrath — poured into him. His armour
  fused with its black scales; the red aura never left him. The darkness wanted him to burn the world. **He used it to
  guard Malasugue instead**, for nine winters.
- **Three winters ago — the Winter of Chains.** High Registrar **Orsolan Vey** of the Accord feared what Aljay carried
  and sold the Three to the **Forsaken Legion** (knights who forsook the oath of the Binding and serve the Pact of
  Wrath's Rekindling; they hunt "wrath-bearers" to wake the Tyrants). The Registry ordered the Three to the **Weeping
  Causeway** in Reedwater Marsh to meet an orc war-host. The Accord's own knights turned their sealing bolts on Aljay.
  **Kethrax, Chain-Marshal of the Forsaken**, rose from the marsh with his Legion. Roydo held the causeway alone.
  Kethrax bound Aljay in Tyrant-chains; Aljay broke his lance in Kethrax's chest as he was dragged under. Paul David's
  sword hand was branded with a chain-seal; Roydo's light sank into the black water. With the Three gone, the Ashen
  Circle struck the Forgotten Temple that same winter — Morthar was hollowed holding it alone.
- **After.** The Accord declared that Aljay had turned Forsaken — "the Forsaken Hero" — and struck all three from the
  Registry; the songs were forbidden. Paul David lives quietly by the lake in Olivar. His blade has not left its
  sheath since: Kethrax's brand forbids it while Kethrax lives. Roydo's fate is unknown ("the Righteous Hammer does not
  drown"). Aljay lives, chained in the Legion's **Black Spire** across the sea — every night he breaks their chains,
  and every night they forge more.
- **Now.** A Wyman scout pulled the lance's broken tip — the **Dusk-Piercer Shard** — out of the marsh. It glows while
  its master lives. Kethrax has come back to the marsh to hunt for it.

## 2. Main quest chain (Objectives.CHAIN)

| # | id | Title | Step | Where / who | Done flag |
|---|---|---|---|---|---|
| 1 | awaken | The Waypoint's Choice | Speak with Elder Maelis by the hearth. | Malasugue, maelis | mq_maelis_orders |
| 2 | gate | The Barred Gate | Ask Captain Hald to open the South Gate. | Malasugue, hald | south_gate_open |
| 3 | wyman | Orders for Wyman | Take the Fen Road to Wyman Outpost; ask Sir Aldric Vane for the sealed reliquary. | Wyman, aldric | mq_shard_taken |
| 4 | olivar | The Swordsman by the Lake | Bring the Dusk-Piercer Shard to Paul David in Olivar. | Olivar, paul_david | mq_three_told |
| 5 | marsh | The Marsh Gate | Return to Wyman Outpost; Sir Aldric opens the Marsh Gate. | Wyman, aldric | mq_marsh_gate_open |
| 6 | kethrax | The Chain-Marshal | Defeat Kethrax on the Weeping Causeway. | weeping_causeway | boss_kethrax_defeated |
| 7 | report | A Chain Breaks | Return to Paul David in Olivar. | Olivar, paul_david | mq_kethrax_reported |
| 8–10 | forest / temple / warden | (legacy chain, texts retold: Morthar held the temple alone) | | | legacy flags |
| 11 | after | A Quiet Valley | Speak with Elder Maelis. | maelis | (visited warden_fallen) |
| 12 | spire | The Road to the Black Spire | Speak with Paul David. | paul_david | (visited spire) — story "to be continued" |

Existing heroes: every step is keyed on its own flag, so an old save simply picks up the first new step it has not done.

## 3. Cutscenes

A data-driven cutscene player (`CutscenePlayer`, UIRoot layer): letterbox, subtitles with speaker plates, title cards,
fades/flashes/shake, camera paths with DOF, actors (CharacterVisual + custom clips), VFX, sound and music cues.
Controls: **Skip scene** (button, Space/Enter/Esc, tap) jumps to the end of the current scene; a **Skip all** button
exists only when the cutscene allows it. `the_three` never offers Skip all (author rule). Gameplay input is blocked;
the world pauses when not networked. Paul David can replay `the_three` on request.

| id | trigger | skip all | scenes |
|---|---|---|---|
| prologue | new game, before the Tempo intro | yes | night over Malasugue, narration of Jre; the waypoint flares; the hero lands in a pillar of light and rises |
| shard | Aldric opens the reliquary | yes | close-up of the shard; crimson pulse; a flash of the dragon helm's eyes; whisper |
| the_three | Paul David's tale | **no** | Olivar two-shot → "Three winters ago" → Roydo's arrival and name card → Aljay consumed by darkness, rising, name card → the Three on the causeway → the betrayal (sealing bolts, Kethrax's chains, Roydo's last stand, the brand) → back to Olivar |
| kethrax_intro | entering the Tollhouse ring | yes | Kethrax drags his chains out of the water; name card |
| chain_breaks | Kethrax falls | yes | Kethrax's last words; his chains shatter; the Black Spire — Aljay in chains opens his eyes, the aura flares, one chain snaps |

## 4. Assets (Blender pipeline, tools/blender/characters)

- `aljay.glb` (2.05 m), `roydo.glb` (2.1 m, broad), `paul_david.glb` (1.86 m), `kethrax.glb` (2.3 m, boss scale in game).
- Weapons (tools/blender weapons path, origin at grip): `dusk_piercer.glb`, `dawnmaul.glb`, `stormwake.glb`,
  `kethrax_chainmace.glb`.
- UVs: rest-pose box projection per face (baked, deforms with the skin). Textures generated to
  `game/assets/textures/legend/`: dragon scale, holy engraved plate, forsaken iron, leather, storm wool (albedo/normal/
  roughness). MaterialLibrary keeps imported textures for palette materials.
- Custom clips (`lib_cinematic.py`, `cs_*`): kneel, rise, lance raise, charge, chained struggle, hammer land, hammer
  slam, hammer shoulder, last stand, talk gesture, brand look, sword draw, chain drag, chain throw, death kneel.
- Name plates / cards: Class SX emblem (`emblem_sx.png`) and animated shader text (crimson flame for Aljay, holy gold
  for Roydo, storm azure for Paul David).
- Boss map `weeping_causeway` (MapBuilder): the sunken causeway and the Drowned Tollhouse ring; reached from Wyman's
  Marsh Overlook once `mq_marsh_gate_open`; Kethrax + Forsaken Legionnaires.

## 5. Acceptance

- Unit tests: chain order/flags, old-save pick-up, dialogue graphs valid (actions/services/conditions), cutscene data
  valid (every scene has a duration, every actor model exists, every clip exists in its GLB), `the_three` has no
  skip-all, skip-scene advances exactly one scene, the flags are set when a cutscene is skipped.
- Real-renderer captures of every cutscene's key frames, Paul David in Olivar, the Kethrax fight.
- Full suite: no new failures against the 19 known.
