#!/usr/bin/env python3
"""Convert the Verilog-AMS LRM PDF into greppable per-clause text files.

One-shot, token-free pipeline (no LLM involved):

    python3 scripts/lrm_convert.py [path/to/VAMS-LRM.pdf]

Produces:
  docs/lrm/<NN>_<slug>.txt          one file per top-level clause/annex,
                                    extracted verbatim with `pdftotext -layout`
  docs/lrm/INDEX.md                 two-level outline -> file + PDF page map,
                                    generated from the PDF bookmarks
  .claude/skills/verilog-ams/references/grammar_bnf.txt
                                    the formal-syntax annex, verbatim

Rationale (see .claude/skills/verilog-ams/SKILL.md, "LRM ground truth"):
agents grep the normative text instead of recalling it, so the conversion
must be verbatim — no summarization step is allowed in this pipeline.

Requires: pypdf (outline/bookmarks), poppler-utils (pdftotext).
"""

import re
import subprocess
import sys
from pathlib import Path

from pypdf import PdfReader

REPO = Path(__file__).resolve().parent.parent
DEFAULT_PDF = REPO / "docs" / "VAMS-LRM-2023.pdf"
OUT_DIR = REPO / "docs" / "lrm"
GRAMMAR_OUT = REPO / ".claude" / "skills" / "verilog-ams" / "references" / "grammar_bnf.txt"

# Bookmark titles that mark the formal-syntax annex across LRM revisions.
GRAMMAR_ANNEX_RE = re.compile(r"formal\s+syntax|syntax\s+definition", re.IGNORECASE)


def slugify(title: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")
    return s[:60]


def flat_outline(reader: PdfReader):
    """Return [(level, title, zero_based_page)] for the first two outline levels.

    pypdf outlines interleave Destination objects and nested lists (children
    follow their parent as a list), hence the manual walk.
    """
    out = []

    def collect(items, level):
        for item in items:
            if isinstance(item, list):
                collect(item, level + 1)
            elif level <= 1:
                try:
                    page = reader.get_destination_page_number(item)
                except Exception:
                    continue
                out.append((level, item.title.strip(), page))

    collect(reader.outline, 0)
    return out


def pdftotext(pdf: Path, first: int, last: int, dest: Path) -> None:
    subprocess.run(
        ["pdftotext", "-layout", "-f", str(first), "-l", str(last), str(pdf), str(dest)],
        check=True,
    )


def main() -> int:
    pdf = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PDF
    if not pdf.exists():
        print(f"error: {pdf} not found.")
        print("Download the LRM (accellera.org, Verilog-AMS standard) to that path first.")
        return 1

    reader = PdfReader(str(pdf))
    n_pages = len(reader.pages)
    outline = flat_outline(reader)
    top = [(t, p) for lvl, t, p in outline if lvl == 0]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    GRAMMAR_OUT.parent.mkdir(parents=True, exist_ok=True)

    index_lines = [
        "# Verilog-AMS LRM — greppable text index",
        "",
        f"Source: `{pdf.name}` ({n_pages} pages), converted verbatim by",
        "`scripts/lrm_convert.py` (pdftotext -layout). Grep these files instead of",
        "recalling the standard from memory; page numbers below are PDF pages.",
        "",
    ]

    if not top:
        # No bookmarks: fall back to fixed 50-page chunks so the text is still greppable.
        print("warning: PDF has no outline; falling back to 50-page chunks")
        for start in range(1, n_pages + 1, 50):
            end = min(start + 49, n_pages)
            dest = OUT_DIR / f"pages_{start:04d}_{end:04d}.txt"
            pdftotext(pdf, start, end, dest)
            index_lines.append(f"- `{dest.name}` — PDF pages {start}-{end}")
    else:
        for i, (title, page0) in enumerate(top):
            first = page0 + 1
            # Include the boundary page on both sides: a clause can end on the
            # page where the next one's heading sits. Slight duplication is
            # preferable to grep-invisible tail text.
            last = top[i + 1][1] + 1 if i + 1 < len(top) else n_pages
            dest = OUT_DIR / f"{i:02d}_{slugify(title)}.txt"
            pdftotext(pdf, first, last, dest)
            index_lines.append(f"\n## `{dest.name}` — {title} (PDF pp. {first}-{last})")
            for lvl, t, p in outline:
                if lvl == 1 and page0 <= p < last:
                    index_lines.append(f"- {t} (p. {p + 1})")
            if GRAMMAR_ANNEX_RE.search(title):
                GRAMMAR_OUT.write_bytes(dest.read_bytes())
                print(f"grammar annex '{title}' -> {GRAMMAR_OUT}")

    (OUT_DIR / "INDEX.md").write_text("\n".join(index_lines) + "\n")
    print(f"wrote {len(list(OUT_DIR.glob('*.txt')))} text files + INDEX.md to {OUT_DIR}")
    if top and not GRAMMAR_OUT.exists():
        print("warning: no bookmark matched the formal-syntax annex; extract it manually")
    return 0


if __name__ == "__main__":
    sys.exit(main())
