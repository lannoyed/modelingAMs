# Pitfall: Connect rules & discipline resolution (Symphony)

## Rules
- Default to Symphony's built-in **automatic connect modules (A2D/D2A/A2R/R2A)**
  for digital<->analog boundaries. Don't declare a project-specific `connectrules`
  block or hand-roll a connect module unless a boundary needs an edge shape or
  behavior the automatic CM genuinely can't provide — see the 2026-07-01 revision
  below for why the earlier "always state connectrules explicitly" default was
  superseded.
- Digital control/data signals are plain `wire`, not the `logic` discipline —
  see 2026-07-01 revision.
- Never `<+` contribute from an `always`/`initial` block — event context only.
- `V()` read in an `always` block is a *sampled* value at that event, not continuous.
  Fine for ADCs, wrong for feedback.

## Discipline resolution
- Ground the design in a single disciplines.vams; don't redeclare `electrical`.
- For VHDL-AMS interop, keep boundary port disciplines standard and note the expected
  resolution so the cross-language CM matches.

## Fast check
- Every digital `wire` feeding an analog expression: is it going through
  `transition()` (directly, relying on the automatic D2A conversion) so Newton
  sees a finite edge, not a step? If not, add it.

## 2026-07-01 — REVISE — default to automatic connect modules, not a custom CM
**SUPERSEDES** the earlier "state connectrules explicitly for every boundary /
make the CM explicit when timing-critical" default. Real review feedback on the
`sc_tripler` SC converter model: a hand-declared `connectrules` block plus a
project-specific `l2e_module` (logic->electrical, `transition()`-smoothed) was
built to make the phase-switch boundary "explicit." The reviewer rejected it —
Symphony already provides automatic A2D/D2A/A2R/R2A connect modules for exactly
this boundary, and re-declaring one is redundant surface area, not extra safety.

**New default:**
- Declare digital control/clock/data signals as plain `wire` (not `logic`, not
  `electrical`). Let Symphony's automatic connect module handle the digital<->
  analog resolution.
- Get the finite edge you need for Newton by calling `transition(wire_signal, 0,
  trise, tfall)` **directly inside the analog block of the receiving module**,
  on the digital net itself. The automatic D2A conversion supplies the real value
  `transition()` operates on; no separate connect-module instance is needed to
  own that edge. See `pitfalls/convergence.md`.
- Only reach for an explicit, hand-declared connect module when the boundary
  needs something the automatic CM can't do (e.g., a non-standard resolution
  function across a VHDL-AMS boundary) — and say specifically what that need is,
  rather than declaring one by default "to be explicit."
- This also simplifies parameter flow: `trise`/`tfall` become ordinary switch/
  module parameters (see `pitfalls/parameters.md`) instead of connect-module
  overrides threaded through a `connectrules` mapping.
