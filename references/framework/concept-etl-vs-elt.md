# Concept — ETL vs. ELT (vs. EtLT)

**Concept anchor:** Reis & Housley 2022, ch. 3 ("Designing Good Data Architecture") and ch. 8 ("Queries, Modeling, Transformation").
**Also drawing from:** Kimball *DW Toolkit* ch. 19 (the classic ETL view); dbt Labs "Analytics Engineering" blog series (the ELT framing); Snowflake "ELT with Snowflake" docs; Databricks lakehouse documentation; Fivetran / Airbyte product docs.

---

## The core distinction

| Pattern | Order | Where does transform run |
|---|---|---|
| **ETL** | Extract → Transform → Load | In a dedicated engine *before* loading the target |
| **ELT** | Extract → Load → Transform | *Inside* the target system (typically warehouse SQL) |
| **EtLT** | Extract → light-transform → Load → heavy-transform | Pragmatic hybrid — light work before load (type casts, PII scrub), heavy work after |

The order swap sounds cosmetic; the consequences are architectural. It changes where compute lives, what raw history you keep, and who owns the transformation layer.

## Why ELT became the default

Pre-cloud, ETL dominated because on-prem warehouses (Teradata, Netezza, early Oracle) had expensive, non-elastic compute. Transforming in a separate engine (Informatica, DataStage, SSIS) was cheaper than hammering the warehouse.

Cloud warehouses (Snowflake, BigQuery, Redshift, Databricks SQL) changed two economics:
1. **Elastic compute** — warehouses can scale up for transformation workloads and scale back down.
2. **Separation of storage and compute** — raw history is cheap to keep; recomputing against it is fast.

dbt formalized the ELT workflow: land raw, model in SQL, version-control the transformations. Modern default since ~2015.

## When ELT is right

- **Target is a cloud warehouse or lakehouse** with elastic compute (Snowflake, BigQuery, Redshift, Databricks, Trino on Iceberg).
- **Raw history has independent value** — audit, replay, re-modeling without re-ingesting.
- **SQL-dominant team** — analysts can own transformations.
- **Iteration speed matters** — new marts on top of the same raw land without touching ingestion.
- **Storage is cheap relative to engineer time** — almost always true on cloud object storage.

Typical stack: **Fivetran / Airbyte / Stitch / Debezium** (EL) + **dbt / warehouse-native SQL** (T) + **Airflow / Dagster** (orchestration).

## When ETL is right

- **Target cannot transform** — operational APIs, transactional databases, SaaS systems. Reverse ETL (Hightouch, Census, Polytomic) is ETL under a different name: warehouse → operational tool.
- **Compliance or PII** mandates scrubbing before data lands. Healthcare, some financial services, strict GDPR-sensitive workloads.
- **Source volume dwarfs useful signal** — massive event streams where aggregates are the value; transform in flight to avoid landing petabytes of noise.
- **On-prem / legacy** warehouse without elastic compute.
- **Strict schema enforcement at load** — traditional RDBMS targets, contract-enforced sinks.
- **Streaming transformations** — Flink / Kafka Streams / Spark Structured Streaming doing windowed aggregates before write. This is stream-time ETL by any reasonable definition.

Typical stack: **Informatica / DataStage / SSIS / Talend** (classic ETL); **Spark / Flink jobs** (modern stream/batch ETL); **Fivetran + in-flight transforms** for reverse-ETL.

## EtLT — the realistic middle ground

Reis & Housley point out that most "ELT" shops actually do EtLT:
- Before load (*light*): type casting, column renaming, obvious PII masking, schema enforcement.
- After load (*heavy*): joins, modeling, aggregations, business logic.

This is pragmatic — keeps the "land raw" benefit while solving compliance / type-safety at the boundary. Don't treat "pure ELT" as a dogma.

## Decision framework

| Question | ELT | ETL |
|---|---|---|
| Target is a cloud warehouse / lakehouse? | yes | no |
| Keep raw history for replay / audit? | yes | no |
| Must scrub PII *before* landing? | no | yes |
| Source volume ≫ useful signal? | no | yes |
| Target executes SQL / compute? | yes | no |
| SQL-dominant team? | yes | no |
| Streaming transforms (windowed aggregates)? | no | yes |
| Target is an operational SaaS / API? | no | yes (reverse ETL) |

Mostly "yes" on the left → ELT. Mostly "yes" on the right → ETL. Mixed → EtLT or split the pipeline.

## Common architectural shapes

- **Inbound ELT + outbound reverse ETL** — ELT into the warehouse for analytics; ETL out for SaaS syncs (reverse-ETL). Most large orgs today.
- **Streaming ETL + batch ELT** — Flink / Spark Streaming produces aggregated events; those events land raw and get modeled in dbt. Hybrid by stage.
- **Pure ELT** — appropriate for analytics-only shops on a cloud warehouse, no operational outputs, no regulated PII-pre-landing requirement.
- **Pure ETL** — appropriate for regulated / legacy shops, or for pure reverse-ETL use cases.

## Anti-patterns

- **ELT on a non-elastic target** — running heavy SQL in an on-prem warehouse that can't scale; you've recreated the 2005 bottleneck.
- **"ELT" that's actually ETL** — loading data through a Python script that reshapes it first, then calling it ELT because the storage is cloud. The pattern is defined by where transformation runs, not where data lives.
- **Landing raw PII you're not allowed to store** — ELT without upstream masking violates the "raw history forever" assumption in regulated contexts.
- **Reinventing Informatica in SQL** — 2000-line stored procedures because "we do ELT now." ELT's value is dbt-style modularity + tests; losing that loses the point.
- **Treating ETL as obsolete** — it isn't. Stream-time transforms, reverse-ETL, and compliance scrubbing are all legitimate and common.

## Cost implications

- **ELT**: storage cheap, compute spiky during transformation runs. Monitor per-model cost (`concept-finops.md`). Watch for full-table scans on giant raw tables.
- **ETL**: compute in a separate engine (often fixed-cost cluster), but the target sees only clean data — so target cost is lower. Trade-off: engine licensing / ops vs. warehouse compute.

## See also

- Ingestion patterns (push/pull/poll, CDC): `03-ingestion.md`
- Transformation modeling (dbt / Spark / warehouse SQL): `04-transformation.md`
- Architecture reversibility and trade-offs: `undercurrent-architecture.md`
- Serving via reverse ETL: `05-serving.md`
- Cost of each pattern: `concept-finops.md`
