#!/usr/bin/env python3
"""
render_output.py — render captured terminal output as a terminal-styled SVG.

Used once to produce demo/sql_anti_patterns_demo.svg for the README.
Pure stdlib; re-runnable if the demo output changes.

Usage:
    python demo/render_output.py
"""
from __future__ import annotations

import re
from html import escape
from pathlib import Path

ROOT = Path(__file__).parent
INPUT_TXT = ROOT / "output.txt"
OUTPUT_SVG = ROOT / "sql_anti_patterns_demo.svg"
PROMPT = "$ python scripts/sql_anti_patterns.py demo/dirty_model.sql"

# Terminal palette (inspired by One Dark / Tokyo Night)
BG = "#1a1b26"
FG = "#c0caf5"
PROMPT_FG = "#7aa2f7"
DIM = "#565f89"
RED = "#f7768e"
YELLOW = "#e0af68"
CYAN = "#7dcfff"
GREEN = "#9ece6a"

CHAR_W = 7.7   # monospace glyph width at font-size 13
LINE_H = 18    # line height
LEFT_PAD = 16
TOP_PAD = 42   # room for window chrome
RIGHT_PAD = 16
BOTTOM_PAD = 16

# Fake macOS-style window buttons at the top
WINDOW_DOTS = """\
<circle cx="20" cy="22" r="6" fill="#f7768e"/>
<circle cx="40" cy="22" r="6" fill="#e0af68"/>
<circle cx="60" cy="22" r="6" fill="#9ece6a"/>
<text x="50%" y="26" fill="#565f89" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" text-anchor="middle">senior-data-engineer — sql_anti_patterns.py</text>
"""


def colorize_line(line: str) -> str:
    """Return SVG <tspan> fragments for a single output line."""
    # Severity marker: [ERROR] / [WARN ] / [INFO ]
    m = re.match(r"^(\[(ERROR|WARN |INFO )\])(\s+)(.*)$", line)
    if m:
        marker, sev, gap, rest = m.group(1), m.group(2).strip(), m.group(3), m.group(4)
        color = RED if sev == "ERROR" else YELLOW if sev == "WARN" else CYAN
        # Split rest into "file:line  rule"
        rest_m = re.match(r"^(\S+?:\d+)(\s+)(.+)$", rest)
        if rest_m:
            loc, gap2, rule = rest_m.group(1), rest_m.group(2), rest_m.group(3)
            return (
                f'<tspan fill="{color}">{escape(marker)}</tspan>'
                f'<tspan fill="{FG}">{escape(gap)}</tspan>'
                f'<tspan fill="{PROMPT_FG}">{escape(loc)}</tspan>'
                f'<tspan fill="{FG}">{escape(gap2)}</tspan>'
                f'<tspan fill="{GREEN}">{escape(rule)}</tspan>'
            )
        return (
            f'<tspan fill="{color}">{escape(marker)}</tspan>'
            f'<tspan fill="{FG}">{escape(gap + rest)}</tspan>'
        )
    # Code-snippet line (starts with indented "> ")
    if re.match(r"^\s+> ", line):
        return f'<tspan fill="{DIM}">{escape(line)}</tspan>'
    # Message body (indented)
    if line.startswith("        "):
        return f'<tspan fill="{FG}">{escape(line)}</tspan>'
    # Header lines ("Scanned N SQL files.")
    return f'<tspan fill="{DIM}">{escape(line)}</tspan>'


def main() -> None:
    raw = INPUT_TXT.read_text(encoding="utf-8").rstrip("\n").splitlines()
    # Prepend the prompt line so readers see the invocation
    display = [PROMPT, ""] + raw

    # Determine width from longest line (bounded to keep SVG reasonable)
    max_len = max(len(ln) for ln in display)
    max_len = min(max_len, 120)
    width = int(LEFT_PAD + max_len * CHAR_W + RIGHT_PAD)
    height = int(TOP_PAD + len(display) * LINE_H + BOTTOM_PAD)

    lines_svg: list[str] = []
    for i, ln in enumerate(display):
        y = TOP_PAD + (i + 1) * LINE_H - 4
        if i == 0:
            content = (
                f'<tspan fill="{PROMPT_FG}">$ </tspan>'
                f'<tspan fill="{FG}">{escape(ln[2:])}</tspan>'
            )
        elif ln.strip() == "":
            content = ""
        else:
            content = colorize_line(ln)
        lines_svg.append(
            f'  <text x="{LEFT_PAD}" y="{y}" '
            f'font-family="ui-monospace, SFMono-Regular, Menlo, monospace" '
            f'font-size="13" xml:space="preserve">{content}</text>'
        )

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" role="img" '
        f'aria-label="Terminal output: senior-data-engineer sql_anti_patterns.py demo">\n'
        f'  <rect width="{width}" height="{height}" rx="8" fill="{BG}"/>\n'
        f'  {WINDOW_DOTS}\n'
        + "\n".join(lines_svg)
        + "\n</svg>\n"
    )

    OUTPUT_SVG.write_text(svg, encoding="utf-8")
    print(f"wrote {OUTPUT_SVG} ({width}x{height})")


if __name__ == "__main__":
    main()
