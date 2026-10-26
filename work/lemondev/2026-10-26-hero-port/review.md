# Independent review and integration decisions

The independent correctness reviewer found and the integration owner corrected:
- Reversed release order on a skill held by two fingers could leave a channel pressed. Ownership now transfers to the remaining contact; both release orders are tested.
- A model change with a shield-only loadout could skip shield rebuilding. The equipment cache checks both hands; shield crystals are covered.
- Hunter and Custom hero share a source animation library. Source arm repairs now apply consistently to compatible rigs, independent of appearance load order. A fresh uncached-library test compares both orders.
- The initial popup test emitted a signal directly. It now routes a real touch/emulated-mouse pair through the embedded popup, checks that the original hold release leaves it open, and checks selection and dismissal without using the underlying item.

Root validation of the new model/touch/settings/overlay suites: 27 tests, 2,669 checks, zero failures before the final 60-FPS-default adjustment. Raw results are in output/hero-port-20261026/overlay-and-model-tests.log. Final staging results supersede these.

Blind visual comparison used only matched raw 1920x1080 OpenGL renders. A fresh context inspected ten images, checked their hashes and chose the candidate with a clear advantage in class silhouettes and bow pose readability. The candidate passed the visible-attachment constraints; the older presentation's bow crossed the shoulders/face. The critic noted that the string does not visibly follow the drawing hand in the stills; this is a source-motion presentation limitation, not evidence of string simulation. Filesystem isolation was instruction-enforced; the critic reported reading only the neutral packet. No source or builder history was provided. The packet and private mapping remain in local output.

Integration decisions:
- No combat simulation changes. Fixed-step combat timings, equipped items and save/network data are retained.
- Default mobile rendering now targets 60 FPS, with 30 available for lower power use and 90–240/Unlimited available for faster devices. Existing explicit caps are preserved. This replaces the initial builder's conservative 30-FPS first-launch decision to better match the user's requested responsiveness.
- The release is assembled from a clean checkout of main plus this task's reviewed files. Pre-existing unfinished Kafga edits/assets in the original checkout are preserved. Their two baseline persona assertions are excluded from the release by keeping that unrelated work out of it; no tests were weakened to hide those failures.
- Physical Android and universal 100+ FPS claims remain unverified. No ADB device was available at discovery. The 40-enemy stress workload remains slower than the target and is reported explicitly.
