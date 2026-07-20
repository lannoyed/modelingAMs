# LRM ground-truth text (pending download)

This directory will hold the Verilog-AMS LRM converted to verbatim, greppable
per-clause text files, plus a generated `INDEX.md` (topic -> file + PDF page).
Agents grep these files instead of recalling the standard from memory.

## Status: source PDF not yet available in this environment

The remote session's network egress policy blocks `accellera.org`, so the PDF
could not be fetched automatically. To complete the (one-time) conversion:

1. Either add `accellera.org` to the environment's network allowlist
   (Claude Code on the web -> environment settings -> network policy), or
   download the PDF yourself and commit/place it at `docs/VAMS-LRM-2023.pdf`:
   https://accellera.org/images/downloads/standards/v-ams/VAMS-LRM-2023.pdf
2. Run: `python3 scripts/lrm_convert.py`
   (needs `pypdf` and poppler's `pdftotext`; the script is deterministic and
   involves no LLM — the text lands here verbatim.)

The script also extracts the formal-syntax (BNF) annex verbatim to
`.claude/skills/verilog-ams/references/grammar_bnf.txt` and writes `INDEX.md`
from the PDF bookmarks.

Note: the repo docs reference LRM 2.4 (2014); VAMS-LRM-2023 is Accellera's
newer revision of the same standard. Keep clause citations tagged with the
revision they came from.
