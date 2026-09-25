# Source and adaptation record

This skill was created from the user-supplied **Gauntlet Loop Guide for Autonomous AI Game Development.pdf**, four pages, internal title *The Gauntlet Loop Manual*, **Autonomous Agent Directive V4.2**. It was retrieved from the attachment to the referenced “Create Game Skill” conversation; the original request identified its cloud path as `/mnt/data/Gauntlet Loop Guide for Autonomous AI Game Development.pdf`. All four pages were extracted and visually inspected.

Source PDF SHA-256:
`0455cbc8302cfc525edf456c784eabf065bb1531e11bf1298ebef08348d4217e`

The skill is self-contained; the original PDF and its former temporary/cloud paths are not runtime dependencies. This is an operational adaptation, not a claim that the manual's quality guarantees have been empirically established.

| PDF location | Principle preserved | Skill location |
| --- | --- | --- |
| Page 1, sections 1–3 | Orchestration, decomposition, isolated builders, blind output-only critic, binary comparison, integration gate | `SKILL.md`; `roles-and-review.md` |
| Page 2, sections 4–6 | Decoupled data-oriented state, fixed 60 Hz / 10,000-step validation, subsystem workloads and thresholds, one-gap rejection | `systems.md`; `roles-and-review.md` |
| Page 3, sections 7–9 | Procedural geometry, custom shaders, procedural textures, four AAA visual criteria, iterative refinement | `visuals-and-ui.md` |
| Page 4, sections 10–11 | Layered HUD, micro-detail, hierarchy, event binding, no harmful reflow | `visuals-and-ui.md` |
| Page 4, section 12 | Eight passes, repeated-gap plateau, 80% context breaker, cold integration, 60 FPS, shader/texture checks, 1080p–4K UI | `SKILL.md`; `systems.md`; `records.md` |

## Explicit operational additions and reconciliations

- Separate the validation runner from the Blind Critic so the critic can judge raw simulation evidence without seeing forbidden code or execution commentary. Raw measurement logs are allowed; builder execution logs are not.
- Randomize neutral A/B labels and keep a private mapping where practical. The manual labels candidate A/reference B; the core forced binary comparison is preserved.
- Add an evidence-integrity state before binary judgment. Missing information is UNVERIFIED, never a fabricated winner. Resolve ties conservatively because the manual asks whether the candidate is superior; its example of matching lighting is not treated as permission to claim superiority without evidence.
- Define contracts, revision-linked evidence, ledger records, reproducible seeds, and conservative defaults for measurement windows/percentiles. The PDF does not specify those operational details.
- Distinguish 60 Hz simulated time from rendered FPS, and headless software rendering from performance on the target device.
- Treat illustrative physics and Fresnel snippets as incomplete examples, preserving their intended architecture without copying their shortcomings.
- Retain the guide's procedural and detailed-HUD defaults, while honoring explicit engine/style constraints. The user's plain-language and readable-UI preferences override the sample HUD's military labels and small uppercase presentation.
- Bound retries and carry counters through integration and new contexts. Unknown context telemetry is reported honestly. Tool limitations permit useful implementation but do not permit a false verification claim.

Host invocation and local packaging guidance was checked against official OpenAI documentation on 2026-09-21; it is product guidance rather than part of the PDF:

- [Build skills](https://learn.chatgpt.com/docs/build-skills)
- [Skills and plugins](https://learn.chatgpt.com/docs/skills-and-plugins)
