# Hero models, animation and platform controls

User outcome: bring suitable Warriors of Aether bodies and animation into the existing Beyond Heroes Godot 4.7.2 game; preserve equipment, character creation, combat timing, saves and networking; improve Android input parity and measured rendering performance.

Additional user instruction: after implementation and integration checks, export fresh Windows and Android packages, commit the finished project changes and push to main. Build products remain in the existing ignored build folder; record their hashes and provide links. Avoid adding QA project mirrors, import caches, signing files or user data to Git.

Baseline: current working tree on 2026-10-26, with 13 pre-existing modified gameplay/world files. Preserve those files. Source benchmark: the user's local Warriors of Aether project at A:/Python/woa, especially its Blood Ranger bow animation and class-appropriate hero bodies. Binary asset reuse is explicitly requested and overrides the procedural-asset default.

Release assembly: a separate managed checkout of the same base commit receives only the reviewed task files. This preserves the original folder's unfinished Kafga work and permits a build that matches the source pushed to main. Desktop runtime captures in the original QA mirror remain reference evidence; final test/build receipts use the isolated release checkout. First-launch mobile target is 60 FPS with lighter rendering; explicit saved caps remain unchanged, and faster caps remain available.

Components and ownership:
- Models/animation builder: character_visual.gd, hero visual/catalog helpers and imported hero assets, associated focused tests and preview tools. Fit Knight, Mage, Hunter and Shadowblade; retain customizable body support and real equipped weapons.
- Touch builder: mobile UI, item/context interaction helpers and focused tests. Long hold performs the intended secondary action once, movement and cancellation do not activate it, modal/focus changes release held controls; avoid per-frame icon/resource work.
- Performance builder: settings.gd, perf.gd, video settings UI and focused tests. Preserve gameplay and player preferences; provide high-refresh choice and reduce measured presentation overhead.
- Integration owner: test execution, evidence tools/reports, builds, runtime captures and final review. Builders must coordinate rather than edit another component's files.

Acceptance: import and cold start without new script/runtime errors; focused regressions; suitable visible models and weapon animation; touch context and cancellation behavior; repeat lifecycle operations without stuck input. Applicable simulation changes require 10,000 fixed-step checks. No combat simulation changes are planned. Measure real rendering separately from headless tests, at matched 1280x720 profiles, including town, forest and dense combat. Target 100+ FPS (10 ms/frame) on capable hardware and sustained 60 FPS (p95 <=16.67 ms) as an additional reported threshold. Neither is a universal device guarantee. Report median/p95/p99, hardware/backend and sample duration. Physical Android performance and refresh behavior require an actual connected device.

Capture conditions: fixed gallery cameras for bodies/poses, 1920x1080 and 3840x2160 UI plus touch viewport; existing perf scenarios and deterministic seed. Preserve scratch save slots and isolate user data. Eight passes maximum per component; repeated identical rejection twice stops that component. Independent critic receives only neutral raw evidence; filesystem isolation is instruction-enforced in this shared workspace. If reference/capture/device evidence is unavailable, mark that gate unverified and preserve the runnable implementation.
