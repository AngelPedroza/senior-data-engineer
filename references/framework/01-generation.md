# Stage 1 — Generation (Source Systems)

**Concept anchor:** Reis & Housley 2022, ch. 5 ("Data Generation in Source Systems").
**Also drawing from:** Kleppmann *Designing Data-Intensive Applications* ch. 1, 11; Kimball *DW Toolkit* ch. 3; Debezium documentation.

---

## What this stage is

The systems that *produce* data. Not owned by the data team, but must be understood. Misunderstanding the source is the root cause of most downstream bugs.

## Source system archetypes

| Type | Examples | Update semantics | Extraction |
|---|---|---|---|
| OLTP RDBMS | Postgres, MySQL, SQL Server | Mutable rows | CDC preferred; full snapshot fallback |
| OLAP warehouse | Snowflake, BigQuery | Append-mostly | Read-replica or warehouse-to-warehouse share |
| SaaS API | Salesforce, Stripe, Zendesk | Mutable, no CDC usually | Incremental API with `updated_at` filter |
| Event stream | Kafka, Kinesis, PubSub | Append-only | Consume from offset |
| File drops | S3 / SFTP / email | Append | Watch bucket; process on arrival |
| Application logs | stdout, structured logs | Append | Log aggregator → stream |
| Mobile / web telemetry | Segment, Snowplow, custom | Append | SDK → collector → stream |
| IoT | MQTT, device streams | Append, possibly late | Buffer → stream |

## What you must discover before ingesting

1. **Schema** — columns, types, nullability, foreign keys. Is it documented? Enforced?
2. **Volume** — rows/day, total rows, growth rate, burstiness.
3. **Update semantics** — append-only, updatable, deletable? Soft-delete or hard?
4. **Timestamps** — is there a reliable `updated_at` / `event_time`? Can you detect late data?
5. **Stability** — how often does the schema change? Who changes it? Are you notified?
6. **Extraction cost** — does reading hurt the source? What's the allowed concurrency?
7. **Authentication and rate limits** — credentials, quotas, retry behavior.

If any of these are unknown, you are guessing. Record what you learn; it becomes part of the data contract.

## OLTP vs. OLAP vs. HTAP

- **OLTP** (row-oriented, indexed for point lookups) — optimized for many small transactions. Reading large ranges is expensive and can contend with writes. Ingest via CDC.
- **OLAP** (column-oriented, compressed, scan-optimized) — optimized for analytical queries. Not usually a source; sometimes a source when reverse-ETL feeds another system.
- **HTAP** (hybrid, e.g., SingleStore, TiDB) — tries to serve both. Rare as a source; treat as OLTP for safety.

Never run analytical queries directly against the OLTP primary in production — use a read replica, logical replication, or CDC.

## Change Data Capture (CDC)

Three implementation patterns:

1. **Log-based** (preferred) — read the database WAL / binlog (Debezium). Low source load, captures every change including deletes, preserves order.
2. **Trigger-based** — database triggers write to an audit table; ingest the audit table. Source-side overhead.
3. **Query-based** — periodically poll with a `WHERE updated_at > last_run`. Misses deletes and intra-poll updates. Use only when nothing else is available.

Log-based CDC is the standard. Query-based polling is an anti-pattern for anything more than occasional data.

## Anti-patterns at the generation boundary

- Scraping the OLTP primary during business hours → source performance incidents.
- Ingesting without capturing soft-deletes → ghost rows downstream.
- Trusting the source schema without a snapshot baseline → silent breaks on upstream migrations.
- No `updated_at` field → forced to full-snapshot or miss updates.
- Accepting "just use the API" without reading the rate-limit page → throttled pipelines.

## What to do when source quality is bad

Reis & Housley's term is "upstream problems." Document them, quantify them, report them. The data team does not fix source-system quality unilaterally, but surfacing the problem with evidence is part of the role.

## See also

- Ingestion: `03-ingestion.md`
- Data contracts between source and ingestion: `../playbooks/design-data-contract.md`
