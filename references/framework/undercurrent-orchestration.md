# Undercurrent — Orchestration

**Concept anchor:** Reis & Housley 2022, ch. 2 (undercurrents section on Orchestration).
**Also drawing from:** Apache Airflow docs; Dagster docs ("Software-Defined Assets"); Prefect docs; Argo Workflows docs; Kleppmann *DDIA* ch. 10 (batch processing).

---

## What this undercurrent is

Coordinating the execution of data pipelines: scheduling, dependency management, retries, timeouts, SLAs, backfills, lineage. Without orchestration, you have scripts. With it, you have a system.

## The three dominant orchestrators

| Tool | Model | Strengths | Trade-offs |
|---|---|---|---|
| **Airflow** | Task-centric DAG, Python-defined | Mature ecosystem, vast operator library, broad adoption | DAG-as-Python has gotchas (module-load side effects), operator-heavy mental model |
| **Dagster** | Asset-centric, typed | Software-defined assets model data as first-class, strong local dev, typed inputs / outputs, lineage built-in | Smaller community, newer |
| **Prefect** | Flow-centric, Python-first | Light abstraction, great local dev, dynamic task generation | Smaller than Airflow's ecosystem |

**Also relevant:** Argo Workflows (Kubernetes-native, YAML DAGs), Flyte (K8s-native, typed), Temporal (workflow-as-code, broader than data).

## Task vs. asset orchestration

- **Task-centric** (Airflow default) — DAGs are graphs of tasks; each task does something; the output is implicit.
- **Asset-centric** (Dagster default) — DAGs are graphs of assets; each asset is a versioned dataset; the computation is a function that produces it. Lineage is structural, not emergent.

Asset-centric models are a better fit for data engineering because data engineering is about producing datasets, not running scripts. If starting greenfield, prefer asset-centric.

## Idempotency in tasks

Every task must be idempotent — re-running with the same inputs produces the same outputs. Requirements:

- Parameterize by a partition key (usually a date / interval), not by "now."
- Never call `datetime.now()` / `date.today()` inside a task body — use the orchestrator-provided `data_interval_start` / `data_interval_end` / `asset_partition_key`.
- No module-top-level side effects in DAG files (Airflow re-imports them constantly; side effects at import become repeated calls in schedulers).
- Deterministic writes: upserts, partition replace, or overwrite — never blind append.

## Retries, timeouts, SLAs

Every task needs:
- `retries` — finite count; exponential or fixed backoff.
- `retry_delay` — non-zero; usually minutes, not seconds, for data jobs.
- `execution_timeout` — bound the task; prevents hung tasks consuming workers.
- `sla` (Airflow) / equivalent — alerts when the task runs but misses its time budget.

Defaults matter: a task with no retries and no timeout is a production incident waiting.

## Backfills

The orchestrator knows which partitions have run. Backfill = re-run a historical range. Works only if tasks are idempotent and partition-scoped.

- **Airflow** — `catchup=True` on a DAG will run all missing intervals between `start_date` and now. Default `False` for new DAGs unless backfill is intentional.
- **Dagster** — `backfill` UI runs a range of asset partitions.

Anti-pattern: ad-hoc backfill by temporarily modifying production DAG code. Always use the orchestrator's backfill mechanism; log it; confirm idempotency.

## Dependency management

- **Task dependencies** — explicit in the DAG definition. Keep DAGs shallow (avoid 50-task serial chains).
- **Cross-DAG dependencies** — Airflow `ExternalTaskSensor`, Dagster asset sensors. Avoid when possible; prefer a single DAG per data product.
- **Sensor-driven** — polling for external events. Use `poke_interval`, `timeout`, `mode='reschedule'` (in Airflow) to avoid occupying workers.

## Observability

- Task-level logs centralized (not stranded on worker boxes).
- Success / failure metrics to Prometheus or equivalent.
- Freshness as an explicit signal, not just "did the task run."
- Lineage exported (OpenLineage integration in both Airflow and Dagster).

## Anti-patterns

- `datetime.now()` inside a task — breaks idempotency, makes backfill lie.
- No retries — transient network blips become manual on-call.
- Hard-coded credentials in DAG files — secrets leak, rotation impossible.
- Catchup=True on new DAGs — launches years of historical runs on first deploy.
- One giant DAG with 200 tasks — impossible to reason about; break into multiple DAGs or sub-DAGs.
- Sensors without timeouts — hang forever.
- "Success" meaning "the script exited 0," without validating the data was produced correctly.

## See also

- Testing idempotency: `undercurrent-dataops.md`
- Backfill playbook: `../playbooks/plan-a-backfill.md`
