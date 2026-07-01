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
- **Instant transitions on logic->analog** -> give connect modules finite tr/tf.

## Quick triage order
1. Grep the module for `if (` inside `analog` -> smooth or `$discontinuity` each.
2. Check every division/sqrt/log argument for a reachable zero/negative.
3. Confirm slew/transition on all edges crossing the AMS boundary.
