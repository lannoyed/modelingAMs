# Skill Changelog

Each accepted SKILL-UPDATE lands here, newest first.
Format: `## YYYY-MM-DD — [ADD/REVISE] target — summary`

## 2026-07-06 — ADD convergence.md (+ CLAUDE.md ground rule) — digital clocks & repo-wide timescale
First purely-digital blocks (`generic_clkgen`, `generic_sr_nonoverlap`): generate
clock/phases in the event-driven digital kernel (one analog breakpoint per edge, not
an analog source Newton must integrate), consumer owns the edge via `transition()`.
Repo-wide `` `timescale 1ns / 1ps`` added as a CLAUDE.md Symphony ground rule — a `#`
delay is in ns, so convert physical seconds to units (`t/1e-9`) and mind the 1 ps
floor. `reg`+`always`+`initial clk=0` over a self-referential net oscillator, which
latches at `x` (a net can't be seeded).

## 2026-07-03 (final) — REVISE parameters.md, generic_switch.vams — guard block is plain `initial`, not `analog`
Symphony accepts exactly one `analog` block per module (in tension with
VAMS-2023 §6.2, which permits multiple — another tool restriction, not a spec
rule, same pattern as the ANSI-header `from` finding). Moved the parameter
guard out of the `analog` block entirely into a plain digital `initial`
block, which has no such restriction and works identically for elaboration-
time `$error` checks on `real` parameters. `generic_switch.vams` now has one
`initial` block (guards) and one `analog` block (the `<+` contribution),
never merged. See `pitfalls/parameters.md`'s final 2026-07-03 entry.

## 2026-07-03 (latest) — REVISE parameters.md, generic_switch.vams — `$error`, not clamp-and-warn
Sub-module runtime range guard simplified: `@(initial_step) $error(...)` on an
out-of-range override, no `localparam` clamp-to-default and no `$display`
warning. A bad override is a configuration mistake, not something to paper
over with a substituted default — `$error` halts the run with the offending
value instead of continuing on a value the caller never asked for.
`generic_switch.vams` reads `ron`/`roff`/`trise`/`tfall` directly (no
`_g`-suffixed clamped variables) since `$error` has already stopped
elaboration before an out-of-range value could reach the analog equations.
See `pitfalls/parameters.md`'s latest 2026-07-03 entry.

## 2026-07-03 (later) — REVISE parameters.md — narrowed to `_top` vs. sub-module
Corrects the entry directly below: the "strip `from` from every ANSI header"
fix over-generalized from `generic_switch`'s single reproduced failure to
`sc_tripler` too, without evidence `sc_tripler` ever failed. Reverted
`sc_tripler` back to its original ANSI-header + `_PARAM.vams` + `from (...)`
form and renamed it `sc_tripler_top`, establishing a `_top`-suffix naming
convention: `_top` modules (terminal, never instantiated-with-overrides) use
elaboration-time `from (...)` bounding via a `_PARAM.vams` file spliced inside
`#( ... )`; sub-modules (instantiated with per-instance overrides, e.g.
`generic_switch`) keep the bare-header + runtime-guard fix from the entry
below, since override-binding reliability is specifically a sub-module
concern. Also confirmed a `_PARAM.vams` file's comma-chained,
semicolon-free parameter list only parses spliced inside `#( ... )` — moving
the same `` `include`` into a module body does not parse (VAMS-2023 Annex A.2:
module-body parameter declarations each need their own terminating `;`,
that's not the grammar rule this file's shape depends on). See
`pitfalls/parameters.md`'s two 2026-07-03 entries.

## 2026-07-03 — REVISE parameters.md, converter.md, SKILL.md
`sc_switch` rebranded to `generic_switch` (dropped the `tier` parameter — it
never fed an equation, pure traceability dead weight). Real Symphony
elaboration of `from (0:inf)` inside an ANSI `#( ... )` parameter port list
failed (`received keyword 'from' while expecting ')'`); traced against
VAMS-2023 Annex A.2 grammar and confirmed the LRM draws no distinction between
ANSI-header and body-level parameter positions for `value_range` — this is a
Symphony ADMS nonconformance, not a spec rule. New convention: ANSI headers
stay bare (no `from`/`exclude`), ranges enforced at runtime via an
`@(initial_step)` guard (`$display` warning) plus a `localparam` clamp. See
`pitfalls/parameters.md`'s 2026-07-03 entry and
`src/models/converters/generic_switch.vams` for the reference pattern.
`patterns/converter.md`'s reusable-switch-sub-module guidance updated to match
(module renamed, no `tier` field on the sub-module).

## 2026-07-01 — REVISE connect_rules.md, convergence.md, SKILL.md; ADD parameters.md; REVISE converter.md
Feedback from the `sc_tripler`/`sc_switch` SC converter model review:
- **SUPERSEDED:** "state connectrules explicitly / make the CM explicit by
  default" — default is now Symphony's automatic A2D/D2A/A2R/R2A connect
  modules; hand-declare a connect module only for a genuine unmet need.
- Digital control/data signals are `wire`, not the `logic` discipline.
  SKILL.md's discipline table and boundary rule corrected accordingly.
- Smoothing convention: `transition(wire_sig, 0, trise, tfall)` called
  directly inside the receiving analog block, no separate connect-module
  instance owning the edge (`convergence.md`).
- New `pitfalls/parameters.md`: ANSI-style `#( ... )` parameter headers
  (required for reliable named-parameter override at instantiation),
  `localparam` for parameter-derived constants (computed once, not per
  analog evaluation), and the `<MODULE_NAME>_PARAM.vams` convention —
  included only inside the top module's own `#( ... )` list, with sub-modules
  receiving values purely through instantiation overrides.
- `patterns/converter.md` gained an SC/charge-pump converter sub-section:
  physical netlist over algebraic transfer function (output impedance and
  its SSL/FSL corner should emerge from a transient sweep, not be asserted
  by formula), reusable switch sub-module with Strategy(Ron)/Factory(tier)
  hooks, phases as externally-driven `wire` ports, reservoir cap/load kept
  out of the model's scope.

## 2026-07-01 — REVISE scope — narrowed to three stages
- Dropped testbench + verification. Pipeline is now STRATEGY -> IMPLEMENTATION ->
  STIMULI (a written drive plan). Pattern files gained a Stimulus-plan section in
  place of the verification checklist. SKILL.md bumped to v2.0.

## 2026-07-01 — INIT — skill seeded
- SKILL.md, patterns/ (opamp, converter, sensor), pitfalls/ (convergence,
  connect_rules, units)
