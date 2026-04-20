# Playbook — Review a Data-Engineering PR

**When to use:** reviewing a PR that touches SQL models, dbt projects, Spark jobs, orchestration DAGs, or schema DDL.
**Related framework:** `../framework/undercurrent-software-engineering.md`, `../framework/undercurrent-dataops.md`.
**Related scripts:** `scripts/sql_anti_patterns.py`, `scripts/dbt_project_audit.py`, `scripts/dag_idempotency_check.py`, `scripts/schema_contract_diff.py`.

---

## Approach

Focus, in order: correctness → contract impact → idempotency → observability → cost → clarity.

Do not bikeshed style if the logic is broken. Do not miss logic bugs because you were reading variable names.

## Layer 1 — Correctness

For each modified model / job:

- [ ] **Grain is declared** and matches the logic. "One row per order-line-item" means `count(*) = count(distinct order_id, line_id)`.
- [ ] **Primary key is truly unique** — check for `unique` test; verify it covers the declared grain.
- [ ] **Joins do not explode cardinality** — every join should be LEFT from the fact side, or there must be a reason. `INNER` joins silently drop rows; read with that lens.
- [ ] **NULL handling** — is NULL a valid state? If so, explicit handling. If not, `NOT NULL` or a test.
- [ ] **Date / timezone handling** — all timestamps in UTC unless explicitly stated. Be wary of `CURRENT_DATE` in logic (non-idempotent).
- [ ] **Window functions** — partition keys correct? Frame clauses explicit?
- [ ] **Aggregations** — `SUM` / `AVG` / `COUNT` over the right subset? `COUNT DISTINCT` where appropriate?

## Layer 2 — Contract impact

- [ ] **Schema changes** — is this additive (new nullable column) or breaking (rename, type narrowing, drop)?
- [ ] **Breaking changes documented** — if yes, has the PR listed affected downstream consumers and coordinated with them?
- [ ] **Column semantics** — if a column's meaning changed (e.g., "revenue" now includes refunds), is it renamed, or is there a migration plan?
- [ ] Run `scripts/schema_contract_diff.py` against the previous schema.

## Layer 3 — Idempotency & replay

- [ ] **Idempotent write** — `MERGE` / partition replace / full replace. Not blind append.
- [ ] **Deterministic keys** — hash-based surrogate keys, not `ROW_NUMBER`.
- [ ] **No `datetime.now()` inside transformations** — use orchestrator-provided interval boundaries.
- [ ] **Re-runnable** — would a second run with the same inputs produce the same output?
- [ ] **For DAG changes** — run `scripts/dag_idempotency_check.py`.

## Layer 4 — Tests

- [ ] Boundary tests present: `unique`, `not_null`, `relationships`, `accepted_values`.
- [ ] Freshness on sources touched.
- [ ] Business-rule tests for non-obvious invariants.
- [ ] Tests actually execute in CI — not skipped or tagged out.
- [ ] New incremental models have `unique_key` configured.
- [ ] If dbt project, run `scripts/dbt_project_audit.py`.

## Layer 5 — Observability

- [ ] Ownership assigned (model `meta.owner` or equivalent).
- [ ] Freshness / volume monitoring in place or explicitly not needed for this table.
- [ ] Alerts route to someone who can act.
- [ ] Lineage updated (dbt docs, OpenLineage).

## Layer 6 — Cost

- [ ] Materialization appropriate (view / table / incremental).
- [ ] Partition pruning intact — `WHERE` on partition column where applicable.
- [ ] No `SELECT *` in production models.
- [ ] No accidental full-table scans on large sources.
- [ ] For big changes: has the author estimated query cost / bytes scanned?
- [ ] Run `scripts/sql_anti_patterns.py`.

## Layer 7 — Clarity

Lowest priority but not zero:
- [ ] Model / column descriptions are accurate and non-empty for published tables.
- [ ] CTEs are named for what they represent.
- [ ] Complex logic has a one-line comment *why* (not *what*).
- [ ] No commented-out code.
- [ ] No `TODO` without an issue link.

## Anti-patterns to flag hard

- `SELECT *` in a production model.
- `ROW_NUMBER()` over unordered partition used as surrogate key.
- `WHERE 1=1` as a permanent condition (debugging remnant).
- `DISTINCT` over many columns (usually a join-cardinality bug in disguise).
- `ORDER BY` in a subquery without `LIMIT` (ignored; wastes compute on some engines).
- Hardcoded schema / database names instead of `ref()` / `source()`.
- Deeply nested CTEs where staging models would be clearer.
- Tests disabled or tagged out without explanation.

## When to block vs. suggest

**Block (request changes):**
- Correctness bug (grain violated, data loss possible).
- Breaking schema change without consumer coordination.
- Idempotency violation (non-deterministic output).
- Missing tests on grain / FKs.

**Suggest (comment only):**
- Style, naming, comment wording.
- Refactoring opportunities unrelated to the diff.
- Optimization hints where current cost is tolerable.

## After review

- If approved, say what you verified so the author knows what was checked and what wasn't.
- If blocked, be specific — "fails the idempotency check because of `now()` on line 42" beats "this isn't idempotent."
- If you ran scripts, mention which and the result.
