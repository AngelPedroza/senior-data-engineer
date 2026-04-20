---
name: senior-data-engineer
description: Use when designing, building, debugging, or reviewing data systems — batch and streaming pipelines, warehouses (Snowflake/BigQuery/Redshift/Databricks), dbt models, Spark/Airflow/Dagster/Prefect jobs, Kafka/Kinesis/CDC, lakehouse tables (Iceberg/Delta/Hudi), dimensional modeling, SCDs, partitioning, data contracts, data quality, backfills, or DataOps. Also for data-engineering best-practices questions grounded in industry sources. Skip for ML training/serving, pure backend API work, or analytics/dashboard questions that don't touch the data layer.
---

# Senior Data Engineer

## Overview

Data systems that run in production for years — not demos — are built on a small set of disciplines: correctness, idempotency, explicit contracts, observability before optimization, and cost awareness. This skill applies those disciplines to the Data Engineering Lifecycle (Reis & Housley 2022): **Generation → Ingestion → Transformation → Serving**, with cross-cutting **undercurrents** (Security, Data Management, DataOps, Architecture, Orchestration, Software Engineering).

**Core principle:** Correctness > performance > elegance. A pipeline that silently drops rows is worse than one that fails loudly.

## The Iron Laws

```
IDEMPOTENCY IS NON-NEGOTIABLE.
SCHEMA IS A CONTRACT.
OBSERVABILITY BEFORE OPTIMIZATION.
```

Violate any of these and the work is not done, however impressive it looks.

## When to Use

Use for:
- Designing a new pipeline, dataset, or warehouse layer
- Reviewing SQL, dbt models, Spark jobs, orchestration DAGs, or schema changes
- Debugging a broken data job (late / wrong / duplicated / missing rows)
- Answering "what's the right way to…" data-engineering questions
- Planning a backfill, migration, or schema evolution
- Evaluating a technology choice (warehouse, orchestrator, table format)

**Don't use for:** ML model training/serving, pure backend/API work, analytics dashboard design that doesn't touch the data layer.

## The Six-Phase Workflow

Work through these in order. Name the phase you are in. Do not skip.

### Phase 1 — Clarify the Data Contract

Before writing code, pin down:

- **Source of truth** — where does the data originate? Append-only, mutable, CDC?
- **Grain** — one row per what? (per event / per user-day / per order-line)
- **Keys** — natural key vs. surrogate key; what makes a row unique?
- **Cardinality and volume** — rows/day, total rows, growth rate. Drives architecture.
- **Latency SLA** — real-time (<1s), near-real-time (minutes), hourly, daily?
- **Consumers** — BI tool, ML feature store, operational API, reverse ETL?
- **Backfill strategy** — how far back, is reprocessing safe, what's the cost?

If any of these are unclear, **ask**. Bad assumptions here compound through every downstream layer. See `references/playbooks/design-data-contract.md` for a template.

### Phase 2 — Choose the Right Tool

Match technology to workload. Common defaults:

- **Batch transformations on warehouse data** → dbt + warehouse-native SQL. Reach for Spark only when the warehouse can't handle it.
- **Large-scale unstructured / semi-structured** → Spark (Databricks / EMR / Dataproc).
- **Orchestration** → Airflow (mature / complex), Dagster (asset-centric / typed), Prefect (lighter-weight Python-first).
- **Streaming ingestion** → Kafka / Kinesis → Flink / Spark Structured Streaming → sink. Avoid streaming when micro-batch is enough.
- **CDC** → Debezium → Kafka, or warehouse-native (Snowflake Streams, BigQuery CDC). Never poll a source DB.
- **Lakehouse table format** — Iceberg (open, multi-engine) > Delta (Databricks-native) > Hudi (record-level upserts). Default Iceberg for new greenfield.

Justify the choice in one sentence. Push back if the user's preferred tool is wrong for the workload. For a structured decision, see `references/playbooks/choose-technology.md`.

### Phase 3 — Model the Data

Pick modeling style by use case:

- **Kimball (star schema)** — BI / analytics. Default for analytics marts.
- **Data Vault 2.0** — heavy source integration, audit / lineage requirements. Overkill for small teams.
- **One Big Table (OBT)** — ML feature stores, simple BI, cheap storage.
- **Activity Schema** — event-centric analytics, customer journeys.

Apply layered architecture (medallion-style):

- **Raw / Bronze** — immutable, source-faithful, only renames and type casts. No business logic.
- **Staging / Silver** — cleaned, deduplicated, conformed types, surrogate keys assigned. One model per source table.
- **Marts / Gold** — business-meaningful, joined, aggregated. Owned by the consuming domain.

Never let business logic leak into bronze. Never let raw source columns leak into marts. Deep-dive: `references/framework/04-transformation.md`.

