# Undercurrent — DataOps

**Concept anchor:** Reis & Housley 2022, ch. 2 (undercurrents section on DataOps).
**Also drawing from:** Forsgren, Humble & Kim *Accelerate* (2018) / DORA metrics; Google *Site Reliability Engineering*; dbt testing docs; Monte Carlo "Data Observability" whitepapers; Great Expectations docs.

---

## What DataOps is

Applying DevOps and SRE principles to data systems: version control, CI / CD, testing, observability, incident response, continuous improvement. "DataOps" is DevOps's discipline adapted to data's distinct risks (silent data corruption, upstream schema drift, long feedback loops).

## DORA metrics adapted to data

The four DORA metrics for software delivery also apply to data pipelines:

1. **Deployment frequency** — how often new models / pipelines ship.
2. **Lead time for changes** — commit to production latency.
3. **Change failure rate** — % of deploys that cause incidents.
4. **Mean time to recovery (MTTR)** — from incident detection to resolution.

High-performing data teams ship small, frequent changes; pipelines are recovered in under an hour, not a day.

## Version control

Everything in git:
- Pipeline code (dbt models, Spark jobs, orchestrator DAGs).
- Schemas / DDL / migrations.
- Configuration (excluding secrets).
- Tests and expectations.
- Documentation.

If a production change wasn't in git, it doesn't exist as far as the team is concerned.

## CI for data

Minimum viable CI on a pipeline PR:
- Lint (SQL, Python, YAML).
- Type-check (where applicable).
- Unit tests (pure functions / transformations).
- Integration tests on a subset of real data (not just mocks — see also the integration-test guidance).
- dbt `parse` / `compile` — catches ref() errors.
- Schema contract diff — flag breaking changes.

Advanced:
- Build in an isolated dev schema; run tests there; teardown.
- dbt `defer` — run only changed models against production copies of unchanged dependencies.

## Testing taxonomy for data

| Test type | What it checks |
|---|---|
| **Structural** | Table exists, columns / types match schema |
| **Unique / not_null / relationships** | dbt-style boundary tests on grain and FKs |
| **Accepted values** | Enum columns have valid values |
| **Freshness** | Source data is recent enough |
| **Volume / row count** | Current load is within tolerance of recent runs |
| **Distribution** | Null %, mean, stddev within recent-history tolerance |
| **Reconciliation** | End-to-end sums match source of truth |
| **Custom business rules** | "Every order must have a customer older than 18" |

Layer them: structural and boundary tests always; volume / distribution tests on business-critical tables; reconciliation tests for revenue-impacting pipelines.

## Observability

Beyond tests, continuous monitoring:
- **Freshness monitors** — alerts on late data.
- **Volume anomaly detection** — alerts on unexpected row counts.
- **Schema drift** — alerts on source schema change.
- **Lineage-aware** — which downstream consumers are affected by an incident.

Tools: Monte Carlo, Soda, Elementary (open-source, dbt-native), Great Expectations + Marquez, Bigeye.

## SLAs and SLOs

- **SLA** — external commitment ("daily refresh by 9am").
- **SLO** — internal target ("99% of runs complete by 8:30am").
- **SLI** — measurable indicator ("time from source close to mart refresh").

Define these for every served dataset. Without SLAs, "is the data working?" is unanswerable.

## Incident response

- **On-call rotation** with documented escalation.
- **Runbooks** — how to investigate, how to backfill, who to page.
- **Postmortems** — blameless, for every customer-impacting incident.
- **Related skill:** `superpowers:systematic-debugging` for root-cause discipline.

## Anti-patterns

- Tests exist in dev, disabled in production.
- Alerts go to a Slack channel no one reads.
- Schema changes deployed without CI validation.
- Manual SQL in production that's "just a one-time fix" (it isn't).
- Pipelines without owners — nothing to escalate to.
- Retrying forever on a broken upstream — masks the real problem.

## See also

- Orchestration retry / timeout patterns: `undercurrent-orchestration.md`
- Code review for DE: `../playbooks/review-data-pr.md`
- Debugging playbook: `../playbooks/fix-broken-job.md`
