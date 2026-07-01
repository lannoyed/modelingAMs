# Pitfall: Convergence (Symphony Newton solver)

## Symptoms
"No convergence at time X", timestep collapsing to abstol, oscillating iterations.

## Root causes & fixes
- **Hard `if`/discontinuous contributions** -> replace branch selection with
  `transition(sel, td, tr)` or a smooth tanh blend. Newton hates step changes.
- **Unbounded derivatives** (1/x near 0, sqrt of a going-negative arg) -> clamp the
  argument with a smooth floor before the operation.
- **Missing `$discontinuity`** when a switch is unavoidable (diode regions) ->
  announce it with `$discontinuity(0)` so the solver re-evaluates.
- **abstol too tight/loose** -> set per discipline in disciplines.vams; current nodes
  ~1e-12, voltage ~1e-6. Justify the number.
- **Instant transitions on logic->analog** -> call `transition(wire_signal, 0, trise,
  tfall)` directly on the digital `wire` inside the receiving analog block (relying
  on Symphony's automatic D2A conversion) rather than a hard 0/1 step. See the
  2026-07-01 revision below and `pitfalls/connect_rules.md`.

## Quick triage order
1. Grep the module for `if (` inside `analog` -> smooth or `$discontinuity` each.
2. Check every division/sqrt/log argument for a reachable zero/negative.
3. Confirm slew/transition on all edges crossing the AMS boundary.

## 2026-07-01 — REVISE — smooth digital control at the point of use
Reviewed pattern from `sc_switch` (SC converter model): conductance blended
directly on a `wire` control input,
`g = goff + (gon-goff)*transition(ctrl, 0, trise, tfall);`
No separate connect-module instance owns the edge — the automatic D2A gives
`transition()` a real value to work with, and `trise`/`tfall` are ordinary
module parameters. This is now the default pattern for any switch/gate whose
on/off state is driven by a digital net; only fall back to a hand-declared
connect module for a boundary need `transition()` at the point of use can't
cover (see `pitfalls/connect_rules.md`).
