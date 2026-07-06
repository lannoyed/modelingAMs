---
name: verilog-ams-modeling
description: Use when defining a modeling strategy, implementing a Verilog-AMS (.vams)
  behavioral model, or writing a stimulus plan for an analog/mixed-signal block
  targeting Siemens Questa ADMS / Symphony. Triggers on Verilog-AMS, AMS model,
  electrical discipline, `<+` contributions, connectrules, transition/slew/laplace,
  disciplines.vams, or any request to model an analog or mixed-signal block.
version: 2.0
---

# Verilog-AMS Modeling (Siemens Symphony)

## Scope
Three stages only: STRATEGY -> IMPLEMENTATION -> STIMULI (a written drive plan).
No testbenches, no driver modules, no analysis setups, no verification. See CLAUDE.md.

## When triggered, do this in order
1. Read the repo CLAUDE.md (three-stage output contract + Siemens ground rules).
2. Identify the block class -> read the matching file in `patterns/`.
3. Skim `pitfalls/` for anything relevant (always check `convergence.md`,
   `connect_rules.md`, and `parameters.md`).
4. Produce STRATEGY, IMPLEMENTATION, STIMULI.
5. Emit a SKILL-UPDATE candidate (protocol below).

## Discipline decision table
| Domain            | Discipline/type | Access    | Use when                              |
|-------------------|-----------------|-----------|---------------------------------------|
| Electrical node   | `electrical`    | V, I      | Conservative KCL/KVL nodes, real pins |
| Digital control   | `wire`          | —         | Clocks, enables, digital codes        |
| Abstract voltage  | `voltage`       | pot V     | Signal-flow, no current loading       |
| Abstract current  | `current`       | flow I    | Signal-flow current sources           |
| Thermal (opt.)    | `thermal`       | Temp,Pwr  | Self-heating / electro-thermal        |

Boundary rule (revised 2026-07-01): default to Symphony's automatic A2D/D2A/A2R/R2A
connect modules for any `electrical`<->`wire` boundary; smooth with `transition(wire_sig,
0, trise, tfall)` directly inside the receiving analog block. Only hand-declare a
project-specific connect module when the boundary needs something the automatic CM
can't provide. See `pitfalls/connect_rules.md`.

## Reusable patterns (`patterns/`)
- `opamp.md`     — op-amps, LDOs, filters (conservative electrical)
- `converter.md` — ADC/DAC, PLL (mixed-signal, sampling, quantization)
- `sensor.md`    — sensors/transducers (physical-domain -> electrical)
Each = strategy notes + vetted module skeleton + stimulus-plan notes.

## Known pitfalls (`pitfalls/`)
- `convergence.md`  — discontinuity smoothing, abstol, timestep control
- `connect_rules.md`— Symphony CM insertion, discipline resolution, interop
- `units.md`        — dimensional balance in `<+` contributions
- `parameters.md`   — ANSI-style parameter headers, `localparam` for derived
  constants, the `<MODULE_NAME>_PARAM.vams` convention, and why `from`/
  `exclude` belongs in a runtime guard, not the ANSI header, on Symphony
- `ports.md`        — port/net declaration style: never split a `wire` port's
  direction (ANSI header) from a `wire` net redeclaration (body) — "Symbol
  already defined"; use non-ANSI port style when the body needs the net

## SKILL-UPDATE protocol (the self-upgrade loop)
End every model with exactly one line:

    SKILL-UPDATE: [ADD pattern <class> | ADD pitfall <topic> | REVISE <file>] — <summary>

When the user accepts it:
1. Append the change to the target file under a dated `##` subsection.
2. Add a dated entry to CHANGELOG.md.
3. Never delete a pitfall — mark it `SUPERSEDED (see <ref>)` if it no longer applies.

Each conversation compounds: models start from vetted skeletons that grow richer over
time instead of a blank page.
