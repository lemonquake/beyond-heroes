# Reusable records

Copy only the records needed for the task. Fill fields with observed values; use `unknown` or `not run` instead of invented values. These are workflow records, not executable commands or a built-in enforcement service.

## Component contract

```text
Run / component ID:
User outcome and scope exclusions:
Engine / platform / target device:
Artifact and owned files:
Dependencies and public input/output/event contracts:
Baseline revision / rollback point:
Benchmark source and evidence location:
Frozen comparison criterion and mandatory invariants:
Simulation / stress / render / interaction checks:
Performance thresholds and measurement conditions:
Capture scenes, camera, viewport, seed:
Maximum passes (default 8); user time/token/cost ceiling:
Known tools or evidence unavailable:
Guide overrides and reasons:
```

## Builder assignment

```text
Build this one component: <contract>.
Work only in: <owned paths>.
Use these interfaces: <schemas / relevant dependency exports>.
Return source/assets, reproducible run/test commands, actual outputs,
artifact revision, and known limitations. Do not grant acceptance.
For a revision, address only: <single gap + evidence + recheck condition>.
Preserve existing passed behavior and run affected regression checks.
```

## Blind critic packet

```text
Neutral review ID:
Comparison criterion fixed before candidate inspection:
Mandatory observable constraints:
A: <raw renders / clips / measurements / traces>
B: <raw renders / clips / measurements / traces>
Neutral test definitions, units, viewing conditions:
Read only this packet. Do not access source, builder history, logs, or rationale.
If evidence is incomplete or incomparable, return UNVERIFIED and the reason.
Otherwise choose A or B, without numerical quality scores.
Return the response below, with only one decisive comparison gap.
```

```text
Evidence status: VALID | UNVERIFIED
Unavailable or incomparable evidence: <only if unverified>
Winner: A | B <only if valid>
Clear advantage: true | false
Observed basis: <specific evidence pointers>
Mandatory constraints: <observed results; no unsupported claims>
Single comparison gap: <one defect, or no demonstrated advantage, or none>
Recheck condition: <observable acceptance condition for that gap>
```

Keep candidate-label mapping and revision identifiers in an Orchestrator-only record. The Orchestrator computes candidate PASS/REJECT after revealing this mapping and checking required validation results. If a mandatory failure overrides a visual win, return that single largest failure to the builder instead of another visual improvement request.

## Iteration ledger (private; not sent to fresh critics)

| Component | Pass | Artifact revision | Evidence / reviewer ID | Winner / clear advantage | Verdict | Primary defect ID | Used budget / context | Next state |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

Normalize defect identity across wording variations. Record invalid reviews without treating them as valid wins or resetting the build-pass counter. Cap repeated evidence-recovery work within the same user budget. Track integration-triggered rework against the same component counter.

## Final handoff

```text
Status: VERIFIED | IMPLEMENTED — UNVERIFIED | STOPPED — reason | PLAN ONLY
Scope and exact artifact revision:
What changed and where the runnable result is:
Setup / launch / controls:
Gate results: component tests; blind benchmark; integration; target performance
Evidence: commands, actual results, captures/traces, benchmark and review IDs
Performance: environment, resolution, workload, window, frame-time distribution
Unverified items / remaining largest gap:
Pass counts and stop reason, if any:
Next action needed to resume, if stopped:
```

Keep the user-facing response concise; link the detailed record. Do not expose private critic mappings before review or publish proprietary benchmark materials beyond the user's authorized destination.
