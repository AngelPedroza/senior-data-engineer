# Concept — FinOps for Data

**Concept anchor:** Reis & Housley 2022, ch. 4 (cost as a first-class architectural concern).
**Also drawing from:** FinOps Foundation framework (finops.org); Snowflake / BigQuery / Databricks cost-management docs; Jordan Tigani "Big Data is Dead" (2023); "The Cost of Cloud" (a16z 2021).

---

## Why cost is a feature

On cloud data platforms, a query that scans 10 TB when it could scan 10 GB is not an optimization opportunity — it's a bug. Cost decisions compound: an inefficient model is queried a thousand times before anyone notices the bill.

## The three cost axes

1. **Storage** — data at rest. Cheap per-GB, but grows linearly forever if retention isn't enforced.
2. **Compute** — queries, jobs, clusters. The variable cost; usually the largest line item.
3. **Egress / movement** — inter-region, inter-cloud, vendor-to-vendor transfers. Easy to accidentally dominate.

## Warehouse-specific cost models

| Warehouse | Cost driver | Levers |
|---|---|---|
| **Snowflake** | Virtual warehouse credits (size × time running) | Right-size warehouses, auto-suspend, resource monitors, result cache |
| **BigQuery (on-demand)** | Bytes scanned | Partition pruning, column selection, materialized views, slot commitments to cap |
| **BigQuery (capacity)** | Reserved slots | Slot reservation sizing, workload management |
| **Redshift** | Node-hours (provisioned) or bytes scanned (serverless) | Cluster sizing, pause/resume, workload management |
| **Databricks SQL** | DBU × instance-hours | Cluster sizing, autoscaling, spot instances |

Read your platform's billing docs. Guessing costs more than reading.

## Query-level cost practices

- **Filter early, project early** — push predicates and column selection above the first join.
- **Partition pruning** — queries must include the partition column in `WHERE`. Validate with `EXPLAIN` / dry-run.
- **Avoid `SELECT *`** — cost + schema fragility.
- **Materialized views** for expensive repeated queries (check per-platform semantics).
- **Result cache** — same query within cache TTL returns instantly at no cost (Snowflake, BigQuery).
- **Clustering / Z-order** on high-cardinality filter columns after partitioning.

## Pipeline-level cost practices

- **Right-size materializations** — don't rebuild a 1TB table hourly if consumers need daily data.
- **Incremental models** where append-mostly.
- **Ephemeral / view materializations** for cheap-to-compute logic.
- **Lakehouse compaction schedule** — small-file problem wastes compute on every read.
- **Vacuum / time-travel retention** — lakehouse time travel is not free; set retention per table.

## Cost observability

Measure before optimizing. Minimum:
- **Per-model / per-job cost** — tag queries with model names (Snowflake `QUERY_TAG`, BigQuery labels).
- **Daily cost dashboard** — broken down by warehouse / user / query tag.
- **Cost anomaly alerts** — notify on unexpected spikes (a bad `WHERE` clause on a 100 TB table).
- **Per-consumer attribution** — analytics vs. ML vs. ops, so chargeback is possible.

## FinOps practices (from the FinOps Foundation framework)

- **Inform** — make costs visible to engineers. Invisible costs are never optimized.
- **Optimize** — continuous improvement; right-sizing; eliminating waste (idle clusters, never-queried tables).
- **Operate** — policies, quotas, budget alerts. Resource monitors that cut off runaway usage.

## Anti-patterns

- No cost visibility per pipeline — "the warehouse bill grew" with no attribution.
- Running BI dashboards on raw ingested data — every dashboard refresh is a fresh full scan.
- Auto-suspend disabled on warehouses — idle compute costs real money.
- "We'll optimize later" — three months of waste is cheaper to prevent than fix.
- Cross-region replication for data that never leaves one region — egress and storage duplication.
- Never-queried tables accumulating indefinitely — storage cost without value.

## See also

- Storage tiering and retention: `02-storage.md`
- Architecture cost trade-offs: `undercurrent-architecture.md`
