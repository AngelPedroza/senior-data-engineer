#!/usr/bin/env python3
"""
dag_idempotency_check.py — lint Airflow / Dagster / Prefect DAG files for idempotency violations.

Usage:
    python dag_idempotency_check.py path/to/dags [--json]

Uses Python AST — no imports executed, so safe on third-party DAG code.
Checks:
  - datetime.now() / date.today() inside task bodies
  - missing retries on Airflow operators
  - missing execution_timeout on Airflow operators
  - catchup=True on DAG constructor (warn for new DAGs)
  - bare top-level side-effect calls in DAG files (print, requests.get, etc.)
Exits 0 when clean, 1 on findings.
"""
from __future__ import annotations

import argparse
import ast
import json
import sys
from dataclasses import dataclass, asdict
from pathlib import Path


NOW_CALLS = {
    ("datetime", "now"),
    ("datetime", "today"),
    ("date", "today"),
    ("time", "time"),
    ("pendulum", "now"),
    ("pendulum", "today"),
}

TOP_LEVEL_SIDE_EFFECTS = {"print", "open"}
SIDE_EFFECT_MODULES = {"requests", "urllib", "boto3", "psycopg2", "subprocess"}


@dataclass
class Finding:
    file: str
    line: int
    rule: str
    severity: str
    message: str


def check_now_calls(tree: ast.AST, path: Path) -> list[Finding]:
    findings: list[Finding] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            attr = node.func.attr
            value = node.func.value
            if isinstance(value, ast.Name):
                pair = (value.id, attr)
                if pair in NOW_CALLS:
                    findings.append(Finding(
                        file=str(path), line=node.lineno,
                        rule="now-call",
                        severity="error",
                        message=f"{value.id}.{attr}() call inside DAG / task code breaks idempotency. "
                                "Use data_interval_start / data_interval_end (Airflow) or asset_partition_key (Dagster).",
                    ))
    return findings


def check_airflow_operators(tree: ast.AST, path: Path) -> list[Finding]:
    findings: list[Finding] = []
    operator_suffixes = ("Operator", "Sensor", "Transfer")
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func_name = ""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr
        if not any(func_name.endswith(s) for s in operator_suffixes):
            continue
        kwarg_names = {kw.arg for kw in node.keywords if kw.arg}
        if "retries" not in kwarg_names:
            findings.append(Finding(
                file=str(path), line=node.lineno, rule="missing-retries",
                severity="warn",
                message=f"{func_name} has no explicit retries. Set a finite retries count.",
            ))
        if "execution_timeout" not in kwarg_names:
            findings.append(Finding(
                file=str(path), line=node.lineno, rule="missing-execution-timeout",
                severity="warn",
                message=f"{func_name} has no execution_timeout. Unbounded tasks can hang workers indefinitely.",
            ))
    return findings


def check_dag_catchup(tree: ast.AST, path: Path) -> list[Finding]:
    findings: list[Finding] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "DAG":
            kwargs = {kw.arg: kw.value for kw in node.keywords if kw.arg}
            catchup_node = kwargs.get("catchup")
            if catchup_node is None:
                findings.append(Finding(
                    file=str(path), line=node.lineno, rule="catchup-unset",
                    severity="info",
                    message="DAG has no explicit catchup=. Airflow defaults to True in older configs; set explicitly.",
                ))
            elif isinstance(catchup_node, ast.Constant) and catchup_node.value is True:
                findings.append(Finding(
                    file=str(path), line=node.lineno, rule="catchup-true",
                    severity="warn",
                    message="DAG has catchup=True. On new DAGs this triggers historical runs on first deploy. Use backfill explicitly instead.",
                ))
    return findings


def check_top_level_side_effects(tree: ast.AST, path: Path) -> list[Finding]:
    findings: list[Finding] = []
    for node in tree.body if hasattr(tree, "body") else []:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            call = node.value
            name = ""
            if isinstance(call.func, ast.Name):
                name = call.func.id
            elif isinstance(call.func, ast.Attribute):
                if isinstance(call.func.value, ast.Name):
                    name = call.func.value.id
            if name in TOP_LEVEL_SIDE_EFFECTS or name in SIDE_EFFECT_MODULES:
                findings.append(Finding(
                    file=str(path), line=node.lineno, rule="top-level-side-effect",
                    severity="error",
                    message=f"Top-level {name}(...) call in DAG file. Airflow re-imports DAG files repeatedly; side effects at module scope run on every scheduler tick.",
                ))
    return findings


def scan_file(path: Path) -> list[Finding]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"), filename=str(path))
    except SyntaxError as e:
        return [Finding(file=str(path), line=e.lineno or 0,
                        rule="syntax-error", severity="error",
                        message=f"Could not parse: {e.msg}")]
    return (check_now_calls(tree, path)
            + check_airflow_operators(tree, path)
            + check_dag_catchup(tree, path)
            + check_top_level_side_effects(tree, path))


def main() -> int:
    ap = argparse.ArgumentParser(description="Lint DAG files for idempotency violations.")
    ap.add_argument("path", help="Directory or .py file to scan")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--fail-on", choices=["info", "warn", "error"], default="error")
    args = ap.parse_args()

    root = Path(args.path)
    if not root.exists():
        print(f"error: path not found: {root}", file=sys.stderr)
        return 2

    files = [root] if root.is_file() else sorted(root.rglob("*.py"))
    findings: list[Finding] = []
    for f in files:
        findings.extend(scan_file(f))

    rank = {"info": 0, "warn": 1, "error": 2}
    threshold = rank[args.fail_on]

    if args.json:
        print(json.dumps({"files_scanned": len(files), "findings": [asdict(f) for f in findings]}, indent=2))
    else:
        print(f"Scanned {len(files)} Python files.")
        if not findings:
            print("No idempotency findings.")
        for f in findings:
            print(f"[{f.severity.upper():5}] {f.file}:{f.line}  {f.rule}")
            print(f"        {f.message}")

    return 1 if any(rank[f.severity] >= threshold for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
