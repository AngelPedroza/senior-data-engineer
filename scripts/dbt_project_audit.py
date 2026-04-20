#!/usr/bin/env python3
"""
dbt_project_audit.py — audit a dbt project for common quality issues.

Usage:
    python dbt_project_audit.py path/to/dbt_project [--json]

Checks:
  - models without descriptions
  - sources without freshness
  - incremental models missing unique_key
  - models without unique/not_null tests on a grain column
  - orphan models (nothing ref()s them from other models)

Requires PyYAML. Install: `pip install pyyaml`
Exits 0 on clean, 1 on findings.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict, field
from pathlib import Path


def _require_yaml():
    try:
        import yaml  # noqa: F401
        return yaml
    except ImportError:
        print("error: PyYAML required. Install with `pip install pyyaml`.", file=sys.stderr)
        sys.exit(2)


REF_RE = re.compile(r"\{\{\s*ref\(\s*['\"]([^'\"]+)['\"]\s*\)\s*\}\}")
SOURCE_RE = re.compile(r"\{\{\s*source\(\s*['\"]([^'\"]+)['\"]\s*,\s*['\"]([^'\"]+)['\"]\s*\)\s*\}\}")
CONFIG_MATERIALIZED_RE = re.compile(
    r"\{\{\s*config\s*\([^)]*materialized\s*=\s*['\"](\w+)['\"]", re.IGNORECASE
)
CONFIG_UNIQUE_KEY_RE = re.compile(r"unique_key\s*=\s*['\"]?[\w\[\],\s]+['\"]?", re.IGNORECASE)


@dataclass
class ModelInfo:
    name: str
    path: str
    materialized: str = "view"
    has_unique_key: bool = False
    description: str | None = None
    tests: list[str] = field(default_factory=list)
    refs: list[str] = field(default_factory=list)


@dataclass
class Finding:
    model: str
    rule: str
    severity: str
    message: str


def load_yaml_models(project_root: Path) -> dict[str, dict]:
    """Load schema.yml / _schema.yml / *.yml describing models."""
    yaml_mod = _require_yaml()
    out: dict[str, dict] = {}
    for yml in list(project_root.rglob("*.yml")) + list(project_root.rglob("*.yaml")):
        if "target" in yml.parts or "dbt_packages" in yml.parts:
            continue
        try:
            data = yaml_mod.safe_load(yml.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        for m in data.get("models", []) or []:
            if isinstance(m, dict) and "name" in m:
                out[m["name"]] = m
    return out


def load_sources(project_root: Path) -> list[dict]:
    yaml_mod = _require_yaml()
    sources: list[dict] = []
    for yml in list(project_root.rglob("*.yml")) + list(project_root.rglob("*.yaml")):
        if "target" in yml.parts or "dbt_packages" in yml.parts:
            continue
        try:
            data = yaml_mod.safe_load(yml.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(data, dict):
            for s in data.get("sources", []) or []:
                sources.append(s)
    return sources


def load_sql_models(project_root: Path) -> list[ModelInfo]:
    models_dir = project_root / "models"
    if not models_dir.exists():
        return []
    models: list[ModelInfo] = []
    for sql_file in sorted(models_dir.rglob("*.sql")):
        text = sql_file.read_text(encoding="utf-8", errors="replace")
        name = sql_file.stem
        mat_match = CONFIG_MATERIALIZED_RE.search(text)
        materialized = mat_match.group(1) if mat_match else "view"
        has_unique_key = bool(CONFIG_UNIQUE_KEY_RE.search(text))
        refs = REF_RE.findall(text)
        models.append(ModelInfo(
            name=name,
            path=str(sql_file),
            materialized=materialized,
            has_unique_key=has_unique_key,
            refs=refs,
        ))
    return models


def audit(project_root: Path) -> list[Finding]:
    findings: list[Finding] = []
    yaml_models = load_yaml_models(project_root)
    sql_models = load_sql_models(project_root)
    sources = load_sources(project_root)

    # Build ref-count for orphan detection
    ref_count: dict[str, int] = {m.name: 0 for m in sql_models}
    for m in sql_models:
        for r in m.refs:
            if r in ref_count:
                ref_count[r] += 1

    for m in sql_models:
        y = yaml_models.get(m.name, {})
        desc = y.get("description")
        columns = y.get("columns", []) or []

        if not desc or (isinstance(desc, str) and not desc.strip()):
            findings.append(Finding(m.name, "missing-description", "warn",
                                    "Model has no description."))

        if m.materialized == "incremental" and not m.has_unique_key:
            findings.append(Finding(m.name, "incremental-without-unique-key", "error",
                                    "Incremental model has no unique_key configured — duplicates likely on re-run."))

        # Look for any column with unique + not_null tests (the grain)
        has_grain_tests = False
        for col in columns:
            if not isinstance(col, dict):
                continue
            tests = col.get("tests", []) or []
            test_ids = {t if isinstance(t, str) else list(t.keys())[0] for t in tests if t}
            if "unique" in test_ids and "not_null" in test_ids:
                has_grain_tests = True
                break
        if not has_grain_tests:
            findings.append(Finding(m.name, "no-grain-tests", "warn",
                                    "No column has both unique + not_null tests. Declare and test the grain."))

        # Orphan check — model is not an exposure or final mart and no one ref()s it
        if ref_count.get(m.name, 0) == 0 and "mart" not in m.path and "final" not in m.name:
            findings.append(Finding(m.name, "orphan-model", "info",
                                    "No other model ref()s this. If it's a mart / final output, this is expected."))

    # Sources without freshness
    for s in sources:
        src_name = s.get("name", "unknown")
        has_freshness = "freshness" in s or any("freshness" in (t or {}) for t in (s.get("tables", []) or []))
        if not has_freshness:
            findings.append(Finding(f"source:{src_name}", "source-without-freshness", "warn",
                                    "Source has no freshness declaration. You cannot alert on staleness."))

    return findings


def main() -> int:
    ap = argparse.ArgumentParser(description="Audit a dbt project for quality issues.")
    ap.add_argument("path", help="Path to the dbt project root (contains dbt_project.yml)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--fail-on", choices=["info", "warn", "error"], default="error")
    args = ap.parse_args()

    root = Path(args.path)
    if not (root / "dbt_project.yml").exists():
        print(f"error: no dbt_project.yml at {root}", file=sys.stderr)
        return 2

    findings = audit(root)
    rank = {"info": 0, "warn": 1, "error": 2}
    threshold = rank[args.fail_on]

    if args.json:
        print(json.dumps({"findings": [asdict(f) for f in findings]}, indent=2))
    else:
        if not findings:
            print("dbt project audit: no findings.")
        for f in findings:
            print(f"[{f.severity.upper():5}] {f.model}  {f.rule}")
            print(f"        {f.message}")

    return 1 if any(rank[f.severity] >= threshold for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
