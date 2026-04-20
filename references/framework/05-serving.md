# Stage 4 — Serving

**Concept anchor:** Reis & Housley 2022, ch. 9 ("Serving Data for Analytics, Machine Learning, and Reverse ETL").
**Also drawing from:** Dehghani, "How to Move Beyond a Monolithic Data Lake to a Distributed Data Mesh" (martinfowler.com, 2019) + "Data Mesh Principles" (martinfowler.com, 2020) + *Data Mesh* book (O'Reilly, 2022); ThoughtWorks "Data Products" radar; Feast / Tecton feature-store docs; Hightouch / Census reverse-ETL docs.

---

## What this stage is

Making transformed data usable by humans and systems. Three primary serving patterns, each with different requirements.

## Pattern 1 — Analytics serving

Consumers: BI tools (Looker, Tableau, Power BI, Metabase), ad-hoc SQL users, dashboards, embedded analytics.

Requirements:
- **Query latency** — seconds for dashboards, minutes tolerable for ad-hoc.
- **Concurrency** — many concurrent users during business hours.
- **Semantics** — one version of the truth; conformed dims; defined metrics.

Serve from:
- Warehouse tables or materialized views (Snowflake, BigQuery, Redshift).
- Lakehouse tables via query engines (Trino / Starburst, Databricks SQL, Athena).
- **Semantic layer** (dbt Semantic Layer, Cube, AtScale, LookML) — the single place metrics are defined. Prevents drift between dashboards.

## Pattern 2 — ML feature serving

Consumers: offline training jobs and online inference services.

Two distinct access paths:
- **Offline store** — historical feature values joined at training time. Often the same warehouse/lakehouse as analytics.
- **Online store** — low-latency point lookups at inference time (Redis, DynamoDB, Cassandra, Tecton-managed).

**Training / serving skew** is the central risk: if the feature computation differs between offline training and online inference, the model silently degrades. Feature stores (Feast, Tecton, Databricks Feature Store) solve this by computing features once and serving both paths.

Feature requirements:
- Point-in-time correctness — a feature at time T uses only data known at time T. Preventing leakage is non-negotiable.
- Low-latency read at inference (<50 ms p99 typical).
- Materialization pipelines that keep offline and online in sync.

## Pattern 3 — Reverse ETL

Taking warehouse / lakehouse data and pushing it back into operational SaaS tools (Salesforce, HubSpot, Zendesk, Marketo, etc.). Tools: Hightouch, Census, Polytomic.

Use cases:
- Synced customer scores to CRM.
- Product usage data to customer success tools.
- Warehouse-computed segments to marketing automation.

Requirements:
- **Idempotency at the destination** — upserts on stable keys; no duplicate records in the SaaS tool.
- **Frequency tuning** — many SaaS APIs rate-limit aggressively.
- **Operational observability** — failures here affect revenue-adjacent teams directly, not just analytics.

## Data products (Data Mesh framing)

Dehghani's reframing: don't think of serving as a step; think of each served dataset as a **data product** with:

- **Discoverable** — registered in a catalog with metadata.
- **Addressable** — stable location / URI.
- **Trustworthy** — SLAs on freshness, completeness, and correctness.
- **Self-describing** — schema, grain, semantics documented.
- **Interoperable** — standard formats (Parquet, JSON Schema, Avro).
- **Secure** — access controls and PII handling defined.
- **Owned** — a named domain team, not "the data team."

Even outside full Data Mesh adoption, these seven properties are a useful checklist for "is this served dataset production-ready?"

## Serving anti-patterns

- Dashboards reading raw / bronze tables directly — bypasses modeling, couples BI to source schema.
- Metric definitions duplicated across dashboards — guaranteed drift, no single answer.
- Feature engineering in notebooks that never gets productionized — training-serving skew on first deployment.
- Reverse ETL without idempotency — duplicate Salesforce records, downstream operational chaos.
- No SLA on served datasets — consumers can't tell if the data is fresh.
- "Everything is a view on the warehouse" — unclustered views can't scale to concurrent BI load.

## See also

- Modeling that feeds serving: `04-transformation.md`
- Data contracts for served datasets: `../playbooks/design-data-contract.md`
- Governance of served products: `undercurrent-data-management.md`
- Full Data Mesh treatment (four principles, platform, governance): `concept-data-mesh.md`
