# Stage 3 — Transformation

**Concept anchor:** Reis & Housley 2022, ch. 8 ("Queries, Modeling, Transformation").
**Also drawing from:** Kimball *The Data Warehouse Toolkit* (3rd ed.); Inmon *Building the Data Warehouse* (4th ed.); Linstedt *Building a Scalable Data Warehouse with Data Vault 2.0*; dbt Labs documentation; Narrator *Activity Schema* docs.

---

## What this stage is

Turning raw ingested data into modeled, business-meaningful datasets ready to serve. Where the majority of data-engineering code lives.

## Modeling styles

Pick by use case, not by preference. Each style makes different trade-offs.

| Style | Best for | Grain example | Strengths | Weaknesses |
|---|---|---|---|---|
| **Kimball (star schema)** | BI / analytics marts | One row per fact event | Analyst-friendly, fast BI queries | Multiple sources hard to integrate; conforming dims is work |
| **Inmon (3NF enterprise DW)** | Central source of truth, many downstream marts | Normalized entities | Consistency, minimal redundancy | Expensive queries, hard to teach analysts |
| **Data Vault 2.0** | Many sources, heavy audit / lineage, regulated industries | Hubs / links / sats | Highly auditable, schema-flexible | Query complexity; overkill for small teams |
| **One Big Table (OBT)** | ML features, simple BI, cheap storage | One row per entity-time | Simplest consumer access | Joins hidden in build-time logic |
| **Activity Schema** | Event / customer-journey analytics | One row per activity | Simple to extend with new activities | Poor fit for non-event data |

**Default for new analytics marts:** Kimball star schema. Default for ML feature stores: OBT. Default for heavily-regulated multi-source integration: Data Vault.

## Layered architecture (medallion-style)

Standard three-layer convention (names vary: raw/staging/marts, bronze/silver/gold, landing/core/presentation — same idea):

- **Raw / Bronze** — immutable, source-faithful, only renames and type casts. No business logic. Safe to drop and re-ingest.
- **Staging / Silver** — cleaned, deduplicated, conformed types, surrogate keys assigned. One model per source table typically. Idempotent rebuild.
- **Marts / Gold** — business-meaningful, joined, aggregated. Owned by the consuming domain.

**Hard rules:**
- Business logic never leaks into bronze.
- Raw source columns never leak into marts (rename to business terms at staging).
- Every model declares its grain in its description.

## Dimensional modeling essentials

**Fact table** — rows represent events or measurements. Has foreign keys to dims plus numeric measures. Grain should be declared in a comment on every fact table: "one row per line item per order."

**Dimension table** — rows represent entities (customer, product, date). Has descriptive attributes. Surrogate keys over natural keys for stability.

**Slowly Changing Dimensions (SCD):**
- **Type 1** — overwrite (no history). Use for corrections.
- **Type 2** — new row per change with `valid_from` / `valid_to` / `is_current`. Standard for business attributes you want to analyze historically.
- **Type 3** — add a "previous value" column. Rarely correct; use Type 2 instead.

Implement Type 2 via dbt snapshots (`check` or `timestamp` strategy) or Iceberg/Delta MERGE with effective-dated logic.

## dbt essentials (most common transformation tool today)

- Use `ref()` / `source()` — never hard-coded names.
- Materializations: `view` (cheap, always fresh), `table` (moderate cost, repeated reads), `incremental` (large append-mostly facts), `ephemeral` (small CTE helpers).
- Incremental models: **always** set `unique_key` and `incremental_strategy` (`merge`, `delete+insert`, `insert_overwrite`).
- Tests at boundaries: `unique` / `not_null` on grain keys, `relationships` on FKs, `accepted_values` on enums, source freshness on all sources.
- Deterministic surrogate keys: `dbt_utils.generate_surrogate_key(['col_a','col_b'])`. Never `row_number()`.
- SCD Type 2: dbt snapshots.

## Spark essentials (when warehouse SQL isn't enough)

- DataFrame API > RDDs. Spark SQL for set logic.
- Avoid `collect()` / `toPandas()` on large data.
- Cache only when reused ≥2 times; `unpersist()` after.
- Tune `spark.sql.shuffle.partitions` so output files land at 128–256 MB.
- Broadcast joins for dims <10 MB (post-filter).
- Avoid row-wise PySpark UDFs (per-row serialization). Use built-ins or pandas UDFs.
- Enable AQE (`spark.sql.adaptive.enabled=true`) for skew handling and dynamic partition pruning.
- Partition output by the columns used in downstream filters.

## Transformation anti-patterns

- `SELECT *` in a model — breaks downstream silently when schema shifts; scans unused columns.
- `ROW_NUMBER()` as surrogate key — non-deterministic across runs.
- `DISTINCT` over wide rows — usually a join-cardinality bug; prove duplicates are real before masking.
- Business logic in raw/bronze — impossible to replay cleanly.
- Ad-hoc date-dimension hacks — maintain one `dim_date` and reuse everywhere.
- Narrow models with 20 joins per query — consolidate at silver or gold, don't push join burden to consumers.
- Deep view chains (view on view on view) — kills query planner and makes debugging opaque.

## See also

- Modeling a specific fact table: `../playbooks/model-a-fact-table.md`
- Serving the modeled data: `05-serving.md`
- Cost impact of materializations: `concept-finops.md`
- ETL vs. ELT (where transformation runs): `concept-etl-vs-elt.md`
