# Stage 2 — Ingestion

**Concept anchor:** Reis & Housley 2022, ch. 7 ("Ingestion").
**Also drawing from:** Kleppmann *DDIA* ch. 11 (streaming); Apache Kafka docs; Debezium CDC guide; Confluent "Streaming Data" ebook.

---

## What this stage is

Moving data from source systems into storage the data team controls, with known semantics and contracts. The boundary where idempotency, exactly-once handling, and schema contracts are established — or first broken.

## Three orthogonal dimensions

1. **Direction** — push (source emits) vs. pull (consumer requests) vs. poll (consumer requests on a schedule).
2. **Shape** — batch (bounded, periodic) vs. stream (unbounded, continuous) vs. micro-batch (small frequent batches).
3. **Semantics** — at-most-once, at-least-once, exactly-once.

Pick each explicitly. Silence about these produces silent data loss or duplication.

## Push vs pull vs poll

- **Push** — source calls an endpoint you expose (webhook). Requires idempotent receiver.
- **Pull** — consumer reads from source on demand (SDK / API). Stateful consumer tracks progress.
- **Poll** — consumer queries periodically with a "since X" filter. Misses deletes and intra-poll updates. Avoid for anything beyond low-volume reference data.

## Batch vs stream vs micro-batch

| Shape | Latency | Complexity | Default use |
|---|---|---|---|
| Batch | Hours / days | Low | Historical analytics, financial reporting |
| Micro-batch | Minutes | Medium | Near-real-time analytics (Spark Structured Streaming) |
| Stream | Sub-second | High | Real-time ops, fraud detection, live personalization |

**Don't reach for streaming unless the use case justifies the complexity.** Streaming pipelines are 3–5x harder to build, test, and operate than batch. When in doubt, micro-batch.

## Idempotency

A pipeline is idempotent if re-running it for the same input produces the same output. Required — not optional.

Patterns:
- **Merge / upsert** with deterministic key (`MERGE INTO target USING source ON key`).
- **Partition replace** — delete the target partition, re-insert. Safe because the replace is atomic within a partition.
- **Full replace** — drop and recreate the entire dataset. Simplest, expensive for large data.

Do NOT use `TRUNCATE + INSERT` in a non-transactional context — a crash mid-operation leaves an empty table.

## Exactly-once semantics

True end-to-end exactly-once is rare and expensive. It requires:
- Transactional source (CDC from WAL with offset commit)
- Transactional sink (ACID writes with deterministic keys)
- Atomic offset-and-write coordination

Most systems settle for **at-least-once + idempotent sink** = effectively exactly-once. This is the pragmatic standard. Examples: Kafka with idempotent producers + upsert sinks; CDC + MERGE.

## Change Data Capture (CDC) as ingestion

The modern default for OLTP-sourced pipelines. Log-based CDC (Debezium reading the WAL) captures every insert / update / delete with order preserved. Produces events like:
```
{op: "u", before: {...}, after: {...}, ts: "...", source: {...}}
```

Sink strategies:
- **Event stream** → Kafka topic per table → downstream consumers apply.
- **Merge into warehouse** → periodically batch-apply events via `MERGE`.

## Backpressure and dead-letter

- **Backpressure** — consumer signals source / broker to slow down. Enforce or you will OOM.
- **Dead-letter queue** — events that fail parsing / validation go to a separate destination for human review, not dropped. Always have one.

## Schema evolution at ingestion

- **Schema registry** (Confluent, Glue) enforces compatibility rules (forward / backward / full) at produce time.
- Without a registry: at minimum, snapshot source schema on every run and diff. Fail or alert on breaking change.

## Anti-patterns

- Polling an OLTP DB for changes (miss deletes, miss intra-poll updates, source load).
- Ingestion that applies business logic (joins, filters) before landing raw — violates stage boundary, makes replay impossible.
- No dead-letter — bad events silently dropped, or pipeline halts forever.
- Idempotency "added later" — refactor cost grows with table age.
- Reaching for streaming when daily batch would do.

## See also

- Source systems: `01-generation.md`
- Orchestration of ingestion: `undercurrent-orchestration.md`
- Designing the contract with the source: `../playbooks/design-data-contract.md`
- ETL vs. ELT decision (where transform runs): `concept-etl-vs-elt.md`