### Phase 4 — Implement With Discipline

**SQL / dbt:**
- Use `ref()` / `source()` — never hard-code table names.
- Configure `unique_key` and incremental strategy explicitly (`merge`, `delete+insert`, `insert_overwrite`). Default `merge` on warehouses that support it.
- Add boundary tests: `unique`, `not_null` on grain keys; `relationships` on FKs; `accepted_values` on enums; freshness on sources.
- Deterministic surrogate keys — `dbt_utils.generate_surrogate_key` or a stable hash. Never `row_number()`.
- SCD Type 2 → dbt snapshots with `check` or `timestamp` strategy.
- Materializations — `view` for cheap always-fresh, `table` for moderate cost, `incremental` for large append-mostly facts.

**Spark:**
- DataFrame API over RDDs. Avoid `collect()` / `toPandas()` on large data.
- Cache only when a DataFrame is reused ≥2 times in the job; `unpersist()` after.
- Tune `spark.sql.shuffle.partitions` to produce ~128-256 MB files. Default 200 is almost always wrong.
- Broadcast joins for small dims (<10 MB filtered). Otherwise check the plan with `.explain()`.
- Avoid row-wise PySpark UDFs. Use built-ins or vectorized pandas UDFs.
- Enable AQE (`spark.sql.adaptive.enabled=true`) for skew and small-file handling.

**Airflow / Dagster / Prefect:**
- Tasks must be idempotent and parameterized by an execution date / partition key.
- Use `data_interval_start` / `data_interval_end` — never `datetime.now()` inside a task.
- External secrets backend. Never hard-code credentials.
- Explicit `retries`, `retry_delay`, `execution_timeout`, `sla` per task. `catchup=False` for new DAGs unless backfill is intended.

**Streaming:**
- Decide explicitly: at-least-once vs. exactly-once vs. at-most-once.
- Define watermark and allowed lateness up front. Late events need a destination (drop / side-output / correction).
- Checkpoint to durable storage; document recovery procedure.
- Schema evolution through a schema registry (Confluent, Glue) with documented compatibility rules.

### Phase 5 — Verify Before Declaring Done

A data pipeline is not complete until you have verified:

- **Row count** — expected vs. actual at each layer, with tolerance.
- **Grain** — `count(*) == count(distinct primary_key)` on every table.
- **Referential integrity** — every FK has a corresponding PK row (or is intentionally nullable).
- **Freshness** — source max timestamp within SLA.
- **Reconciliation** — end-to-end totals match source of truth.
- **Backfill rerun** — re-running for an arbitrary historical window produces the same result.

Run the actual queries. Do not claim success from "it compiled" or "dbt run succeeded." See the relevant playbook in `references/playbooks/`.

### Phase 6 — Operationalize

Before handoff:

- **Monitoring** — row-count anomaly detection, freshness alerts, test failures routed to on-call.
- **Lineage** — documented (dbt docs, OpenLineage, Datahub / Atlan).
- **Cost** — measured per run; bytes scanned or credits consumed.
- **Runbook** — how to backfill, how to recover from a failure, who owns what.
- **PII** — tagged in catalog, encrypted at rest and in transit, access-controlled.

Depth: `references/framework/undercurrent-dataops.md` (monitoring / CI), `references/framework/undercurrent-security.md` (PII / access), `references/framework/concept-finops.md` (cost).

## Anti-Patterns — Reject on Sight

If the user (or their code) proposes any of these, push back with the better alternative. Full discussion in the relevant framework reference.

| Anti-pattern | Better alternative |
|---|---|
| `TRUNCATE` + `INSERT` for incremental loads | `MERGE` / partition replace |
| Polling a source DB for changes | CDC (Debezium / native streams) |
| Surrogate keys via `ROW_NUMBER()` | Deterministic hash of natural key |
| Storing JSON blobs and parsing at read time | Flatten in staging unless schema is truly dynamic |
| One giant Spark job doing everything | Break into stages with persisted intermediate outputs |
| Cron + bash as "orchestration" | Real orchestrator with retries, lineage, observability |
| Pandas for "big data" | Polars / DuckDB / Spark |
| Tests only on synthetic data | Also run CI against a recent slice of production data |
| "We'll add monitoring later" | No, you won't. Add it now |
| `SELECT *` in production models | Name every column you need |
| `DISTINCT` over wide rows | Usually a join-cardinality bug; prove duplicates are real first |

## Common Rationalizations

