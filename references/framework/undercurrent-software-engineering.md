# Undercurrent — Software Engineering

**Concept anchor:** Reis & Housley 2022, ch. 2 (undercurrents section on Software Engineering).
**Also drawing from:** Kleppmann *Designing Data-Intensive Applications*; Dave Farley *Modern Software Engineering*; Forsgren/Humble/Kim *Accelerate*; dbt Labs "Analytics Engineering" blog.

---

## Why this is an undercurrent

Data engineering is software engineering. The data part makes some problems harder (silent failures, upstream dependencies, long feedback loops), but the engineering discipline is the same. Teams that treat SQL / pipelines as "scripts" instead of software accumulate debt fast.

## Core practices applied to data

### Version control

Every model, DAG, DDL, test, config (minus secrets) lives in git. Commit messages follow the team convention. Branches, reviews, PRs for production changes.

### Modularity

- Models do one thing well; staging separates from marts separates from facts.
- Shared logic goes in macros (dbt) / shared libraries (Python).
- Avoid 1000-line SQL files — break into chains of `ref()`-linked models.

### Typing

- SQL: columns have declared types. Constraints (`NOT NULL`, `UNIQUE`, `CHECK`) where the engine supports them.
- Python: `mypy` / `pyright`. No `Any` in production code paths.
- Schemas (Avro, JSON Schema, Protobuf) for streaming and API boundaries.
- dbt `contracts:` for enforcing column types at build time.

### Testing

Layered:
- **Unit** — pure functions (Python), pure expressions (dbt macros). Fast, always run.
- **Component** — a model against a fixture, isolated.
- **Integration** — end-to-end on a small real-data slice, not just mocks. Mocks hide the divergence bugs that matter.
- **Contract** — schema and semantics enforced via dbt contracts, Great Expectations, or schema registry.

Related skill: `superpowers:test-driven-development`.

### Code review

Every production-impacting change gets reviewed. Reviewers focus on:
- Correctness (grain, idempotency, tests).
- Clarity (is the intent obvious?).
- Consistency (does it match existing patterns?).
- Observability (is there a way to know if this is working in production?).
- Cost (bytes scanned, materialization choice, partition pruning).

See `../playbooks/review-data-pr.md` for a checklist.

### CI / CD

- Lint + type-check + unit tests on every push.
- Full integration tests on PR.
- Slim deploys — only what changed (dbt `defer`, asset-aware orchestrators).
- Automated deploys after merge; manual approval gates only where genuinely warranted.

### Reproducibility

Given the same code and the same input data, the same pipeline run should produce the same output. Sources of non-reproducibility to eliminate:
- `datetime.now()` inside tasks.
- Random IDs without seeds.
- `SELECT * FROM external_source` without capturing a snapshot.
- Rounding differences from running the same job on different engines.

### Documentation in code

- Every table / model has a description and a declared grain.
- Every column has a description if non-obvious.
- Macros have doc blocks.
- ADRs for significant architectural decisions (see `undercurrent-architecture.md`).

### Observability as code

- Logs are structured (JSON), not prose.
- Metrics are instrumented at stage boundaries.
- Tracing IDs thread through distributed pipelines (if applicable).

## Anti-patterns

- 500-line stored procedures with no tests.
- "Utility" models that become 40-column grab-bags.
- Quick fixes merged to `main` without review.
- Copy-pasted SQL across three files "because macros are complicated."
- Python tasks that catch all exceptions and print — failures invisible in production.
- "It works on my laptop" — pipelines that can't be reproduced on CI / another engineer's machine.

## See also

- CI testing: `undercurrent-dataops.md`
- Code review process: `../playbooks/review-data-pr.md`
