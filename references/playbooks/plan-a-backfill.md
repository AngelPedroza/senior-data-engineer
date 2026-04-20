# Playbook — Plan a Backfill

**When to use:** historical data needs to be (re)processed — e.g., after a bug fix, schema change, new column addition, or source correction.
**Related framework:** `../framework/undercurrent-orchestration.md`, `../framework/03-ingestion.md`.

---

## Preconditions

Before starting:
- [ ] The pipeline is idempotent (confirm, don't assume).
- [ ] The affected partitions / date range are known and bounded.
- [ ] The reason for the backfill is documented (what changed, why re-run?).
- [ ] Source data is still available for the backfill range (e.g., retention not elapsed).

If any precondition fails, stop. A non-idempotent backfill produces garbage. Bounded scope is required for cost and safety.

## Step 1 — Define the scope precisely

- **What dates / partitions** are affected?
- **What models / tables** need reprocessing? Use lineage to find all downstream consumers.
- **What consumers** need to be re-refreshed (materialized views, ML feature tables, reverse-ETL syncs)?

Underscoping means some consumers still see stale data. Overscoping wastes compute. Write the list.

## Step 2 — Estimate the cost

Before running, estimate:
- **Compute cost** — how many dollars / credits?
- **Time** — how many hours / days? Is there a maintenance window?
- **Source load** — is the backfill going to hammer upstream? (If pulling from OLTP, this alone can cause an incident.)
- **Downstream impact** — will consumers see stale / inconsistent data during the backfill?

Document the estimate. If it is surprising, escalate before running.

## Step 3 — Choose the strategy

| Strategy | When to use |
|---|---|
| **In-place reprocessing** | Target table has partition-replace idempotency; orchestrator backfill is safe |
| **Shadow table** | Bad data must remain queryable; build new table beside, swap atomically |
| **Blue / green** | Consumers need uninterrupted access; run new pipeline to a parallel target, cut over |

Default: in-place if the pipeline is partition-idempotent. Shadow / blue-green for high-stakes, consumer-facing datasets where any downtime is unacceptable.

## Step 4 — Throttle the backfill

Backfills are large batches. Precautions:
- Run in **chunks** (e.g., one week at a time), not the whole range in one job.
- Rate-limit against the source system if pulling raw data.
- Off-peak if possible (night / weekend).
- Pause upstream ingestion if the target is in an inconsistent state during the backfill — or design the backfill to tolerate concurrent ingest.

## Step 5 — Communicate before

Notify affected parties:
- Consumers of affected tables — what's changing, when, expected duration.
- On-call — that a backfill is starting (so volume / cost anomalies aren't misread as incidents).
- Stakeholders — if numbers on dashboards may shift.

Silent backfills create confusion. "Why did last month's revenue just change?" is not a conversation you want to have after the fact.

## Step 6 — Execute

Use the orchestrator's backfill mechanism:
- **Airflow** — `airflow dags backfill` or UI-driven clear and re-run.
- **Dagster** — asset backfill UI.
- **dbt** — `dbt run --select model_name --vars '{"start": "...", "end": "..."}'` with a date variable.

Do **not** manually hack production DAG code to re-run history. Document the backfill command in the runbook.

## Step 7 — Verify during

Watch as it runs:
- [ ] Row counts per chunk match expected.
- [ ] No errors / retries escalating.
- [ ] Source system is not overloaded.
- [ ] Cost is tracking with the estimate.

If any check fails, pause and diagnose. Don't push through.

## Step 8 — Verify after

After the backfill completes:
- [ ] **Row count** — expected vs. actual across the full range.
- [ ] **Grain** — `count(*) = count(distinct pk)` over the range.
- [ ] **Reconciliation** — totals match the source of truth for the range.
- [ ] **Downstream propagation** — materialized views / feature tables / reverse-ETL syncs refreshed.
- [ ] **Consumer spot check** — key dashboards / reports show the corrected numbers.

## Step 9 — Document

After completion, write:
- Date, range, reason.
- What was reprocessed (tables, downstream consumers).
- Cost actual vs. estimate.
- Anything unexpected (did the estimate hold? did any downstream consumer miss the refresh?).

Commit to the runbook. Future backfills will benefit.

## When not to backfill

- When the affected range is older than the retention period — data may simply be gone.
- When the source system's historical data is itself unreliable (and the "bug" is actually source drift).
- When the affected rows are immaterial to any consumer's decision (yes, this happens).

In those cases, *don't backfill.* Document why.

## Common mistakes

- Running a non-idempotent pipeline over history — compounds the problem.
- Hacking production DAG code temporarily — forgotten, left in, becomes source of next bug.
- Underestimating source load — ingestion DB grinds to a halt mid-backfill.
- Not notifying consumers — dashboards shift numbers, stakeholders alarmed.
- Skipping post-backfill reconciliation — declaring success without verification.
- Concurrent ingestion + backfill without coordination — race condition corruption.

## See also

- Orchestration patterns for backfill: `../framework/undercurrent-orchestration.md`
- Debugging the bug that prompted the backfill: `fix-broken-job.md`
