# Undercurrent — Data Management

**Concept anchor:** Reis & Housley 2022, ch. 2 (undercurrents section on Data Management).
**Also drawing from:** DAMA International *DMBOK2* (Data Management Body of Knowledge); Dehghani, "Data Mesh Principles and Logical Architecture" (martinfowler.com, 2020) + *Data Mesh* book (O'Reilly, 2022); Chad Sanderson "Data Contracts" (2023 blog series); OpenLineage / Marquez documentation.

---

## What this covers

The non-code concerns that make data usable across an organization: governance, cataloging, lineage, master data, contracts, and stewardship.

## Governance

Policies and decision rights about data: who owns it, who decides schema changes, who approves new consumers, what's the retention, what's the classification.

Minimum viable governance for a small team:
- Every dataset has a named owner (team or person).
- PII datasets are tagged and access-controlled.
- Breaking schema changes require owner approval.
- Each dataset declares a retention period.

Heavy governance (committees, multi-stage approval, formal steward rotation) suits large regulated enterprises. Start minimal; add process as scale demands.

## Data catalog

A queryable inventory of all datasets with metadata: schema, owner, description, lineage, freshness, PII tags, usage.

Tools: DataHub, Atlan, Collibra, Alation, OpenMetadata, Amundsen. dbt docs + Great Expectations docs cover a subset.

Without a catalog: analysts rediscover the same tables, schema changes break consumers silently, no single place answers "what does this column mean?"

## Data lineage

Which datasets flow into which. Critical for impact analysis ("if I change column X, what breaks?") and incident investigation ("bad numbers in dashboard Y, where did they originate?").

Sources of lineage:
- **Code-level** — dbt (from `ref()` graph), Dagster (from asset dependencies).
- **Query-level** — parsed from executed SQL logs (OpenLineage, Marquez, SQL parsers).
- **Column-level** (harder) — tools like `sqlglot`-based analyzers or vendor catalogs.

## Master Data Management (MDM)

Single authoritative record for core entities (customer, product, location) across multiple source systems. E.g., "Customer 12345 in Salesforce is the same person as `cust_abc` in the billing DB."

Approaches:
- **Central MDM system** (Informatica, Reltio) — the authoritative record.
- **Identity resolution pipeline** — deterministic (email match) + probabilistic (fuzzy attributes) in your warehouse.
- **Source of truth per domain** — in Data Mesh, each domain owns its entities; cross-domain resolution is explicit.

## Data contracts

A formal agreement between data producer and data consumer about schema, semantics, and SLAs. Inspired by API contracts.

A data contract typically specifies:
- Schema (column names, types, nullability)
- Grain / uniqueness keys
- Semantics (what does each column mean, units, enumerations)
- SLAs (freshness, completeness, availability)
- Compatibility policy (how schema changes are communicated)
- Owner and consumers

Tooling: Protocol Buffers + schema registry, JSON Schema, Data Contract CLI, dbt contracts (`columns:` enforcement), Great Expectations expectations as contract.

Value: breaking changes become a negotiated event, not a surprise outage.

## Stewardship roles

- **Data owner** — accountable for the dataset's correctness, access, and lifecycle.
- **Data steward** — operational role; resolves quality issues, approves access requests, maintains catalog metadata.
- **Data custodian** — manages the technical storage (DBA-like).

Small teams collapse these into one person. Large organizations separate them; confusion about who holds which role is a common root cause of quality issues.

## Data classification

Typical tiers:
- **Public** — marketing data, published reports.
- **Internal** — employee-only but not sensitive.
- **Confidential** — business-sensitive (financials before earnings, strategy).
- **Restricted** — PII, PHI, payment data. Regulated.

Tags drive downstream policies: retention, encryption, masking, replication rules.

## Anti-patterns

- No catalog, no documented owners — every question becomes a Slack archaeology expedition.
- Lineage exists in someone's head, not in tooling.
- Schema changes deployed without notifying consumers — dashboards break, downstream jobs fail.
- PII discovered late, retrofit instead of tagged at ingestion.
- Data contracts implied, not written — disagreements resolve as incidents.

## See also

- Security tagging: `undercurrent-security.md`
- CI enforcement of contracts: `undercurrent-dataops.md`
- Writing a data contract: `../playbooks/design-data-contract.md`
- Decentralized domain ownership (Data Mesh): `concept-data-mesh.md`
