# CLAUDE.md — modelingAMs

Repository guidance for Claude Code. Read this before touching any file.

## What this repo is
A library of **Verilog-AMS behavioral models** for analog/mixed-signal blocks,
targeting **Siemens Questa ADMS / Symphony** (Verilog-AMS LRM 2.4, VHDL-AMS interop
capable). Each model elaborates cleanly under Symphony's Newton-based mixed-signal
solver.

## Scope — three stages, nothing more
Every unit of work moves through exactly these stages and stops:

    1. STRATEGY        modeling approach: disciplines, decomposition, patterns
    2. IMPLEMENTATION  the .vams module
    3. STIMULI         a report of what sequences/corners to drive it with

**Out of scope:** testbenches, driver modules, analysis setups (`.tran`/`.ac`/
`.noise`), verification checklists, running or debugging simulations. Do not create
`tb_*.vams`, `.do` scripts, or waveform assertions. The stimuli stage is a written
plan, not an executable driver.

---

## Repository layout
```
src/
  disciplines/      Shared disciplines.vams — the single source of discipline truth
  models/
    analog/         Op-amps, LDOs, filters (conservative electrical)
    converters/     ADC/DAC, PLL (mixed-signal: sampling + quantization)
    sensors/        Transducers (physical-domain -> electrical)
stimuli/            Stimulus-plan reports: <block>.md (sequences, corners, ranges)
docs/               Per-model strategy notes
.claude/
  skills/verilog-ams/  The modeling skill (patterns, pitfalls, self-upgrade loop)
```

## Naming conventions
- Model: `src/models/<class>/<block>.vams`, module name == filename stem.
- Stimulus plan: `stimuli/<block>.md`.
- Never redeclare a discipline outside `src/disciplines/disciplines.vams`.

---

## Engineering philosophy (applies to every deliverable)
- **Separation of concerns.** Model physics is decoupled from stimulus definition. A
  model never contains its own drive sources.
- **Composition over inheritance.** Build complex blocks by instantiating vetted
  sub-models, not by copy-pasting equations. A PLL instantiates a VCO model.
- **Design patterns, proactively.** Reach for Strategy (swappable quantizer/rounding),
  Factory (corner/config selection) where they make a model easier to extend. Name the
  pattern in the STRATEGY section.
- **Defensive modeling.** Every parameter range-guarded: `parameter real X = d from
  [lo:hi];`. Reachable divide-by-zero, `sqrt`/`log` of negative, and unbounded
  derivatives are clamped. Silent failures are unacceptable.
- **Maintainability.** Write as if a different engineer extends this in six months.
  Comment the physics and the intent (the "why"), never the syntax.
- **Translation layer.** For each nontrivial metric (gm, poles, ENOB, slew rate,
  phase noise) add a one-line plain-English note on what it means for circuit behavior.

---

## Siemens Symphony ground rules
- **Timescale:** every module begins with `` `timescale 1ns / 1ps`` — the single
  repo-wide time unit / precision. Change it only if a model genuinely cannot be
  expressed at this unit/precision, and say why in the header. Consequence for any
  module that uses `#` delays (digital clocks, gates): a delay is in **nanoseconds**,
  so a physical delay of `T` seconds is written `` `#(T/1e-9)` `` (scale by the 1 ns
  unit; keep the user-facing parameter in seconds/Hz and convert with a `localparam`).
  Anything below the 1 ps precision rounds to zero.
- **Time:** use `$abstime`, never `$realtime`, inside `analog` blocks.
- **Solver:** smooth every discontinuity — `transition()`, `slew()`, `laplace_*`, and
  `$discontinuity` where a hard switch is unavoidable. Prefer a smooth blend over a
  hard `if` to help Newton converge.
- **Tolerances:** declare `abstol` per discipline in `disciplines.vams` and justify the
  value (current nodes ~1e-12, voltage ~1e-6 as starting points).
- **Connect rules:** state the assumed `connectrules` for every `electrical`<->`logic`
  boundary. Make the connect module explicit when the boundary is bidirectional or
  timing-critical. Never leave a mixed-net boundary implicit.
- **Contributions:** `<+` only inside `analog begin...end`. Never contribute from an
  `always`/`initial` block.
- **Interop:** for blocks beside VHDL-AMS, keep boundary port disciplines standard and
  note the expected resolution.

---

## Output contract (produce all three, in order)
1. **STRATEGY** — intent; conservation vs. signal-flow per port; analog/digital split;
   sub-model composition; which design pattern applies and why; connect-rule
   assumptions. For large models, post STRATEGY and wait for approval before code.
2. **IMPLEMENTATION** — the `.vams` module: header docstring (purpose, the "why",
   LRM/Symphony features used, limitations); ports (name/direction/discipline);
   parameters (name, unit, default, range guard, meaning); named `analog` block;
   contributions via `<+`; physics/intent comments.
3. **STIMULI** — a written report of what to drive the model with: input sequences
   (e.g., DC sweep range, step edges, PWL shape), corners/parameter settings to
   exercise, and which behavior each sequence is meant to expose. Prose + tables, not
   code. Save to `stimuli/<block>.md`.

## Interaction style
- Direct and insightful. Challenge quick/lumped shortcuts when a conservative
  formulation is more correct; explain the tradeoff.
- If a metric is ambiguous (gain = DC vs AC vs loop; bandwidth = -3dB vs GBW), ask
  which and why it matters before coding.
- Proactively flag convergence or solver-efficiency wins (e.g. replacing a hard `if`
  with `transition()`).

## The self-upgrade loop
End every model by emitting exactly one line:

    SKILL-UPDATE: [ADD pattern <class> | ADD pitfall <topic> | REVISE <file>] — <summary>

When accepted, the delta is folded into `.claude/skills/verilog-ams/` and logged in
its CHANGELOG. Pitfalls are never deleted, only marked superseded. Each conversation
starts from richer, vetted skeletons than the last.
