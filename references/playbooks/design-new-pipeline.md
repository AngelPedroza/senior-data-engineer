# Playbook — Design a New Pipeline

**When to use:** before writing any code for a new dataset, pipeline, ingestion, or transformation.
**Related framework:** `../framework/00-data-engineering-lifecycle.md` (mental model), `../framework/03-ingestion.md`, `../framework/04-transformation.md`.
**Related script:** `scripts/lifecycle_checklist.py` (interactive walk-through).

---

## Step 1 — Nail the data contract

Do not skip. Answers to these drive every downstream decision.

- [ ] **Source of truth** — where does the data originate?
- [ ] **Update semantics** — append-only / mutable / soft-delete / CDC?
- [ ] **Grain** — one row per *what*? Write it as a full sentence.
- [ ] **Primary key** — natural key? Surrogate? How is uniqueness guaranteed?
- [ ] **Volume** — rows/day, total rows, growth rate, burstiness.
- [ ] **Latency SLA** — real-time, near-real-time, hourly, daily, weekly?
- [ ] **Consumers** — who reads this and why? What is their access pattern?
- [ ] **Backfill scope** — how far back? Is reprocessing safe?
- [ ] **PII / sensitivity** — what's in it? Classification tier?
- [ ] **Retention** — how long? (Must have an answer.)

If any of these are "TBD," stop and get the answer before designing.

## Step 2 — Pick stage boundaries

Name the stages your pipeline traverses (`../framework/00-data-engineering-lifecycle.md`):

- [ ] Generation — source system, owned by who?
- [ ] Ingestion — push / pull / poll? Batch / stream / micro-batch?
- [ ] Transformation — layered how? (raw / staging / marts)
- [ ] Serving — how are consumers reading? BI, ML features, reverse ETL?

Each boundary is a contract point. Write the schema that crosses each boundary.

## Step 3 — Choose technology

Default to what the team already runs unless there is a clear reason to introduce something new. Reversibility test: if this choice is wrong in two years, what does reversing it cost?

For a typical batch analytics pipeline in a team already running dbt on a warehouse:
- Ingestion: managed connector (Fivetran / Airbyte) or custom Python.
- Storage: existing warehouse / lakehouse.
- Transformation: dbt.
- Orchestration: existing orchestrator.

Deep dive: `choose-technology.md`.

## Step 4 — Design the model

For analytics mart pipelines — apply Kimball by default (`../framework/04-transformation.md`):
- [ ] Layer 1 (raw) — immutable, source-faithful.
- [ ] Layer 2 (staging) — cleaned, typed, surrogate keys.
- [ ] Layer 3 (marts) — joined, aggregated, business-meaningful.

For fact tables specifically, use `model-a-fact-table.md`.

Declare the grain of every model in its description.

## Step 5 — Plan tests

Before writing model SQL, write the tests you expect it to pass:
- [ ] `unique` on grain key
- [ ] `not_null` on grain key
- [ ] `relationships` on every FK
- [ ] `accepted_values` on every enum
- [ ] Source `freshness` on every source
- [ ] Row-count reconciliation test against source of truth (if applicable)

Tests-first means the definition of "done" is clear.

## Step 6 — Plan observability

Before coding, decide:
- [ ] Freshness alert — trigger at what lag?
- [ ] Volume anomaly — what is the tolerance window?
- [ ] Schema drift — how will source changes be detected?
- [ ] Dashboard / lineage link — how will consumers see status?
- [ ] On-call — who gets paged if it breaks?

## Step 7 — Plan cost

- [ ] Estimate bytes scanned / credits per run — is it reasonable?
- [ ] Is partitioning set up for downstream query patterns?
- [ ] Is the materialization right (view / table / incremental)?
- [ ] What's the storage retention policy?

See `../framework/concept-finops.md`.

## Step 8 — Document

Write a short design note (not a 30-page doc — one page):
- Contract (from Step 1)
- Stage choices (from Step 2)
- Technology (from Step 3) and reversibility note
- Model diagram (even ASCII)
- SLAs
- Owner
- Open questions

Commit this to the repo in a `/docs` folder or equivalent. Future you (and your teammates) will read it more often than you think.

## Step 9 — Build in layers

Implementation order:
1. Raw / ingestion first. Land data correctly.
2. Staging. Clean, type, dedupe. Add boundary tests.
3. Marts. Join and aggregate. Add business-rule tests.
4. Orchestration. Idempotent tasks, retries, SLAs.
5. Monitoring. Alerts routed correctly.
6. Consumer access. BI connections, feature-store materialization, or reverse-ETL sync.

Do not skip ahead; the layer below must be verified before the layer above is built.

## Step 10 — Verify before declaring done

- [ ] Row count expected vs. actual at each layer.
- [ ] `count(*) == count(distinct pk)` on every table.
- [ ] Reconciliation test passes (totals match source of truth).
- [ ] A clean re-run from zero produces the same output.
- [ ] Monitoring alerts fire on a seeded failure (test the alerting).
- [ ] Consumers can read the data with expected schema.

Only after all boxes are checked: announce and hand off.

## Common mistakes at design time

- Jumping to code before the contract is clear.
- Picking technology before understanding the workload.
- Designing for scale you don't have (over-engineering) or ignoring growth (under-engineering).
- Treating tests and monitoring as "Phase 2" work — they never get added.
- No named owner.
