# Concept — Data Maturity Model

**Concept anchor:** Reis & Housley 2022, ch. 1 (the three-stage data maturity model).
**Also drawing from:** dbt Labs "Analytics Engineering Maturity Model"; DAMA *DMBOK2* maturity framings; Monte Carlo "Data Maturity Curve."

---

## Why it matters

The "right" data-engineering advice depends on where the organization is. Advice that is mandatory at Stage 3 is premature at Stage 1. This model helps identify the current stage and what to invest in next, versus what to defer.

## Stage 1 — Starting with data

**Characteristics:**
- Data exists but is rarely used in decisions.
- Reporting is manual, ad-hoc, one-off.
- No central data team (or one person wearing many hats).
- Most "analytics" is spreadsheets pulled from operational systems.
- Data quality issues surface anecdotally.

**What to invest in:**
- A single analytical destination (one warehouse / lakehouse, not five).
- Basic ingestion from the 3–5 most important sources.
- A BI tool that non-engineers can use.
- Documentation of "where data lives" — even a wiki page.
- A first pass at PII tagging before ingesting more.

**What to defer:**
- Heavy governance programs, enterprise catalog tooling, complex modeling methodologies (Data Vault, advanced Data Mesh), feature stores, real-time streaming.

**Failure mode:** Attempting to build "the right data platform" before any actual analytical use case is served. The platform never gets finished.

## Stage 2 — Scaling with data

**Characteristics:**
- Multiple teams consume data; dashboards are in active use.
- Data team (3–15 people) exists and is swamped with requests.
- Pipelines break regularly; trust is partial.
- Schema changes cause outages.
- Cost is growing faster than usage.

**What to invest in:**
- Testing discipline (grain, not_null, relationships on critical tables).
- Basic observability (freshness alerts, row-count anomaly detection).
- Data contracts with the most important producers.
- Cost monitoring per pipeline / consumer.
- Catalog (even dbt docs is a start) with ownership declared.
- Code review, CI, version control for all pipeline code.

**What to defer:**
- Full Data Mesh reorganization; exotic table formats if current warehouse is working; full-blown enterprise MDM.

**Failure mode:** Stage-2 orgs often try to leap to Stage-3 tooling (complex governance, multi-domain mesh) without having consolidated the Stage-2 basics. Result: expensive tooling, unchanged pain.

## Stage 3 — Leading with data

**Characteristics:**
- Data is embedded in operational decisions, not just reporting.
- ML features are productionized; reverse ETL feeds operational systems.
- Data team is decentralized or federated; domain teams own their products.
- SLAs and SLOs are in place and measured.
- Cost is actively managed, not just observed.

**What to invest in:**
- Federated / data-mesh organization if scale warrants.
- Mature data contracts between domains.
- Feature stores for ML.
- Real-time where the use case actually demands it.
- Sophisticated governance (lineage, column-level masking, audit).
- Platform-as-a-product mindset for the internal data platform team.

**Failure mode:** Stage-3 orgs risk over-engineering. Every new framework gets adopted; tooling complexity grows faster than value delivered.

## How to identify the current stage

Questions:
- Do non-data-team members make daily decisions using data? (no = 1, yes = 2/3)
- Do multiple teams own different data products? (no = 1/2, yes = 3)
- Do pipelines have tests, monitoring, and documented owners? (no = 1, partial = 2, full = 3)
- Is data embedded in production operations (not just reports)? (no = 1/2, yes = 3)
- Does the org treat data platform as a product with its own roadmap? (no = 1/2, yes = 3)

Majority answers map to the current stage. Investment priorities should target the next stage, not two stages ahead.

## Anti-patterns

- **Cargo-culting** — adopting Netflix / Airbnb / Uber architecture at Stage 1. Their constraints aren't yours.
- **Framework collecting** — each Stage 2 pain point met with a new tool rather than consolidating existing tools.
- **Stage-skipping** — reorganizing into Data Mesh before consolidating basic quality. Distributing a mess distributes the mess.
- **Perpetual Stage 1** — never standardizing, every team rebuilding basics, "we're a startup" forever.

## See also

- Architecture principles across stages: `undercurrent-architecture.md`
- DataOps maturity specifically: `undercurrent-dataops.md`
