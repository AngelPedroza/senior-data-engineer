#!/usr/bin/env python3
"""
schema_contract_diff.py — diff two schemas; classify each change as additive / breaking / semantic.

Usage:
    python schema_contract_diff.py OLD NEW [--json]

Supports two schema formats:
  - JSON Schema (object with "properties" mapping to {type:...})
  - Simple SQL DDL (single CREATE TABLE ... ( col type [NOT NULL] [, ...] ))

Non-zero exit if any breaking change is detected.
Pure standard library.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class Change:
    kind: str       # added | removed | type_changed | nullability_changed | unchanged
    column: str
    old: str | None
    new: str | None
    classification: str  # additive | breaking | semantic
    note: str = ""


def parse_json_schema(text: str) -> dict[str, dict]:
    data = json.loads(text)
    props = data.get("properties", {})
    required = set(data.get("required", []))
    cols: dict[str, dict] = {}
    for name, spec in props.items():
        t = spec.get("type", "unknown")
        if isinstance(t, list):
            nullable = "null" in t
            t = ",".join(x for x in t if x != "null") or "unknown"
        else:
            nullable = name not in required
        cols[name] = {"type": t, "nullable": nullable}
    return cols


SQL_COL_RE = re.compile(
    r"""^\s*
        ["\[`]?(?P<name>[\w]+)["\]`]?
        \s+(?P<type>[A-Za-z][\w()\d,\s]*?)
        (?P<nn>\s+NOT\s+NULL)?
        \s*(?:,|$)""",
    re.IGNORECASE | re.VERBOSE,
)


def parse_sql_ddl(text: str) -> dict[str, dict]:
    m = re.search(r"CREATE\s+TABLE[^(]*\((.+)\)\s*;?\s*$", text, re.IGNORECASE | re.DOTALL)
    if not m:
        raise ValueError("Could not find CREATE TABLE ( ... ) body in SQL input.")
    body = m.group(1)
    lines = [ln.strip() for ln in body.split("\n") if ln.strip()]
    cols: dict[str, dict] = {}
    for ln in lines:
        # Skip constraints
        if re.match(r"^\s*(PRIMARY|FOREIGN|CONSTRAINT|UNIQUE|CHECK)\b", ln, re.IGNORECASE):
            continue
        cm = SQL_COL_RE.match(ln)
        if cm:
            cols[cm.group("name").lower()] = {
                "type": cm.group("type").strip().rstrip(",").upper(),
                "nullable": cm.group("nn") is None,
            }
    return cols


def sniff_and_parse(path: Path) -> dict[str, dict]:
    text = path.read_text(encoding="utf-8")
    stripped = text.lstrip()
    if stripped.startswith("{"):
        return parse_json_schema(text)
    return parse_sql_ddl(text)


TYPE_WIDEN_HINTS = {
    ("INT", "BIGINT"), ("INTEGER", "BIGINT"),
    ("SMALLINT", "INT"), ("SMALLINT", "INTEGER"), ("SMALLINT", "BIGINT"),
    ("VARCHAR", "TEXT"), ("CHAR", "VARCHAR"), ("CHAR", "TEXT"),
    ("FLOAT", "DOUBLE"), ("REAL", "DOUBLE"),
}


def classify_type_change(old: str, new: str) -> tuple[str, str]:
    """Return (classification, note). Simple heuristic; not a type-checker."""
    o, n = (old or "").upper(), (new or "").upper()
    if o == n:
        return "additive", "no change"
    # Normalize: drop parens and numbers (e.g. VARCHAR(100) -> VARCHAR)
    def norm(t: str) -> str:
        return re.sub(r"\(.*?\)", "", t).strip()
    on, nn = norm(o), norm(n)
    if on == nn:
        return "additive", f"parameters changed: {old} -> {new}"
    if (on, nn) in TYPE_WIDEN_HINTS:
        return "additive", f"widening: {old} -> {new}"
    if (nn, on) in TYPE_WIDEN_HINTS:
        return "breaking", f"narrowing: {old} -> {new}"
    return "breaking", f"type change: {old} -> {new}"


def diff_schemas(old: dict[str, dict], new: dict[str, dict]) -> list[Change]:
    changes: list[Change] = []
    for col in set(old) | set(new):
        o = old.get(col)
        n = new.get(col)
        if o and not n:
            changes.append(Change("removed", col, f"{o['type']} nullable={o['nullable']}", None,
                                  "breaking", "column dropped"))
        elif n and not o:
            classification = "additive" if n["nullable"] else "breaking"
            note = ("nullable new column" if n["nullable"]
                    else "non-nullable new column — requires default or backfill")
            changes.append(Change("added", col, None, f"{n['type']} nullable={n['nullable']}",
                                  classification, note))
        elif o and n:
            if o["type"] != n["type"]:
                cls, note = classify_type_change(o["type"], n["type"])
                changes.append(Change("type_changed", col, o["type"], n["type"], cls, note))
            if o["nullable"] != n["nullable"]:
                if o["nullable"] and not n["nullable"]:
                    changes.append(Change("nullability_changed", col,
                                          "nullable", "not null", "breaking",
                                          "tightening nullability requires backfill / default"))
                else:
                    changes.append(Change("nullability_changed", col,
                                          "not null", "nullable", "additive",
                                          "relaxing nullability"))
    return changes


def main() -> int:
    ap = argparse.ArgumentParser(description="Diff two schemas; classify breaking changes.")
    ap.add_argument("old", help="Path to the old schema (JSON Schema or SQL DDL)")
    ap.add_argument("new", help="Path to the new schema")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    try:
        old = sniff_and_parse(Path(args.old))
        new = sniff_and_parse(Path(args.new))
    except (ValueError, json.JSONDecodeError) as e:
        print(f"error: could not parse schema: {e}", file=sys.stderr)
        return 2

    changes = diff_schemas(old, new)

    if args.json:
        print(json.dumps({"changes": [asdict(c) for c in changes]}, indent=2))
    else:
        for c in changes:
            print(f"[{c.classification.upper():9}] {c.kind:20} {c.column:30} {c.old} -> {c.new}")
            if c.note:
                print(f"            note: {c.note}")
        breaking = [c for c in changes if c.classification == "breaking"]
        print()
        print(f"Summary: {len(changes)} change(s), {len(breaking)} breaking.")

    return 1 if any(c.classification == "breaking" for c in changes) else 0


if __name__ == "__main__":
    sys.exit(main())
