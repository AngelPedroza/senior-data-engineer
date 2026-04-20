# Playbook — Design a Data Contract

**When to use:** a new dataset is being produced for other teams / systems to consume, or an existing dataset's consumer boundaries are being formalized.
**Related framework:** `../framework/undercurrent-data-management.md`.
**Primary sources:** Chad Sanderson "Data Contracts" series (2023); Andrew Jones *Driving Data Quality with Data Contracts* (2024).

---

## What a data contract is

A formal agreement between a data producer and its consumers about schema, semantics, and service levels. Analogous to an API contract. Makes breaking changes a negotiated event rather than a surprise outage.

Without a contract: the producer's implementation *is* the contract. Consumers build on undocumented invariants, which silently break on refactor.

## Contract components

### 1. Identity

- **Dataset name** — stable, human-readable.
- **Location / URI** — warehouse table, topic, bucket path.
- **Version** — major / minor / patch or equivalent.

### 2. Schema

- Column names and types (with nullability).
- Primary key / uniqueness constraints.
- Foreign-key relationships (if any).
- Column-level descriptions.

### 3. Semantics

- **Grain** — one row per what? (full sentence).
- **Unit / enumeration** for each measure (USD cents? meters? a specific enum list?).
- **Derivation** — is a column raw from the source or computed? If computed, how?
- **Timezone** — UTC unless explicitly stated.
- **Meaning of NULL** — "missing," "not applicable," or "not yet known"?

### 4. SLAs

- **Freshness** — data is produced within X of the source event / end of day / etc.
- **Completeness** — % of expected rows present; how is "expected" defined?
- **Availability** — dataset is readable X% of the time.
- **Correctness** — measurable quality bar (test pass rate, reconciliation match).

### 5. Compatibility policy

- **Additive changes** (new nullable column) — ship at any time, producer notifies.
- **Semantic changes** (meaning of a column shifts) — require consumer coordination.
- **Breaking changes** (rename / drop / narrow type) — require version bump, deprecation window, and consumer sign-off.
- **Deprecation process** — what period does the old version stay available?

### 6. Ownership

- **Producer team / owner** — who maintains, who's accountable.
- **Oncall path** — who gets paged.
- **Consumer list** — known consumers (can be generated from lineage).

### 7. Sensitivity

- **Classification** — public / internal / confidential / restricted.
- **PII columns** — tagged; masking / access rules stated.
- **Retention** — how long data is kept.

## Tools for encoding contracts

Pick tools that fit the stack:

- **dbt `contracts:`** — enforces column names / types at build time for dbt models.
- **JSON Schema / Protocol Buffers / Avro + schema registry** — for streaming and API boundaries.
- **Data Contract CLI** (datacontract.com) — an open spec.
- **Great Expectations expectations** — can encode semantic / quality portions of the contract.
- **Catalog-level definitions** — Datahub / Atlan / Unity Catalog can hold contract fields as metadata.

No single tool captures everything. A pragmatic setup: schema in code (dbt contracts / Avro), semantics in catalog, SLAs in observability tool, policy prose in a markdown file stored with the dataset.

## Process

### When introducing a new dataset

1. Draft the contract *before* implementing the pipeline.
2. Share with expected consumers; revise based on their needs.
3. Implement to the contract; enforce schema via tooling.
4. Publish the contract alongside the dataset in the catalog.
5. Set up monitoring on SLAs.

### When evolving an existing dataset

1. Classify the change: additive / semantic / breaking.
2. For non-additive changes: list affected consumers via lineage.
3. Negotiate deprecation window with consumers.
4. Run old and new versions in parallel until consumers migrate.
5. Enforce breaking-change schema diff in CI (see `scripts/schema_contract_diff.py`).

## Anti-patterns

- **Implicit contract** — producer and consumers have never discussed expectations; first conflict is an outage.
- **"Self-service" without contract** — consumers build on raw tables, producer refactors, everything breaks.
- **Contract documented but unenforced** — no CI check, no monitoring; drifts from reality.
- **Over-specified contract** — 80-page documents nobody reads. Keep it one page per dataset.
- **Contract belongs to "the data team"** — no, it belongs to the producer domain. Ownership matters.
- **No deprecation window** — breaking changes deployed on Tuesday, consumers find out Wednesday.

## One-page contract template (markdown)

```
# Data Contract: <dataset_name>

**Version:** 1.0
**Owner:** <team>
**Classification:** <tier>

## Identity
- Location: <table_or_topic>
- Format: <parquet | json | avro>

## Grain
One row per <sentence>.

## Schema
| column | type | null? | description |
| ... | ... | ... | ... |

## Semantics
- <non-obvious derivations / units / enumerations>

## SLAs
- Freshness: <X>
- Completeness: <%>
- Availability: <%>

## Compatibility
- Additive changes: <process>
- Breaking changes: <process>

## PII / sensitivity
- <list of sensitive columns + handling>

## Consumers
- <known consumer list with contacts>

## Change log
- 2026-04-19 — v1.0 initial publication
```

## See also

- Data management context: `../framework/undercurrent-data-management.md`
- Schema change workflow: `scripts/schema_contract_diff.py`
- Review of a contract change: `review-data-pr.md`
