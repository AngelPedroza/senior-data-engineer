# Playbook — Fix a Broken Data Job

**When to use:** a pipeline has failed, produced wrong / late / missing / duplicated data, or a stakeholder is complaining about bad numbers.
**Related framework:** `../framework/undercurrent-dataops.md`, `../framework/undercurrent-orchestration.md`.
**Related skill:** `superpowers:systematic-debugging` — read that first if available.

---

## Step 0 — Stop first

Before changing anything, decide:
- [ ] Is the pipeline still running? Should it be paused?
- [ ] Is downstream consumption serving wrong numbers *right now*? Should dashboards / APIs be flagged?
- [ ] Is data still being ingested into a broken state? (If yes, consider stopping ingestion.)

Acting before stopping can compound damage (more corrupted rows, more retry storms, more pages).

## Step 1 — Classify the symptom

Name the problem precisely. Pick one:
- **Late** — data is not where it should be by its SLA.
- **Missing** — rows expected aren't there.
- **Duplicated** — rows appear more than once.
- **Wrong values** — rows are present but a measure / attribute is incorrect.
- **Schema drift** — downstream is breaking because shape changed.
- **Failed task** — orchestrator shows failure.

Each class has different likely root causes. Do not investigate all of them at once.

## Step 2 — Preserve evidence

Before fixing:
- [ ] Snapshot the current broken state (row counts, a `SELECT` sample, the error log).
- [ ] Capture the failing run's DAG / job ID.
- [ ] Note the upstream source state (was there a source outage?).
- [ ] Note any deploys / infra changes in the last 24-72 hours.

Evidence disappears when you retry.

## Step 3 — Form a single hypothesis

From the symptom class, list plausible root causes. Pick the most likely one. Write it down:

> "I hypothesize X is the root cause because Y."

Specific. Testable.

Common root causes by symptom:

| Symptom | First suspects |
|---|---|
| Late | Upstream source delay; orchestrator worker starvation; long-running step |
| Missing | Filter bug; silent `INNER JOIN` dropping rows; source dedupe wrong |
| Duplicated | `MERGE` key not unique; non-idempotent append; upstream retry |
| Wrong values | Logic bug; timezone; measure unit mismatch; source schema change |
| Schema drift | Upstream migration without notification |
| Failed task | Infra (OOM / disk / network); auth / secret expiry; code bug |

## Step 4 — Gather evidence at component boundaries

For multi-component pipelines (source → ingestion → staging → marts → serving), add instrumentation at each boundary:

- Row count out of each stage vs. expected.
- Distinct primary-key count at each stage.
- Null count on critical columns.
- A sample of 10 rows from each stage for the affected partition.

Identify which boundary loses fidelity. Fix at that boundary, not further downstream.

## Step 5 — Test the hypothesis minimally

- Reproduce the bug in a sandbox / dev environment if possible.
- Make the smallest change that would confirm or refute the hypothesis.
- Do NOT make multiple changes at once.

If the test confirms the hypothesis → proceed to Step 6.
If it refutes → form a new hypothesis (Step 3). Do not stack fixes.

## Step 6 — Fix the root cause, not the symptom

- Do not add a filter to hide duplicates if the join should not be producing them.
- Do not widen a timeout if the real issue is an infinite loop.
- Do not disable a failing test if the data is genuinely wrong.

The short fix is tempting and almost always wrong in data pipelines, where the symptom will reappear under different conditions.

## Step 7 — Write a regression test

Before merging the fix:
- Add a test that would have caught this bug.
- Grain test, relationship test, distribution test, or custom business rule — whichever matches the bug class.
- Run it. Confirm it passes on the fixed code and fails on the pre-fix code.

If this isn't testable — that is also a root cause. Address it.

## Step 8 — Backfill affected historical data

If the bug produced bad data historically:
- Determine the affected window (which partitions / dates).
- Use `plan-a-backfill.md`.
- Verify post-backfill with reconciliation.

## Step 9 — Unblock consumers

- Communicate resolution to affected stakeholders with: what broke, what was affected, what's been fixed, what's been re-verified.
- Update status on dashboards / catalog / incident channel.
- Remove any manual "data is broken" flags.

## Step 10 — Postmortem

For customer-impacting or recurring incidents:
- Timeline of detection → diagnosis → fix.
- Root cause (not symptom).
- What went well.
- What didn't (detection lag? Lack of alerts? Missing test?).
- Action items, each with an owner and a date.

Blameless. The goal is preventing the class of bug, not assigning fault.

## If 3+ fixes fail

Stop. This is an architecture problem, not a bug. Examples:
- Each fix reveals a new, different corruption in the pipeline.
- Fixes require "massive refactoring" to implement.
- Fixes cause new problems in unrelated places.

Do not attempt a fourth fix in isolation. Escalate, involve more eyes, question whether the current design is sound. See `../framework/undercurrent-architecture.md`.

## Common mistakes

- Retrying without investigating (same failure, again).
- Multiple simultaneous fixes — can't tell which worked; introduces new bugs.
- Symptom fixes (filter out the duplicates instead of fixing the join).
- Declaring done without backfilling the bad historical window.
- Skipping the regression test "because it's urgent."
