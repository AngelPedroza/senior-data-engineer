# Undercurrent — Data Architecture

**Concept anchor:** Reis & Housley 2022, ch. 3 ("Designing Good Data Architecture") and ch. 4 ("Choosing Technologies").
**Also drawing from:** Bass, Clements, Kazman *Software Architecture in Practice* (4th ed.); ThoughtWorks Technology Radar methodology; Martin Fowler "Who Needs an Architect?"; Dehghani *Data Mesh*.

---

## What architecture means here

High-level structural decisions about how data systems are composed: which tools, which layers, which boundaries, which patterns. Architecture is the set of decisions that are expensive to reverse later.

## Principles of good data architecture (Reis & Housley framing)

1. **Choose common components wisely** — prefer standards (Parquet, SQL, Kafka protocol) over proprietary unless the proprietary tool is clearly better for the workload.
2. **Plan for failure** — fault tolerance, graceful degradation, recovery procedures. Availability targets with math.
3. **Architect for scalability** — design for 10x current load; avoid premature optimization for 100x.
4. **Architecture is leadership** — architectural choices shape team capability; a poor choice entrenches technical debt.
5. **Always be architecting** — the architecture is never "done"; evaluate as the context shifts.
6. **Build loosely coupled systems** — clear boundaries, explicit contracts, replaceable components.
7. **Make reversible decisions** — prefer choices that can be undone. Lock-in is a cost.
8. **Prioritize security** — from the first sketch, not an afterthought.
9. **Embrace FinOps** — cost is a first-class architectural concern in the cloud. See `concept-finops.md`.

## The reversibility test

Before choosing a technology, ask: **if this turns out to be the wrong choice in two years, what does reversing cost?**

- Low-reversibility (beware): a warehouse-specific ML feature (tied to one vendor), a proprietary orchestration language, heavy use of stored procedures in a specific DB.
- High-reversibility (safer): Parquet files on object storage, SQL models via dbt (portable across most warehouses), DAGs in standard Python.

Prefer high-reversibility by default. Accept low-reversibility consciously, with documented justification.

## Immutable vs. transitory technologies

Reis & Housley distinguish:
- **Immutable technologies** — long-lived, standards-based, unlikely to disappear (SQL, Python, Kafka protocol, Parquet, Linux).
- **Transitory technologies** — vendor-specific tools that come and go every few years (specific warehouse UIs, orchestrators, BI tools).

Build on immutable foundations. Accept transitory tools where they add real value, but don't entangle immutable layers with transitory ones.

## Common architectural patterns

- **Lambda architecture** — parallel batch and streaming paths merged at serving. Solves latency vs. correctness trade-off but doubles implementation. Largely superseded.
- **Kappa architecture** — streaming as the primary path; batch is just a replay of the stream. Simpler if streaming tooling is mature.
- **Medallion (bronze/silver/gold)** — three-layer warehouse/lakehouse pattern. Current pragmatic default.
- **Data Mesh** — domain-owned data products, federated governance. Organizational as much as technical. Appropriate for large orgs; often overkill for small teams.
- **Data Fabric** — heavy metadata / catalog layer integrating disparate stores. Vendor-heavy framing.

## Architecture trade-offs, made explicit

For any choice, name the trade-off. Examples:

- **Warehouse vs. lakehouse** — tighter integration and governance vs. openness and portability.
- **dbt vs. stored procedures** — version control and testing vs. engine-native performance.
- **Airflow vs. Dagster** — maturity / ecosystem vs. asset-centric model and types.
- **Iceberg vs. Delta** — open multi-engine vs. deeper single-engine optimization.

A good architecture decision states the trade-off accepted and why.

## Architecture documentation

At minimum, every significant architectural decision should be captured as a short ADR (Architecture Decision Record):
- Title and date.
- Context (what problem, what constraints).
- Decision (what was chosen).
- Consequences (what becomes easier, what becomes harder).

Store in the repo. Grepable, versioned, reviewable.

## Anti-patterns

- Choosing the "most capable" tool when a simpler one would do — accidental complexity.
- Entangling transitory with immutable layers — moving the immutable core later means rewriting the transitory integrations.
- No reversibility analysis — lock-in discovered after contract signing.
- Copy-pasting another team's architecture — their constraints aren't yours.
- Architecture by resumé — choosing tools for personal CV value, not the project's needs.

## See also

- Choosing a specific tool: `../playbooks/choose-technology.md`
- Cost as architecture: `concept-finops.md`
