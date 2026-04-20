#!/usr/bin/env python3
"""
data_profile.py — profile a CSV or Parquet dataset for quick data-quality triage.

Usage:
    python data_profile.py path/to/data.csv [--json] [--rows 100000]
    python data_profile.py path/to/data.parquet [--json]

Prints per-column: non-null count, null %, distinct count, top values, min/max.
Suspects grain columns (count == distinct count).
Suspects primary key candidates (distinct == row count, low null %).

CSV: stdlib only.
Parquet: requires pyarrow. Install: `pip install pyarrow`.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import Counter
from dataclasses import dataclass, asdict, field
from pathlib import Path


@dataclass
class ColumnProfile:
    name: str
    non_null: int = 0
    nulls: int = 0
    distinct: int = 0
    top_values: list[tuple[str, int]] = field(default_factory=list)
    min_value: str | None = None
    max_value: str | None = None
    is_grain_candidate: bool = False
    is_pk_candidate: bool = False


def is_null(v) -> bool:
    if v is None:
        return True
    if isinstance(v, float) and math.isnan(v):
        return True
    if isinstance(v, str) and v.strip().lower() in ("", "null", "nan", "none"):
        return True
    return False


def read_csv(path: Path, limit: int | None) -> tuple[list[str], list[list]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows: list[list] = []
        for i, row in enumerate(reader):
            if limit is not None and i >= limit:
                break
            rows.append(row)
    return header, rows


def read_parquet(path: Path) -> tuple[list[str], list[list]]:
    try:
        import pyarrow.parquet as pq
    except ImportError:
        print("error: pyarrow required for parquet. Install with `pip install pyarrow`.", file=sys.stderr)
        sys.exit(2)
    table = pq.read_table(path)
    header = table.column_names
    cols = [c.to_pylist() for c in table.columns]
    rows = list(zip(*cols)) if cols else []
    return header, [list(r) for r in rows]


def profile_column(name: str, values: list, total: int) -> ColumnProfile:
    col = ColumnProfile(name=name)
    clean = [v for v in values if not is_null(v)]
    col.non_null = len(clean)
    col.nulls = total - col.non_null
    counts = Counter(str(v) for v in clean)
    col.distinct = len(counts)
    col.top_values = counts.most_common(5)
    if clean:
        try:
            as_num = [float(v) for v in clean]
            col.min_value = str(min(as_num))
            col.max_value = str(max(as_num))
        except (ValueError, TypeError):
            sv = sorted(str(v) for v in clean)
            col.min_value = sv[0]
            col.max_value = sv[-1]
    # Grain candidate: column has one row per distinct value (distinct ≈ total non-null)
    if col.non_null > 0 and col.distinct == col.non_null:
        col.is_grain_candidate = True
    # PK candidate: grain AND zero nulls AND non-trivial count
    if col.is_grain_candidate and col.nulls == 0 and col.non_null > 1:
        col.is_pk_candidate = True
    return col


def profile(header: list[str], rows: list[list]) -> dict:
    total = len(rows)
    columns = []
    for i, name in enumerate(header):
        values = [r[i] if i < len(r) else None for r in rows]
        columns.append(asdict(profile_column(name, values, total)))
    grain_candidates = [c["name"] for c in columns if c["is_grain_candidate"]]
    pk_candidates = [c["name"] for c in columns if c["is_pk_candidate"]]
    return {
        "row_count": total,
        "column_count": len(header),
        "grain_candidates": grain_candidates,
        "pk_candidates": pk_candidates,
        "columns": columns,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Quick data-quality profile for a CSV or Parquet file.")
    ap.add_argument("path", help="Path to .csv or .parquet file")
    ap.add_argument("--rows", type=int, default=None, help="Limit CSV read to N rows (Parquet always fully read)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    p = Path(args.path)
    if not p.exists():
        print(f"error: file not found: {p}", file=sys.stderr)
        return 2

    if p.suffix.lower() == ".parquet":
        header, rows = read_parquet(p)
    elif p.suffix.lower() in (".csv", ".tsv"):
        header, rows = read_csv(p, args.rows)
    else:
        print(f"error: unsupported extension: {p.suffix}", file=sys.stderr)
        return 2

    report = profile(header, rows)

    if args.json:
        print(json.dumps(report, indent=2, default=str))
        return 0

    print(f"File:         {p}")
    print(f"Rows:         {report['row_count']:,}")
    print(f"Columns:      {report['column_count']}")
    print(f"Grain candidates: {report['grain_candidates'] or 'none'}")
    print(f"PK candidates:    {report['pk_candidates'] or 'none'}")
    print()
    for c in report["columns"]:
        nulls_pct = (c["nulls"] / report["row_count"] * 100) if report["row_count"] else 0
        print(f"  {c['name']}")
        print(f"    non_null={c['non_null']:,}  nulls={c['nulls']:,} ({nulls_pct:.1f}%)  distinct={c['distinct']:,}")
        print(f"    min={c['min_value']!r}  max={c['max_value']!r}")
        tops = ", ".join(f"{v}={n}" for v, n in c["top_values"])
        if tops:
            print(f"    top: {tops}")
        flags = []
        if c["is_grain_candidate"]:
            flags.append("GRAIN_CANDIDATE")
        if c["is_pk_candidate"]:
            flags.append("PK_CANDIDATE")
        if flags:
            print(f"    flags: {', '.join(flags)}")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
