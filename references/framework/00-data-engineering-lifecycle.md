# The Data Engineering Lifecycle

**Concept anchor:** *Fundamentals of Data Engineering*, Reis & Housley 2022, ch. 2 ("The Data Engineering Lifecycle") and ch. 3 ("Designing Good Data Architecture").

**Also drawing from:** Kimball *The Data Warehouse Toolkit* (3rd ed.) ch. 1; Dehghani *Data Mesh* (2022) ch. 2; dbt Labs "Analytics Engineering Maturity Model"; ThoughtWorks Technology Radar on Data Products.

---

## The model

Reis & Housley frame data engineering as a **lifecycle with four stages**:

```
Generation → Ingestion → Transformation → Serving
```

Cutting across every stage are **six undercurrents** — concerns that do not live in any one stage but must be present at every stage:

1. **Security** — who can read / write / delete what
2. **Data Management** — governance, cataloging, lineage, contracts, master data
3. **DataOps** — CI / CD, testing, observability, incident response
4. **Data Architecture** — high-level design principles, reversibility, trade-offs
5. **Orchestration** — scheduling, dependencies, retries, SLA enforcement
6. **Software Engineering** — types, tests, reviews, modularity, reproducibility

The stages describe **what data moves through**. The undercurrents describe **how each stage is done well**. A pipeline that handles all four stages but fails on security or observability is not a finished pipeline; it is a latent incident.

## Why the lifecycle framing matters

Before this framing became standard, data work was described by technology ("ETL", "warehouse", "lake", "streaming"). The tech changes every few years. The lifecycle does not. Framing work by stage makes knowledge portable across stacks.

Kimball's earlier framing (source → staging → presentation) covers the middle of the lifecycle but does not name Generation or Serving as engineering concerns. The lifecycle is broader: it explicitly includes the upstream source systems (which the data engineer must understand, not just consume) and the downstream serving patterns (analytics, ML feature stores, reverse ETL — each with different requirements).

## What belongs in each stage

**Generation** — the source systems. OLTP databases, SaaS APIs, event streams, mobile / web telemetry, IoT, logs. Not produced by data engineering, but must be understood: schema, volume, update semantics (append-only vs mutable), extraction cost, reliability. Ignorance here causes every downstream problem.

**Ingestion** — moving data from source systems into storage the data team controls. Batch vs stream. Push vs pull vs poll. CDC vs full extract. Schema evolution handling. Ingestion is where idempotency contracts are first established — or first broken.

**Transformation** — cleaning, joining, modeling, aggregating. Typically the largest body of code. Modeling choices (Kimball star / Data Vault / OBT / Activity Schema) live here. dbt, Spark, warehouse-native SQL. Layered (medallion-style) to isolate concerns.

**Serving** — making transformed data usable. Analytics queries, BI dashboards, ML feature stores, operational APIs, reverse ETL back to SaaS tools. Serving is where latency and access patterns drive optimization (partitioning, clustering, denormalization).

## How to use the lifecycle when designing

1. **Name the stage.** For any piece of work, state which stage it is in. "This is an Ingestion task" vs "this is a Transformation task" changes the tools, tests, and success criteria.
2. **Walk the undercurrents for that stage.** Even if the task is Ingestion, ask: what are the security implications? the governance implications? the orchestration implications?
3. **Identify the stage boundary.** Most data bugs live at the boundary between two stages — data entered ingestion correctly but lost fidelity on the way to transformation. Instrument those boundaries first.

## How to use the lifecycle when reviewing

- Does the code stay within its stage, or does it smuggle transformation logic into ingestion (e.g., applying business rules before the raw land)?
- Are boundary contracts documented (what columns / types / invariants are emitted)?
- For each undercurrent, is there *something* — even minimal — addressing it? Zero observability is a failing grade regardless of code quality.

## Relation to data mesh and data products

Dehghani's Data Mesh decomposes the monolithic lifecycle into **domain-owned data products** — each of which still traverses the full lifecycle internally, but is owned end-to-end by a single team. The lifecycle is not replaced; it is repeated at each product boundary. A data mesh with N products has N Generation→Serving lifecycles plus N sets of undercurrents.

## Quick reference

| Question | Stage |
|---|---|
| "Where does this data come from?" | Generation |
| "How does it get to us?" | Ingestion |
| "How do we make it usable?" | Transformation |
| "How do consumers access it?" | Serving |
| "Who can see / change it?" | Security (undercurrent) |
| "How do we know it broke?" | DataOps (undercurrent) |
| "How do we coordinate all of this?" | Orchestration (undercurrent) |

## Deeper dives

Each stage and undercurrent has its own file in this `framework/` folder:
- `01-generation.md`, `02-storage.md` (storage is treated as its own theme in Reis/Housley though it spans ingestion and transformation), `03-ingestion.md`, `04-transformation.md`, `05-serving.md`
- `undercurrent-security.md`, `undercurrent-data-management.md`, `undercurrent-dataops.md`, `undercurrent-architecture.md`, `undercurrent-orchestration.md`, `undercurrent-software-engineering.md`
- For the Data Mesh reframing of ownership across the lifecycle: `concept-data-mesh.md`
