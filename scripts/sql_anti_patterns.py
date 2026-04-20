#!/usr/bin/env python3
"""
sql_anti_patterns.py — scan SQL files for common data-engineering anti-patterns.

Usage:
    python sql_anti_patterns.py path/to/models [--json] [--exclude PATTERN]

Exits 0 when no findings, 1 when findings exist (so CI can block).
Pure standard library. Regex-based — not a full SQL parser.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class Finding:
    file: str
    line: int
    rule: str
    severity: str
    message: str
    snippet: str


RULES = [
    {
        "id": "select-star",
        "severity": "warn",
        "pattern": re.compile(r"(?i)\bSELECT\s+\*", re.MULTILINE),
        "message": "SELECT * in a model. Name every column you need; protects against upstream schema changes and cuts scan cost.",
    },
    {
        "id": "truncate-insert",
        "severity": "error",
        "pattern": re.compile(r"(?is)\bTRUNCATE\b.*?\bINSERT\s+INTO\b", re.DOTALL),
        "message": "TRUNCATE followed by INSERT is not atomic in most engines. Use MERGE or partition replace for idempotent loads.",
    },
    {
        "id": "row-number-as-key",
        "severity": "error",
        "pattern": re.compile(r"(?is)ROW_NUMBER\s*\(\s*\)\s+OVER[^\)]*\)\s+AS\s+\w*(_?id|_?key|_?sk)\b"),
        "message": "ROW_NUMBER() used as surrogate key. Non-deterministic across runs; use a deterministic hash (e.g. dbt_utils.generate_surrogate_key).",
    },
    {
        "id": "distinct-wide",
        "severity": "warn",
        "pattern": re.compile(r"(?is)SELECT\s+DISTINCT\s+(?:\w+\s*,\s*){5,}"),
        "message": "DISTINCT over many columns often hides a join-cardinality bug. Prove duplicates are real before suppressing.",
    },
    {
        "id": "hardcoded-schema",
        "severity": "warn",
        "pattern": re.compile(r"(?i)\bFROM\s+[A-Z_][\w$]*\.[A-Z_][\w$]*\.[A-Z_][\w$]*"),
        "message": "Hardcoded fully-qualified name. In dbt projects, prefer ref() / source() so environments stay isolated.",
    },
    {
        "id": "unqualified-join",
        "severity": "warn",
        "pattern": re.compile(r"(?is)\bJOIN\s+\w+\s+(?:AS\s+\w+\s+)?(?=(?:WHERE|GROUP|ORDER|LIMIT|;|$))"),
        "message": "JOIN without ON clause — produces a Cartesian product. Intentional CROSS JOINs should be explicit.",
    },
    {
        "id": "order-by-in-subquery",
        "severity": "warn",
        "pattern": re.compile(r"(?is)\(\s*SELECT[^()]*ORDER\s+BY[^()]*\)(?!\s*LIMIT)"),
        "message": "ORDER BY in a subquery without LIMIT is typically ignored and wastes compute. Remove or add LIMIT.",
    },
    {
        "id": "now-in-logic",
        "severity": "warn",
        "pattern": re.compile(r"(?i)\b(CURRENT_DATE|CURRENT_TIMESTAMP|NOW\s*\(\s*\)|GETDATE\s*\(\s*\)|SYSDATE)\b"),
        "message": "Using CURRENT_DATE / NOW() / SYSDATE inside a model breaks idempotency. Parameterize by the orchestrator-provided interval boundary.",
    },
    {
        "id": "commented-out-code",
        "severity": "info",
        "pattern": re.compile(r"^\s*--\s*(SELECT|INSERT|UPDATE|DELETE|CREATE)\b", re.IGNORECASE | re.MULTILINE),
        "message": "Commented-out SQL. Remove before shipping; it rots fast.",
    },
    {
        "id": "where-1-equals-1",
        "severity": "warn",
        "pattern": re.compile(r"(?i)\bWHERE\s+1\s*=\s*1\b"),
        "message": "WHERE 1=1 with no additional conditions is a debugging leftover. Remove or complete.",
    },
]


def scan_file(path: Path) -> list[Finding]:
    text = path.read_text(encoding="utf-8", errors="replace")
    findings: list[Finding] = []
    for rule in RULES:
        for m in rule["pattern"].finditer(text):
            line_no = text.count("\n", 0, m.start()) + 1
            line_start = text.rfind("\n", 0, m.start()) + 1
            line_end = text.find("\n", m.end())
            if line_end == -1:
                line_end = len(text)
            snippet = text[line_start:line_end].strip()[:200]
            findings.append(
                Finding(
                    file=str(path),
                    line=line_no,
                    rule=rule["id"],
                    severity=rule["severity"],
                    message=rule["message"],
                    snippet=snippet,
                )
            )
    return findings


def iter_sql_files(root: Path, exclude: list[str]) -> list[Path]:
    files = sorted(root.rglob("*.sql"))
    if exclude:
        excl_patterns = [re.compile(p) for p in exclude]
        files = [f for f in files if not any(p.search(str(f)) for p in excl_patterns)]
    return files


def main() -> int:
    ap = argparse.ArgumentParser(description="Scan SQL files for data-engineering anti-patterns.")
    ap.add_argument("path", help="Directory or file to scan")
    ap.add_argument("--json", action="store_true", help="Output JSON")
    ap.add_argument("--exclude", action="append", default=[], help="Regex to exclude paths (repeatable)")
    ap.add_argument("--fail-on", choices=["info", "warn", "error"], default="error",
                    help="Minimum severity that causes non-zero exit (default: error)")
    args = ap.parse_args()

    root = Path(args.path)
    if not root.exists():
        print(f"error: path not found: {root}", file=sys.stderr)
        return 2

    files = [root] if root.is_file() else iter_sql_files(root, args.exclude)
    findings: list[Finding] = []
    for f in files:
        findings.extend(scan_file(f))

    severity_rank = {"info": 0, "warn": 1, "error": 2}
    fail_threshold = severity_rank[args.fail_on]

    if args.json:
        print(json.dumps({
            "files_scanned": len(files),
            "findings": [asdict(f) for f in findings],
        }, indent=2))
    else:
        print(f"Scanned {len(files)} SQL files.")
        if not findings:
            print("No findings.")
        for f in findings:
            print(f"[{f.severity.upper():5}] {f.file}:{f.line}  {f.rule}")
            print(f"        {f.message}")
            print(f"        > {f.snippet}")
            print()

    return 1 if any(severity_rank[f.severity] >= fail_threshold for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
