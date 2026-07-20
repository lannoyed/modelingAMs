#!/usr/bin/env python3
"""Deterministic structural lint for the repo's Verilog-AMS models.

    python3 scripts/vams_lint.py [file.vams ...]      (default: all of src/models)

This is not a parser — it is a line-scanner encoding the structural rules from
CLAUDE.md and .claude/skills/verilog-ams/pitfalls/ that a behavioral model must
never violate. Every check is mechanical on purpose: a reference document tells
an agent what is right, this script proves the emitted module is not wrong.
Checks (E = error, W = warning):

  E timescale     module file must start with the repo-wide `timescale 1ns / 1ps
  E realtime      $realtime inside an analog block ($abstime is the analog clock)
  E contrib-ctx   `<+` contribution outside an analog block (e.g. always/initial)
  E delay-analog  `#` delay inside an analog block (delays are digital-only)
  E discipline    discipline/nature declared outside src/disciplines/disciplines.vams
  E modname       module name != filename stem
  W no-analog     file uses electrical/branch quantities but has no analog block

Exit status: number of errors (0 = clean).
"""

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DISCIPLINES_FILE = REPO / "src" / "disciplines" / "disciplines.vams"

TIMESCALE_RE = re.compile(r"`timescale\s+1\s*ns\s*/\s*1\s*ps")
CONTRIB_RE = re.compile(r"<\+")
DELAY_RE = re.compile(r"(^|\s)#\s*[\w(]")
DISCIPLINE_RE = re.compile(r"^\s*(discipline|nature)\b")
MODULE_RE = re.compile(r"^\s*module\s+([A-Za-z_]\w*)")
ANALOG_START_RE = re.compile(r"^\s*analog\b(?!\s+function)")
QUANTITY_RE = re.compile(r"\b[VI]\s*\(")


def strip_comments(lines):
    """Remove // and /* */ comments so keywords in prose don't trigger checks."""
    out, in_block = [], False
    for raw in lines:
        line = raw
        if in_block:
            end = line.find("*/")
            if end < 0:
                out.append("")
                continue
            line, in_block = line[end + 2:], False
        while True:
            start = line.find("/*")
            if start < 0:
                break
            end = line.find("*/", start + 2)
            if end < 0:
                line, in_block = line[:start], True
                break
            line = line[:start] + line[end + 2:]
        out.append(line.split("//")[0])
    return out


def analog_regions(lines):
    """Approximate the line ranges of analog blocks via begin/end nesting."""
    regions, i = [], 0
    while i < len(lines):
        if ANALOG_START_RE.search(lines[i]):
            depth, j, seen_begin = 0, i, False
            while j < len(lines):
                depth += len(re.findall(r"\bbegin\b", lines[j]))
                n_end = len(re.findall(r"\bend\b(?!case|module|function)", lines[j]))
                depth -= n_end
                seen_begin = seen_begin or depth > 0
                if seen_begin and depth <= 0:
                    break
                if not seen_begin and lines[j].rstrip().endswith(";"):
                    break  # single-statement analog block
                j += 1
            regions.append((i, j))
            i = j
        i += 1
    return regions


def lint(path: Path):
    errors, warnings = [], []
    raw = path.read_text().splitlines()
    lines = strip_comments(raw)

    module_line = next((i for i, l in enumerate(lines) if MODULE_RE.match(l)), None)
    if module_line is not None:
        # `timescale must precede the module (header comments before it are fine);
        # include files without a module (e.g. *_PARAM.vams) carry no timescale.
        if not any(TIMESCALE_RE.search(l) for l in lines[: module_line + 1]):
            errors.append((1, "timescale", "no `timescale 1ns / 1ps before module declaration"))
        name = MODULE_RE.match(lines[module_line]).group(1)
        if name != path.stem:
            errors.append((module_line + 1, "modname", f"module '{name}' != filename stem '{path.stem}'"))

    regions = analog_regions(lines)

    def in_analog(idx):
        return any(a <= idx <= b for a, b in regions)

    for idx, line in enumerate(lines):
        n = idx + 1
        if "$realtime" in line and in_analog(idx):
            errors.append((n, "realtime", "$realtime inside analog block — use $abstime"))
        if CONTRIB_RE.search(line) and not in_analog(idx):
            errors.append((n, "contrib-ctx", "`<+` contribution outside analog block"))
        if DELAY_RE.search(line) and in_analog(idx):
            errors.append((n, "delay-analog", "`#` delay inside analog block"))
        if DISCIPLINE_RE.match(line) and path.resolve() != DISCIPLINES_FILE:
            errors.append((n, "discipline", "discipline/nature declared outside disciplines.vams"))

    if not regions and any(QUANTITY_RE.search(l) for l in lines):
        warnings.append((1, "no-analog", "V()/I() used but no analog block found"))

    return errors, warnings


def main() -> int:
    targets = [Path(a) for a in sys.argv[1:]] or sorted((REPO / "src" / "models").rglob("*.vams"))
    total_errors = 0
    for f in targets:
        errors, warnings = lint(f)
        total_errors += len(errors)
        for n, code, msg in errors:
            print(f"{f.relative_to(REPO) if f.is_absolute() else f}:{n}: error [{code}] {msg}")
        for n, code, msg in warnings:
            print(f"{f.relative_to(REPO) if f.is_absolute() else f}:{n}: warning [{code}] {msg}")
    print(f"vams_lint: {len(targets)} file(s), {total_errors} error(s)")
    return min(total_errors, 255)


if __name__ == "__main__":
    sys.exit(main())
