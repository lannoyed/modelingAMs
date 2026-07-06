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

## 2026-07-06 — ADD — digital `#` delays: repo-wide `timescale 1ns/1ps, convert seconds to units
First purely-digital blocks in the repo (`generic_clkgen`, `generic_sr_nonoverlap`)
generate a clock/phases in the event-driven digital kernel — the correct AMS
choice: an analog square-wave source would force Newton to integrate a stiff,
fast-switching node every cycle, whereas a digital clock costs the analog solver
only one breakpoint per edge. Two rules that come with that:
- **Generate the clock digitally, not as an analog source.** No `analog` block;
  the output is a raw digital `wire`/`reg`. The finite edge Newton needs is applied
  by the *consumer* via `transition()` at its own boundary — never pre-shape the
  edge in the clock module (double-smoothing).
- **One repo-wide `` `timescale 1ns / 1ps`` (CLAUDE.md ground rule).** A `#` delay
  is therefore in **nanoseconds**, not seconds. Keep the user-facing parameter
  physical (freq in Hz, dead time in s) and convert once at elaboration:
  `` localparam real d_units = t_seconds / 1e-9; `` then `#(d_units)`. Anything below
  the 1 ps precision rounds to zero (the floor on `tnov` / on clock resolution —
  ~0.1% of the period at 1 GHz). A self-referential net oscillator
  (`assign #d clk = ~clk & en;`) is rejected: a net can't be seeded, so `clk`
  latches at `x` forever when `en` is high at t=0 (`~x&1 = x`). Use `reg` + `always`
  with `initial clk = 0` so a free-running clock actually starts.
