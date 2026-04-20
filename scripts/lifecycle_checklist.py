#!/usr/bin/env python3
"""
lifecycle_checklist.py — interactive walkthrough of the Phase-1 data contract.

Usage:
    python lifecycle_checklist.py                 # interactive; writes design skeleton to stdout
    python lifecycle_checklist.py --output design.md
    python lifecycle_checklist.py --json

Walks the questions from:
  references/playbooks/design-new-pipeline.md
  references/framework/00-data-engineering-lifecycle.md

Pure standard library. No network.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, asdict, field
from datetime import date


QUESTIONS = [
    ("pipeline_name", "Name of the pipeline / dataset"),
    ("owner", "Named owner (team or person)"),
    ("source_of_truth", "Source of truth (where the data originates)"),
    ("update_semantics", "Update semantics (append-only / mutable / CDC / soft-delete)"),
    ("grain", 'Grain — "one row per WHAT?" (full sentence)'),
    ("primary_key", "Primary / uniqueness key (natural or surrogate)"),
    ("volume_rows_per_day", "Volume — rows per day (estimate)"),
    ("total_rows", "Total rows (estimate)"),
    ("latency_sla", "Latency SLA (real-time / near-real-time / hourly / daily)"),
    ("consumers", "Primary consumers (BI / ML / ops / reverse-ETL)"),
    ("backfill_scope", "Backfill scope (how far back? reprocessing safe?)"),
    ("pii", "PII / sensitive columns (or 'none')"),
    ("retention", "Retention policy (days / months / years)"),
    ("tech_ingestion", "Ingestion tool (managed connector / custom / CDC)"),
    ("tech_transform", "Transformation tool (dbt / Spark / warehouse SQL)"),
    ("tech_orchestration", "Orchestrator (Airflow / Dagster / Prefect)"),
    ("freshness_alert", "Freshness alert threshold"),
    ("volume_anomaly_window", "Volume-anomaly tolerance (e.g. ±20% rolling 7-day)"),
    ("reversibility_note", "If this tech choice is wrong in 2 years, extraction cost is..."),
]


@dataclass
class Answers:
    answers: dict[str, str] = field(default_factory=dict)


def ask_interactive() -> Answers:
    ans = Answers()
    print("Data contract walkthrough — press Enter to skip a question.")
    print("=" * 60)
    for key, prompt in QUESTIONS:
        try:
            raw = input(f"  {prompt}:\n    > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\naborted.")
            sys.exit(130)
        ans.answers[key] = raw
    return ans


def render_markdown(ans: Answers) -> str:
    a = ans.answers
    today = date.today().isoformat()
    return f"""# Pipeline Design — {a.get('pipeline_name', '(unnamed)')}

**Date:** {today}
**Owner:** {a.get('owner', '(unassigned)')}
**Status:** draft

---

## Contract

- **Source of truth:** {a.get('source_of_truth', 'TBD')}
- **Update semantics:** {a.get('update_semantics', 'TBD')}
- **Grain:** {a.get('grain', 'TBD')}
- **Primary key:** {a.get('primary_key', 'TBD')}
- **Volume:** {a.get('volume_rows_per_day', 'TBD')} rows/day  (total ≈ {a.get('total_rows', 'TBD')})
- **Latency SLA:** {a.get('latency_sla', 'TBD')}
- **Consumers:** {a.get('consumers', 'TBD')}
- **Backfill scope:** {a.get('backfill_scope', 'TBD')}
- **PII / sensitivity:** {a.get('pii', 'TBD')}
- **Retention:** {a.get('retention', 'TBD')}

## Technology

- **Ingestion:** {a.get('tech_ingestion', 'TBD')}
- **Transformation:** {a.get('tech_transform', 'TBD')}
- **Orchestration:** {a.get('tech_orchestration', 'TBD')}
- **Reversibility:** {a.get('reversibility_note', 'TBD')}

## Observability

- **Freshness alert:** {a.get('freshness_alert', 'TBD')}
- **Volume anomaly tolerance:** {a.get('volume_anomaly_window', 'TBD')}

## Open questions / TODO

- Write the per-layer schemas (raw / staging / marts).
- Define per-column boundary tests.
- Confirm cost estimate.
- Document consumer list and notification plan.

## Sign-offs

- [ ] Owner
- [ ] Primary consumer
- [ ] On-call / platform team (if applicable)
"""


def main() -> int:
    ap = argparse.ArgumentParser(description="Interactive data-contract checklist.")
    ap.add_argument("--output", help="Write markdown to this path instead of stdout")
    ap.add_argument("--json", action="store_true", help="Emit JSON instead of markdown")
    args = ap.parse_args()

    ans = ask_interactive()

    if args.json:
        out = json.dumps(asdict(ans), indent=2)
    else:
        out = render_markdown(ans)

    if args.output:
        from pathlib import Path
        Path(args.output).write_text(out, encoding="utf-8")
        print(f"wrote {args.output}", file=sys.stderr)
    else:
        print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
