# bh-005 — Starter Tempo, onboarding guide, Tempo grades and renowned Tempos

Run / component ID: bh-005 (components C1–C6 below)
User outcome (2026-09-27 request):
- A new game / new hero starts with one low-level Tempo: a basic Swordsman.
- A dialogue guide at the start introduces that Tempo, what Tempos are and where to hire them.
- Five more unique Tempos to hire, expensive, meant for stronger raids.
- The Tempos offered for hire upgrade as the game progresses and are replaced by stronger ones with more and more
  unique skills.
- At the start of a new game the player is also guided through shortcut keys and basic functions.
Scope exclusions: no new 3D models or animations (existing knight/mage rigs); no new maps; no commit/push (user rule:
work on main, uncommitted); old saves are not given a starter Tempo retroactively.

Engine / platform: Godot 4.7.2 (C:\Users\Lemon PC\Desktop\Godot.exe), Windows desktop, 1920×1080 logical UI.
Baseline revision / rollback point: 07244e8 + the pre-existing uncommitted working tree (import files).

## Components and owned files
C1 Data + rules — src/data/data_tempos.gd, src/core/tempos/tempo_data.gd, src/core/tempos/tempo_rules.gd
   * Grades 1–5 (Restless → Ascendant) unlocked by hero level or story deeds; grade sets mirror share, skill count,
     price; roster refreshes at once when the grade rises (weaker offers replaced).
   * New classes Mystic (grade 2+) and Warden (grade 3+); advanced grade-gated skills for every class.
   * Five renowned Tempos (fixed identity, unique skills, level requirement, 1,500–12,000 gold, mirror 0.75).
   * Starter Tempo "Tobren" (grade 1 Swordsman, Cleave + Soul Mend, free).
C2 Tempo actor — src/actors/tempo/tempo.gd: data-driven skill handlers (`use`), role-based AI (`ai`), new handlers
   nova / bolt / chain / ward / rally / trap / execute / group heal.
C3 Shrine + Tempo UI — tempo_caller_window.gd (grade line, Renowned tab), tempo_window.gd (grade shown).
C4 Onboarding — data_guide.gd (guide graph), dialogue.gd ({key:action} placeholders, `guide_done`), dialogue_box.gd
   (start without an NPC node, per-node speaker), guide_window.gd (H: Field Guide), input_setup / settings / ui_root,
   game.gd (grant starter + open guide on a new game).
C5 Art — tools/ui_art/bh005_tempos.py: crests (mystic, warden), skill icons for new skills, portraits (Tobren + 5).
C6 Tests + docs — tests/unit/test_tempos.gd additions, new test_guide.gd; docs/LORE.md §9.

## Acceptance (frozen before building)
- New game: hero.tempos == [Tobren, Swordsman, grade 1]; he spawns beside the hero; the guide opens once, never again
  after it ends; Continue/Load never re-opens it; the Field Guide (H) replays it.
- Every {key:x} placeholder in the guide resolves to the live binding (rebinding changes the text).
- Grade: pure function of hero level + flags; offers of a new grade replace the old roster immediately; generated
  skill counts and mirror match the grade table; grade-1 behaviour identical to before (existing tests unchanged).
- Renowned: exactly 5, unique names not in the random pool, each ≥ 1 unique skill, locked below its level, refused
  without gold, cannot be bound twice, returns to the shrine when released; save round trip exact.
- Every skill `use` has a handler in Tempo._use_skill; every class/skill/legend icon exists; combat bot with the new
  classes runs with no SCRIPT ERROR.
- Suite green on 4.7.2; compile_all clean.
- Rendered evidence (real renderer): guide dialogue at start, Field Guide, Shrine roster + Renowned tab, starter Tempo
  in the world.

Benchmark: no accessible commercial reference evidence was supplied or captured for onboarding/companion hiring;
the benchmark gate is UNVERIFIED (disclosed). Maximum passes: 8 per component.