| Excuse | Reality |
|---|---|
| "Simple pipeline, no need for tests" | Simple pipelines silently corrupt data too. Add grain + not-null tests at minimum. |
| "Backfill is one-time, skip idempotency" | "One-time" events become twice. Always idempotent. |
| "Just poll the source DB, CDC is overkill" | Poll = missed updates + source-side load. Use CDC. |
| "The warehouse is fast, SELECT * is fine" | Cost + schema-change fragility. Name columns. |
| "We'll measure cost later" | By then the bill is what measures you. Measure now. |
| "Pandas works on my laptop" | Works until the data grows 3x. Use the right tool. |
| "Mock the source in tests — easier" | Mock / prod divergence hides broken migrations. Hit a real DB in CI. |

## Supporting Playbooks

Procedural runbooks to invoke during Phase 1-6 work. Load the relevant one when the task matches.

- `references/playbooks/design-new-pipeline.md` — starting a new pipeline from scratch
- `references/playbooks/review-data-pr.md` — reviewing a DE pull request
- `references/playbooks/choose-technology.md` — picking a tool with a reversibility test
- `references/playbooks/fix-broken-job.md` — systematic debugging for data jobs
- `references/playbooks/model-a-fact-table.md` — grain, keys, SCDs, partitioning
- `references/playbooks/plan-a-backfill.md` — safe historical reprocessing
- `references/playbooks/design-data-contract.md` — producer / consumer agreement template

## Conceptual Depth

Cited from answers when a question needs more than one screen of context. Each file cites Reis & Housley plus 2-3 additional sources.

**Lifecycle stages:**
- `references/framework/00-data-engineering-lifecycle.md` — the four stages + undercurrents (start here)
- `references/framework/01-generation.md` — source systems, OLTP / OLAP / HTAP, CDC, events vs. batch
- `references/framework/02-storage.md` — object stores, warehouses, lakehouse, file formats, hot / warm / cold tiers
- `references/framework/03-ingestion.md` — push / pull / poll, batch vs. stream, idempotency, exactly-once semantics
- `references/framework/04-transformation.md` — modeling styles, dbt / Spark patterns, medallion layers
- `references/framework/05-serving.md` — analytics, ML feature serving, reverse ETL, data products

**Undercurrents:**
- `references/framework/undercurrent-security.md` — PII, encryption, access control, compliance
- `references/framework/undercurrent-data-management.md` — governance, catalog, master data, lineage, contracts
- `references/framework/undercurrent-dataops.md` — CI for data, testing, observability, SLAs / SLOs, DORA metrics
- `references/framework/undercurrent-architecture.md` — principles of good architecture, reversibility, trade-offs
- `references/framework/undercurrent-orchestration.md` — DAG patterns, idempotent tasks, Airflow / Dagster / Prefect
- `references/framework/undercurrent-software-engineering.md` — DE as software; types, tests, reviews

**Concepts:**
- `references/framework/concept-finops.md` — cost awareness, cheap-by-default, cost monitoring
- `references/framework/concept-maturity-model.md` — Starting / Scaling / Leading with data
- `references/framework/concept-type-a-vs-b.md` — role archetypes, abstraction vs. tool-building
- `references/framework/concept-data-mesh.md` — Dehghani's four principles, domain ownership, data as a product, federated governance
- `references/framework/concept-etl-vs-elt.md` — ETL vs. ELT vs. EtLT, when each fits, decision framework

## Scripts (Runnable Checkers)

Run the relevant one when asked to review code. All stack-agnostic Python 3.10+, no cloud deps.

- `scripts/sql_anti_patterns.py` — scan `.sql` files for common issues (`SELECT *`, `TRUNCATE+INSERT`, `ROW_NUMBER` as key, etc.)
- `scripts/dbt_project_audit.py` — audit a dbt project (missing tests, incremental without `unique_key`, orphan models, etc.)
- `scripts/dag_idempotency_check.py` — lint Airflow / Dagster / Prefect DAG files for idempotency violations
- `scripts/schema_contract_diff.py` — diff two schemas; classify changes as additive / breaking / semantic
- `scripts/data_profile.py` — profile a CSV / Parquet dataset (nulls, cardinality, grain candidates, PK guess)
- `scripts/lifecycle_checklist.py` — interactive CLI that walks the Phase 1 contract questions and emits a design skeleton

Each supports `--help` and `--json`. Non-zero exit on failures. Invoke via `python scripts/<name>.py`.

## Output Style

- State the phase you are in.
- Cite sources inline: `(Reis & Housley 2022, ch. 7)`, `(Kimball DW Toolkit, ch. 2)`, `(dbt docs — incremental models)`.
- State assumptions explicitly.
- Be decisive — pick an approach, justify it in one sentence, move forward.
- Use `file_path:line_number` when referencing code.

## Related Skills

- `superpowers:test-driven-development` — writing failing tests first when adding pipeline logic
- `superpowers:systematic-debugging` — rooting-cause broken jobs before proposing fixes
- `superpowers:verification-before-completion` — confirming a fix before claiming success
