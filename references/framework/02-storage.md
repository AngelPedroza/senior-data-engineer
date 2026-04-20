# Storage

**Concept anchor:** Reis & Housley 2022, ch. 6 ("Storage").
**Also drawing from:** Armbrust et al. "Lakehouse: A New Generation of Open Platforms" (CIDR 2021); Apache Iceberg spec; Apache Parquet docs; Databricks Delta Lake docs.

---

## What this theme is

Storage is not a single stage — it cuts across ingestion, transformation, and serving. Reis & Housley treat it as its own theme because the storage choice constrains every other decision.

## The three storage archetypes

| Archetype | Example | Optimized for | Watch out for |
|---|---|---|---|
| **Object store** | S3, GCS, ADLS | Cheap bulk storage of files | Eventual consistency, no transactions, slow small-file ops |
| **Data warehouse** | Snowflake, BigQuery, Redshift | Columnar analytics queries | Cost scales with compute; lock-in to one engine |
| **Lakehouse** (object store + table format) | Iceberg / Delta / Hudi on S3 | Open, multi-engine, ACID on object store | Operational complexity; compaction / vacuum required |

Modern default for greenfield analytics: **lakehouse**. Warehouses are still correct when you need a single tightly-integrated platform with strong governance out-of-the-box.

## File formats

| Format | Layout | Use when |
|---|---|---|
| CSV | Row, text | Interchange only. Never as a production format. |
| JSON / JSONL | Row, text | Dynamic schemas, logs. Avoid for large analytical data. |
| Avro | Row, binary | Streaming, schema evolution (Kafka + Schema Registry). |
| ORC | Column, binary | Hive ecosystems. |
| **Parquet** | Column, binary | **Default for analytics.** Columnar, compressed, widely supported. |

Compression: ZSTD (best ratio) or Snappy (fastest). Use ZSTD unless CPU is the bottleneck.

## Table formats (the lakehouse layer)

Apache Iceberg / Delta Lake / Apache Hudi add a metadata layer on top of Parquet files to provide:

- ACID transactions on object storage
- Schema evolution (add/rename/drop columns safely)
- Partition evolution
- Time travel (query snapshots)
- Hidden partitioning and Z-ordering

| Format | Strength | Weakness |
|---|---|---|
| **Iceberg** | Open spec, multi-engine (Spark, Flink, Trino, Snowflake, BigQuery), evolving partitioning | Smaller ecosystem than Delta |
| **Delta** | Deep Databricks integration, Unity Catalog, mature tooling | Strongest outside Databricks but less neutral |
| **Hudi** | Strong record-level upsert / CDC sink performance | More operational complexity; less adopted |

**Default recommendation for new lakehouse projects: Iceberg.** Delta is correct if Databricks-centric. Hudi is correct if CDC-heavy write workload.

## Partitioning and clustering

- **Partition by** the high-cardinality column queried most (usually a date: `event_date`). Partition pruning is a correctness-adjacent concern — if a query scans all history, it is a cost bug.
- **Cluster / Z-order by** the filter / join columns queried most after the partition.
- **Avoid over-partitioning** — too many small partitions cause metadata overhead and small-file problems.

Target file size after compaction: 128 MB–1 GB per file for Parquet.

## Storage tiers

Hot / warm / cold lifecycle policies move old partitions to cheaper storage classes (S3 Standard → IA → Glacier). Automate via object-store lifecycle rules. Track which partitions are queryable at which latency.

## Retention

Every dataset needs a documented retention policy. "Forever" is not a policy — it is a cost and compliance risk. PII data often has regulated maximum retention (GDPR). See `undercurrent-security.md`.

## Anti-patterns

- Storing production analytical data as CSV → no schema, no types, unpredictable parsing.
- Parquet files <10 MB → small-file problem; hurts scan performance.
- Partition columns derived at query time (e.g., computing month from timestamp) → no pruning.
- No vacuum / compact schedule on lakehouse tables → metadata bloat, slow reads.
- Using a warehouse as a dumb file store (billing compute to scan raw dumps) → pay for raw ingestion that belongs in object storage.

## See also

- Table-format modeling: `04-transformation.md`
- Cost implications: `concept-finops.md`
