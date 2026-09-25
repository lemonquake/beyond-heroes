---
name: lemondev
description: Build, improve, and verify games, game systems, procedural assets, and HUD/UI with the Gauntlet Loop. Use when the user invokes @lemondev, $lemondev, or asks to apply the Gauntlet Loop to game development. Includes isolated builders, blind benchmark comparison, stress testing, and integration gates. Not for unrelated apps or ordinary game recommendations.
---

# lemondev

Turn a game-development request into bounded, independently verified components. Follow the supplied *Gauntlet Loop Guide for Autonomous AI Game Development*, directive V4.2. Its goal is evidence-backed quality, not a promise that every request will reach AAA quality within a budget.

## Invocation and scope

- Recognize `@lemondev <task>` in ChatGPT and `$lemondev <task>` in Codex. Treat “use lemondev” as the same request once this skill is available. Host installation/discovery controls whether mentions resolve; this file does not register an account-wide alias.
- With only `@lemondev`, ask what game, system, asset, or UI to build. Do not invent a project or start an unlimited loop.
- For a request to explain or plan, deliver that explanation or plan; do not start implementation. For a build/fix request, implement and verify within the authorized scope.
- Preserve the user's engine, platform, style, existing work, and explicit constraints. User instructions override skill defaults; disclose material deviations from the guide. Do not migrate an engine or add external dependencies just to fit this workflow.
- Retain normal implicit discovery. An invocation preference alone does not mean explicit-only operation.

## Start with a component contract

Inspect the project and existing run/test commands. Establish the requested behavior, engine/version, target device and resolution, available tools, benchmark, performance budget, and allowed time/cost. Infer low-risk choices from the project; ask only for information that blocks consequential work. Continue independent work while awaiting it.

Read [roles-and-review.md](references/roles-and-review.md) before decomposition or delegation. Read [systems.md](references/systems.md) for mechanics and simulations; read [visuals-and-ui.md](references/visuals-and-ui.md) for rendered assets, shaders, or UI. Use [records.md](references/records.md) for contracts, review packets, and handoff records. Consult [source-map.md](references/source-map.md) for provenance and adaptations.

Decompose into discrete artifacts with dependencies, one owner per file set, public interfaces, acceptance criteria, benchmark evidence, test commands, and rollback boundaries. Start with a playable vertical slice for a whole game. Keep each component small enough to test and revise independently. Define the acceptance contract before viewing candidate results.

Select an actual accessible benchmark for the relevant feature. Record its source, local evidence location, and comparison conditions. Prefer the user's supplied benchmark; otherwise select an appropriate accessible commercial reference and disclose that choice. A title name alone is not evidence. If no valid reference is available, request one and continue useful implementation, but leave the benchmark gate unverified. Never manufacture commercial telemetry or label a generated reference as commercial.

## Four-phase Gauntlet Loop

1. **Decompose.** The Orchestrator freezes component scope, interfaces, evaluation criteria, benchmark, and iteration budget. Record the baseline and current revision.
2. **Build in isolation.** A System Builder owns mechanics; an Asset/UI Builder owns visuals or presentation. Delegate independent bounded tasks when available and permitted, using minimal context and separate file ownership. Builders may self-test but cannot grant acceptance.
3. **Run the blind comparison.** A fresh, context-isolated Critic judges raw candidate evidence against the benchmark under the protocol in `roles-and-review.md`. Run required validation first. For valid evidence, force a binary A/B choice and derive PASS or REJECT; do not use numerical quality scores. A rejection returns exactly the single largest observed gap, its evidence, and a concrete recheck condition. Fix that gap within the component, retain existing checks, capture the new revision, and repeat with a fresh Critic.
4. **Apply the integration gate.** The Integration Lead assembles accepted components in a staging build and verifies their combined behavior, rendering, lifecycle, and performance. Rejected or unverified components remain quarantined. Local acceptance never implies integration acceptance.

Automated numerical measurements are allowed; “7/10 quality” ratings are not. A missing or corrupted evidence packet is UNVERIFIED, not a fake A/B loss or pass. Do not keep sampling critics until one approves, conceal losing runs, or quietly weaken the benchmark.

