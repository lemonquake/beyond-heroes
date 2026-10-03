# Blind review: crowd animation / simulation LODs (bh-035)

Question fixed before viewing: which build shows the crowd moving and animating more naturally between consecutive frames
(frozen poses while moving, sliding without leg motion, position pops, stutter, clipping)? Mandatory: no T-poses or
missing parts, nobody floating or sunk, HUD readable. Evidence: 8 consecutive frames of the same scripted 40-monster
brawl (pc-high, 1280x720) from the baseline build (0437f968, frozen copy) and this build; fresh reviewer each pass,
labels randomised, mapping revealed only after the verdict.

| Pass | Mapping (revealed after) | Winner | Clear advantage | Single gap |
| --- | --- | --- | --- | --- |
| 1 | this build = B, baseline = A | A (baseline) | false | B's first frame step: a 40 px pop and a dark-to-lit change. Cause: the strip started a fixed 90 frames after the brawl began, which the faster build reached while the map was still fading in (zone title visible). Fixed the capture to wait 6 s in both builds. |
| 2 | this build = A, baseline = B | B (baseline) | false | "No demonstrated advantage": both builds show the same frozen-pose spots (idle monsters) and no position discontinuities. |

Mandatory constraints held in both builds in both passes. Verdict recorded as: no visible motion regression found; not
a visual win. Strips of pass 2: strip_A.png (this build), strip_B.png (baseline).
