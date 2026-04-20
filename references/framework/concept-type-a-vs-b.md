# Concept — Type A vs. Type B Data Engineers

**Concept anchor:** Reis & Housley 2022, ch. 1 (role archetypes).
**Also drawing from:** Jesse Anderson's writings on data engineering roles; dbt Labs "Analytics Engineer" role definition (a close cousin to Type A).

---

## The two archetypes

Reis & Housley describe two common data-engineer archetypes, distinguished by where they spend their time and what they optimize for.

### Type A — Abstraction (Analytics-oriented)

Works on top of existing platforms and abstractions. Focus:
- Modeling data for analytical consumption (dbt, warehouse SQL).
- Enabling analysts and business users.
- Data contracts between producers and consumers.
- Iterating fast on business-facing datasets.

Typical tool kit: SQL, dbt, Airflow / Dagster, warehouse-native features, BI-adjacent tooling. Python for glue.

**Sometimes called:** Analytics Engineer, Data Modeler.

### Type B — Tool-building (Platform-oriented)

Builds and operates the platforms that Type A engineers use. Focus:
- Custom ingestion systems, connectors, CDC pipelines.
- Streaming / real-time infrastructure.
- Internal developer platforms for data.
- Performance tuning at the engine level.
- Orchestration at scale.

Typical tool kit: Python, Scala / JVM, Kafka / Flink / Spark, Kubernetes, Terraform, distributed systems depth.

**Sometimes called:** Data Platform Engineer, Streaming Engineer, Infra-oriented Data Engineer.

## Why the distinction matters

Organizations conflate the two at their peril. Hiring a Type B into a Type A role (or vice versa) leads to mismatched expectations: the platform engineer ships infrastructure nobody needs while business dashboards languish; the analytics engineer is handed distributed-systems work and struggles.

A healthy data-engineering org usually has both, in different proportions based on scale:

- **Stage 1–2 organizations** — Type A dominant. Platform needs are served by managed tools (Snowflake / BigQuery / Fivetran / dbt Cloud / Airflow managed).
- **Stage 3 organizations** — both, with Type B building internal platform for Type A teams to consume.

## How to know which you are (or need)

Ask: what problem annoys you most when it is unsolved?

- "Our dashboards are wrong and analysts can't answer questions" → Type A is the lever.
- "Our pipelines go down for hours and no one can diagnose" → Type B is the lever.
- "We're Snowflake-bound; can't scale this feature ingestion" → Type B.
- "We have no single source of truth for revenue" → Type A.

## Dual-role realities

Most data engineers do both at various points. The distinction is about **primary orientation** and where depth lives, not about rigid silos. A strong Type A knows enough platform to unblock themselves; a strong Type B knows enough modeling to not design useless abstractions.

## Team composition anti-patterns

- **All Type B, no Type A** — the platform is pristine; the business gets no value.
- **All Type A, no Type B** — business moves fast until the managed tool's limits are hit, then everything stalls.
- **Unclear archetype expectations** — hire a Type A and complain they can't build Kafka clusters.

## See also

- Maturity stage and team composition: `concept-maturity-model.md`
- Architecture roles and decisions: `undercurrent-architecture.md`
