# Pitfall: Connect rules & discipline resolution (Symphony)

## Rules
- State the assumed `connectrules` for EVERY electrical<->logic boundary in the
  deliverable. Symphony auto-inserts CMs, but silent insertion hides timing bugs.
- Make the CM explicit when the boundary is bidirectional or timing-critical.
- Never `<+` contribute from an `always`/`initial` block — event context only.
- `V()` read in an `always` block is a *sampled* value at that event, not continuous.
  Fine for ADCs, wrong for feedback.

## Discipline resolution
- Ground the design in a single disciplines.vams; don't redeclare `electrical`.
- For VHDL-AMS interop, keep boundary port disciplines standard and note the expected
  resolution so the cross-language CM matches.

## Fast check
- Every `logic` port touching analog: is its connectrule stated? If not, add it.
