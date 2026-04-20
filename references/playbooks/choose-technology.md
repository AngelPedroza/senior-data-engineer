# Playbook — Choose a Technology

**When to use:** evaluating whether to adopt a new warehouse, orchestrator, table format, streaming engine, catalog, or any other significant tool.
**Related framework:** `../framework/undercurrent-architecture.md`, `../framework/concept-finops.md`.

---

## Step 1 — State the problem, not the tool

Write the problem in one paragraph without naming any tool. Example:

> "We need to move CDC events from Postgres into our lakehouse within 5 minutes of source commit, handling ~50k events/sec peak, preserving insert/update/delete order per table, with retries and dead-letter for parse failures."

If you cannot write the problem without tool names, you do not yet understand the problem.

## Step 2 — Inventory what you already have

The cheapest technology is the one you already run. Cost of a new tool includes:
- Learning curve for the whole team.
- New integrations and authentication.
- New monitoring and alerting.
- New incident-response patterns.
- New vendor relationship.

If an existing tool solves the problem at 80% of ideal, that is usually better than a new tool solving it at 95%.

## Step 3 — List candidates

Two to four serious candidates. Include:
- The thing you'd pick "on instinct."
- The thing someone on the team is evangelizing.
- The thing the current tools can do if stretched.
- One dark-horse option with a known trade-off.

Write the list. No research yet.

## Step 4 — Evaluate against explicit criteria

Write the criteria first, weight them, then score. Typical criteria:

| Criterion | Why it matters |
|---|---|
| **Fit for workload** | Does it actually solve the problem at the scale required? |
| **Reversibility** | If wrong, what does switching cost? |
| **Team familiarity** | Do people already know it? Cost of learning? |
| **Operational burden** | Self-hosted vs. managed; on-call implications |
| **Integration with existing stack** | Auth, IAM, monitoring, catalog, lineage |
| **Ecosystem / longevity** | Active development? Community? Vendor stability? |
| **Cost** | List price + ops cost + engineer-time cost |
| **Licensing** | OSS, commercial, dual-licensed? |
| **Security & compliance** | PII handling, audit, SOC 2 availability |
| **Vendor lock-in** | Proprietary APIs, non-standard storage format |

## Step 5 — Reversibility test (Reis & Housley 2022, ch. 3)

For each candidate, answer: *"If we adopt this and in two years we need to move off it, what is the cost?"*

- **Low-reversibility** (beware): proprietary storage formats, unique orchestration DSLs, tight coupling to a single vendor's identity system.
- **High-reversibility** (safer): Parquet on object storage, standard SQL via dbt, Python-defined DAGs, Kafka-protocol streams.

Prefer high-reversibility. Accept low-reversibility consciously, with documented justification (e.g., "We're accepting Snowflake-specific features because the cost benefit over three years is 10x the extraction cost if we ever move.").

## Step 6 — Immutable vs. transitory layer check

Reis & Housley distinguish:
- **Immutable technologies** — SQL, Python, Parquet, Kafka protocol, Linux, HTTP.
- **Transitory technologies** — specific warehouses, orchestrators, BI tools.

Build transitory choices on immutable foundations. Never entangle immutable data (your core Parquet files, your SQL logic) with a transitory tool (a specific orchestrator's proprietary metadata).

## Step 7 — Prototype, don't debate

One week of spike work on the 1–2 finalists beats two weeks of meetings. The prototype should:
- Run against real data (a slice, not synthetic).
- Exercise the actual integration pain points (auth, monitoring, retry).
- Be thrown away afterward (don't let prototype code become production code).

## Step 8 — Write the ADR

Architecture Decision Record (short — a page):
1. **Title and date.**
2. **Context** — the problem from Step 1.
3. **Options considered** — from Step 3 with scores from Step 4.
4. **Decision** — what you chose.
5. **Consequences** — what becomes easier, what becomes harder, what capability you gave up.
6. **Reversibility** — from Step 5.

Commit to the repo. Future team members need to know *why*, not just *what*.

## Step 9 — Plan the off-ramp

Before fully committing, document:
- Under what conditions would we reconsider this choice?
- What is the extraction cost if we move away?
- What data / logic must we keep on the immutable layer so we *can* move?

"We've locked in forever" is almost never right.

## Common mistakes

- Choosing the most capable tool when a simpler one would do.
- Choosing the tool someone demoed well without checking fit.
- "Big Tech uses this" — their constraints aren't yours.
- Deciding by feature checklist without weighting operational cost.
- Ignoring existing team skills.
- Never writing the ADR — decision is unsearchable three months later.

## See also

- Architecture principles: `../framework/undercurrent-architecture.md`
- Cost modelling: `../framework/concept-finops.md`
