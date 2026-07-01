# modelingAMs

Verilog-AMS behavioral model library for analog/mixed-signal blocks, targeting
**Siemens Questa ADMS / Symphony** (Verilog-AMS LRM 2.4).

## Scope
Three stages per block, and nothing downstream:

    STRATEGY  ->  IMPLEMENTATION  ->  STIMULI (a written drive plan)

Testbenches, driver modules, analysis setups, and verification are out of scope.

## Layout
- `src/disciplines/` — shared `disciplines.vams` (single source of discipline truth)
- `src/models/analog/` — op-amps, LDOs, filters (conservative electrical)
- `src/models/converters/` — ADC/DAC, PLL (mixed-signal)
- `src/models/sensors/` — transducers (physical-domain -> electrical)
- `stimuli/` — stimulus-plan reports, `<block>.md` (sequences, corners, ranges)
- `docs/` — per-model strategy notes
- `.claude/` — Claude Code config: the modeling skill (patterns, pitfalls, upgrade loop)

## Working in this repo with Claude Code
`CLAUDE.md` at the root is read automatically. It defines the three-stage output
contract, Symphony ground rules, and engineering philosophy. The `verilog-ams` skill
under `.claude/skills/` provides vetted pattern skeletons and a self-upgrade loop: each
model ends with a `SKILL-UPDATE:` line whose accepted deltas fold back into the skill,
so the starting point improves over time.

## Conventions
- Model file == module name; stimulus plan is `stimuli/<block>.md`.
- Never redeclare a discipline outside `src/disciplines/disciplines.vams`.
- Every parameter range-guarded; every discontinuity smoothed for the Newton solver.
