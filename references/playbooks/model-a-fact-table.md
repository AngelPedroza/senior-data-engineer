# Playbook — Model a Fact Table

**When to use:** designing a new fact table for analytics (orders, events, transactions, sessions, etc.).
**Related framework:** `../framework/04-transformation.md` (modeling styles).
**Primary source:** Kimball *The Data Warehouse Toolkit*, ch. 1, 3, and the subject-area chapters.

---

## Step 1 — Declare the grain

The single most important decision. Write it as a complete sentence:

> "One row per order-line-item per customer per day."

Rules:
- Be specific. "Order" is ambiguous — is it the order header, each line item, or each shipment?
- One grain per fact table. If you need two grains (e.g., header-level and line-level), that's two fact tables.
- Put the grain in a comment at the top of the model and in the model description.

## Step 2 — Choose the fact type

| Type | When | Example grain |
|---|---|---|
| **Transaction fact** | Discrete events, additive measures | One row per sale |
| **Periodic snapshot** | Regular status capture | One row per account per day |
| **Accumulating snapshot** | Process milestones update a single row | One row per mortgage application, updated as it progresses |
| **Factless fact** | Events where the record of occurrence is the measure | One row per student attendance |

## Step 3 — Identify the dimensions

For each business question the fact is supposed to answer, list the dimension it needs:
- *When* → `dim_date`, `dim_time`.
- *Who* → `dim_customer`, `dim_user`, `dim_employee`.
- *What* → `dim_product`, `dim_service`.
- *Where* → `dim_geography`, `dim_store`.
- *How* → `dim_channel`, `dim_payment_method`.

Every dimension gets a surrogate key in the fact. Do not store natural keys (like `customer_email`) directly on the fact — they belong on the dim, which the fact references.

## Step 4 — Design the measures

Measures are the numeric values aggregated in queries.

- **Additive** — can be summed across all dims (revenue, quantity).
- **Semi-additive** — summable across some but not others (balances — summable across customers, not across time).
- **Non-additive** — cannot be summed (ratios, percentages). Store the components instead (numerator + denominator) and compute at query time.

Rules:
- Prefer additive. Pre-compute non-additive measures rarely — they bite on re-aggregation.
- Use consistent units. Revenue in cents? Integer? Document it.
- Quantity + amount, never "amount * quantity" stored as a single column.

## Step 5 — Handle slowly changing dimensions (SCDs)

When a dim attribute changes (customer moves, product is recategorized), the fact must reference either:
- The **current** dim value (Type 1, overwrite).
- The **historical** value at the time of the fact event (Type 2, effective-dated rows).

**Default recommendation:** Type 2 on business-meaningful attributes you'd want to analyze by ("what was the customer's segment when they placed the order?"). Type 1 for corrections.

Implementation:
- dbt snapshots (`check` or `timestamp` strategy).
- Or Iceberg / Delta MERGE with effective-dated logic.

The fact stores the surrogate key valid at the event's timestamp — not the current surrogate key. This is often missed.

## Step 6 — Surrogate keys

- Deterministic hash of natural key + change-tracking columns: `dbt_utils.generate_surrogate_key(['customer_id', 'valid_from'])`.
- Never `ROW_NUMBER()` — non-deterministic across runs.
- Use a consistent hash function across the project (MD5 or SHA-1 — neither is cryptographic, but both are stable).

## Step 7 — Partitioning and clustering

- **Partition** on the time column queried most — usually `event_date` or `order_date`.
- **Cluster / Z-order** on the highest-cardinality filter column after partitioning (e.g., `customer_key`).
- Avoid over-partitioning — small partitions hurt.

## Step 8 — Incremental strategy

If the fact grows large:
- Incremental materialization with `unique_key` = fact's primary key (usually the combination of dim surrogate keys + event timestamp, or a surrogate fact key).
- Strategy: `merge` on warehouses that support it; `insert_overwrite` on partitioned tables.
- Lookback window — re-process the last N days each run to catch late-arriving rows.

## Step 9 — Write the tests

- `unique` on the fact primary key.
- `not_null` on all dim FKs that aren't optional.
- `relationships` between fact FKs and dim PKs.
- Row-count reconciliation against the source of truth.
- Custom: no future-dated facts (unless valid in the domain).

## Step 10 — Document

- Grain at the top of the model file.
- Column descriptions for every measure (unit, definition, calculation).
- Column descriptions for every dim FK (which dim, which version of attribute — current or historical).
- Lineage upstream (sources) and downstream (consuming marts / dashboards / feature views).

## Common mistakes

- Vague grain ("one row per order" — which kind of order?).
- Storing dim natural keys on the fact — breaks SCD Type 2 semantics.
- Non-additive measures stored as single values — cannot be re-aggregated.
- `ROW_NUMBER()` surrogate keys.
- Partitioning on a low-cardinality column (e.g., just `year`) — too-large partitions.
- Missing lookback window on incremental — late data never arrives.
- Fact tables with more than ~30 dim FKs — consider whether this should be multiple facts.

## See also

- Transformation overview: `../framework/04-transformation.md`
- Data contracts around fact tables: `design-data-contract.md`