## Integration gate

Before accepting the assembled revision:

- Build and cold-start from the documented setup with no dependence on a warm session. Check module imports, shared contracts, namespaced state, and resource ownership.
- Run the impacted system tests and cross-system regressions. Exercise play, input, pause, resume, restart, and teardown where relevant; verify there are no duplicate listeners, timers, entities, or leaked resources after repeated cycles.
- Run combined headless rendering/performance validation and inspect real rendered output. The guide's default is sustained 60 FPS; define measurement conditions and frame-time thresholds before running. A 60 Hz simulation alone is not evidence of 60 FPS.
- Check shader compilation and material/texture availability, including first load and scene transitions. Reject texture popping or missing shaders.
- Inspect UI at 1920×1080 and 3840×2160, plus the actual target viewport. Check clipping, scale, readable text, and interaction. Account for device pixel ratio.
- Confirm integrated captures and measurements belong to the exact final revision. Any later relevant change invalidates its affected evidence and requires rechecking those gates.

If integration fails, withhold acceptance, identify the single largest integration defect, and return it to the responsible builder with a minimal reproducible case. Keep the previously accepted build recoverable. “Merge” in the guide means passing this gate; it does not authorize publishing, remote merges, purchases, or unrelated external changes.

## Stopping and circuit breakers

Maintain counters per component across agents, restarts, and integration rework. The initial build/review is pass 1. Default to **at most 8 build/review passes**; honor a smaller user budget. Do not silently increase this limit or rename a component to reset it.

Stop that component's loop when any condition holds:

- All required component gates pass; then proceed to integration. Finish the whole task only when its integration gates pass too.
- The pass limit is reached without acceptance.
- The same primary gap occurs in two consecutive valid rejections. Compare defect identity, not exact phrasing. Save evidence and report a plateau; do not launch a third attempt automatically.
- An unresolved subagent reaches 80% of its context limit. Use actual telemetry if available. If unavailable, record `unknown`, use a conservative bounded handoff, and never claim an exact percentage. Preserve counters; a fresh context must not bypass the stop.
- The user's time, token, or cost ceiling is reached; the user asks to stop; or required runtime, evidence, permissions, or tools are unavailable for further dependent work.

At a stop, preserve the best known build and a short resumption record: revision, acceptance state, used passes, largest gap, evidence paths, blocker, and smallest next action. Continue only independent in-scope components that do not depend on the failed one and fit the remaining budget. Changing a stopped loop's scope, benchmark, or budget requires an explicit new decision; never present exhaustion as success.

## Completion and output

Use `work/lemondev/<run-id>/` for contracts and evidence, or the project's existing equivalent. Keep builder logs and private mapping separate from the critic packet. Deliver runnable source/assets, reproducible setup and launch steps, verification evidence, and a concise handoff using `records.md`.

Report one of these states, scoped to the named artifact/revision:

- **VERIFIED:** all applicable component and integration gates passed with current evidence and genuine independent review.
- **IMPLEMENTED — UNVERIFIED:** an implementation exists but required runtime, benchmark, independent review, or integration evidence is missing.
- **STOPPED — LIMIT / PLATEAU / BLOCKED:** the loop ended before acceptance; include the reason and remaining gap.
- **PLAN ONLY:** no implementation or execution is claimed.

Do not say “complete,” “AAA,” “production-ready,” “60 FPS,” “stress-tested,” or “blind-reviewed” without the corresponding inspected evidence and stated conditions. A screenshot does not prove mechanics; a test command that never ran does not prove success; a visual win does not cancel a correctness failure. Mark a gate N/A only with a contract-based reason, never to conceal missing tools.

Use plain product labels such as Play, Game Setup, Shop, Pause, Resume, Restart, Team, and Match Results. Keep UI readable at normal desktop size. Avoid military framing, slogans, and tiny uppercase text carrying essential information. Funny bot names are welcome when relevant; ordinary descriptions remain direct.
