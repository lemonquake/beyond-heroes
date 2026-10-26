# Release validation — 2026-10-26

The release checkout contains the reviewed hero-model, animation, touch-control and presentation-performance changes. It excludes the original checkout's unfinished Kafga work. The Windows/Android exports and push to `main` must be recorded below before release handoff.

## Implementation covered

Knight uses Emelrich's plate armour, Mage uses Azrin's robe, Shadowblade uses Caziel's coat, and Hunter uses the Blood Ranger outfit on the matching shared body. Custom hero bodies remain available. Equipment, off-hand items, character previews, portraits and remote avatars use the selected body. The Blood Ranger bow motion keeps the existing normal and charged release timings. Credits, source hashes and local extraction instructions accompany the assets; the private loose animation resource is required for export and is excluded from Git.

Touch holds now expose inventory options, stack quantities, skill/talent refunds and belt choices. Contact ownership, drag/cancel, target changes, modal changes, focus loss and both multi-finger release orders have focused coverage. Mobile starts with lighter rendering and a 60 FPS cap; saved explicit caps survive preset changes. Faster caps and Unlimited remain selectable. The optional Android display-rate request remains subject to the device and OS.

## Automated checks

All receipts below are under the local ignored `output/hero-port-20261026/` folder in the original project directory. They identify the clean release checkout as the tested project.

| Evidence | Result |
| --- | --- |
| `release-import-resume-receipt.json` | Godot 4.7.2 import finished, exit 0; 486.187 s after the earlier interrupted import resumed. |
| `final-release-regressions.json` and receipt | 26 suites, 35,099 checks, zero failures; process exit 0, 151.375 s. |
| `final-model-portrait-regressions.json` and receipt | After the final portrait integration and Hunter gait correction: 10,070 checks, zero failures; process exit 0. This overlaps the broad run and is not an additional unique-check count. |
| `final-touch-timer-check.log` | 1,582 checks, zero failures across touch parity, class rework and BH042. |
| `portrait-final-checked.log` and receipt | 18 class/custom/HUD/save-card/legacy/persona portrait renders; zero comparison failures, exit 0. |

The broad run still reports navigation rasterization warnings plus test-exit diagnostics: two leaked NavMap RIDs, 35 ObjectDB instances, six resources in use and a VariantPool page warning. Render probes also have shutdown resource diagnostics. Passing assertions do not establish leak-free teardown. These diagnostics are retained in the logs. No combat simulation code changed, so the additional 10,000-step equivalence gate for simulation changes was not applicable.

## Visible models and controls

The independent blind critic inspected only the neutral matched render packet and chose the candidate with a clear advantage in class silhouettes and bow-pose readability. It passed the visible attachment constraints. Still images do not prove continuous bow-string deformation; the source-style static string limitation remains.

The final checked portrait set is `portraits-checked/`. The Ranger portrait shows the red-haired Blood Ranger body; the Mage portrait shows the hooded role model. The capture comparison covers the HUD/save-card paths as well as direct previews.

Desktop-engine UI captures exist at 1920×1080, 3840×2160 and a 1920×864 phone-shaped viewport. `clean-touch-final/notes.json` and `ui-4k/notes.json` report that the inventory hold kept the item, opened the options menu, survived the original contact release and resumed successfully. Inputs were injected into Godot, including an explicit simulated focus notification. These are desktop touch-path checks, not physical Android interactions. Native Windows manual interaction was not verified because the Computer Use window-state/focus calls timed out.

## Rendered performance

Measured on the Windows host with Ryzen 7 5700X and NVIDIA RTX 4060, Godot 4.7.2, 1280×720, class models and touch mode enabled. Every row is a single run with approximately 60 seconds of sampled frames after warmup. PC Low uses Vulkan Forward+; Mobile profile uses OpenGL Compatibility. The latter is a desktop renderer/profile measurement, not Android-device performance. Raw frame sidecars, full per-location statistics and logs are retained under `perf/release-desktop/` and `perf/release-mobile-profile/`.

| Scenario/profile | Average FPS | Median / p95 / p99 frame ms | Frames >10 ms | Frames >16.67 ms | Samples |
| --- | ---: | --- | ---: | ---: | ---: |
| Town / PC Low | 269.86 | 3.45 / 5.89 / 7.11 | 4 | 0 | 16,193 |
| Forest / PC Low | 245.06 | 3.52 / 8.02 / 12.33 | 298 | 26 | 14,705 |
| Forest / Mobile profile | 85.54 | 11.32 / 17.29 / 21.04 | 3,398 | 355 | 5,134 |
| 12-enemy combat / Mobile profile | 66.56 | 14.17 / 22.13 / 26.74 | 3,674 | 1,252 | 3,994 |
| 40-enemy stress / Mobile profile | 21.45 | 46.59 / 66.99 / 75.43 | 1,287 | 1,285 | 1,287 |

Town and forest exceeded 100 FPS on this PC using PC Low. Forest/PC Low had occasional frames above the 10 ms and 16.67 ms thresholds. The Mobile-profile runs missed the p95 60-FPS threshold, and dense stress remains substantially below the requested target. The stress run ended with 99 enemies in the map and 45 engaged; the 12-enemy run ended with 62 total and 12 engaged. These workloads are not a universal frame-rate guarantee or a physical low-end phone result.

An earlier matched overlay ablation showed 2,257.5 median draw calls with all overlays attached versus 1,500 with every overlay disabled; wall-time medians were 53.29 versus 51.05 ms. That diagnostic also removed visible effects. Production instead retains flash/rim effects and attaches their pass only while active or during the bounded loading warmup. The ablation is evidence of redundant draw work, not a measured 33% production FPS improvement. Baseline/candidate runs had changing live-fight outcomes and background load; no precise causal speedup is claimed from their absolute FPS difference. Dense CPU/physics work remains the measured gap; collision and AI behavior were preserved.

## Android and release handoff

- Physical Android: unverified. No phone/tablet was connected through ADB. The requested target is a low- to mid-range phone.
- Android emulator: pending root validation on the existing API 36, 2 GB RAM AVD, launched as a temporary read-only instance. Emulator behavior can verify the native Android package and touch/lifecycle paths; its FPS cannot certify a physical phone.
- Fresh Windows EXE/ZIP and Android APK: pending. Record export command receipts, artifact size/SHA-256, included ABIs and signing verification here.
- Exported-package smoke tests: pending. Record actual startup, body/animation and Android touch/lifecycle results, including any errors.
- Source commit and remote `main`: pending. Record the tested source commit, final documentation commit and successful push after preserving the original checkout's unrelated work.

The first-hit overlay warmup render check remains unrecorded at this evidence review. The implementation's bounded warmup/state behavior passes its automated suite; that alone does not prove first-hit frame timing.
