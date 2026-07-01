# Skill Changelog

Each accepted SKILL-UPDATE lands here, newest first.
Format: `## YYYY-MM-DD — [ADD/REVISE] target — summary`

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
