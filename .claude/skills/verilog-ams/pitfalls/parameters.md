# Pitfall: Parameter declaration & override (Symphony)

## Rules
- Declare parameters in the **ANSI-style module header**, not as body statements:
  ```verilog
  module foo #(
      parameter real ron = 50m from (0:inf)
  ) (
      inout p, n
  );
  ```
  not
  ```verilog
  module foo(p, n);
    inout p, n;
    parameter real ron = 50m from (0:inf);
  ```
  Named instantiation-time overrides (`foo #(.ron(2.0)) u1 (...)`) need to bind
  reliably during Symphony elaboration; the ANSI header is the form that does
  that consistently. Default to it for every new module, including sub-modules
  meant to be instantiated with per-instance overrides.
- Compute derived, parameter-only constants (a conductance `1/ron`, a corner
  frequency from other parameters, etc.) as `localparam`, not as a `real`
  variable recomputed inside `analog` every evaluation:
  ```verilog
  localparam real gon = 1.0 / ron;   // once, at elaboration
  ```
  not
  ```verilog
  analog begin
    gon = 1.0 / ron;                // recomputed every timestep for nothing
  ```
- For a top-level module with more than a handful of parameters, put the
  defaults in a sibling `<MODULE_NAME>_PARAM.vams` file and `` `include`` it
  **directly inside that module's `#( ... )` list**, so each default keeps its
  own `from (...)` range guard instead of losing it behind a `` `define``:
  ```verilog
  // sc_tripler_PARAM.vams
      parameter real c1 = 100n from (0:inf),   // note: comma-separated, no
      parameter real c2 = 100n from (0:inf)    // trailing comma on the last line
  ```
  ```verilog
  // sc_tripler.vams
  module sc_tripler #(
  `include "sc_tripler_PARAM.vams"
  ) ( ... );
  ```
  Sub-modules instantiated inside the top block (e.g. a reusable switch) do
  **not** include that file themselves — they declare their own standalone
  ANSI parameters with sensible defaults, and receive the top block's actual
  values purely through instantiation overrides (`#(.ron(ron_tier1), ...)`).
  This keeps the parameter-file convention scoped to "one file per top-level
  model" rather than a shared global constants file that every module reaches
  into directly.

## Fast check
- Every module meant to be instantiated with per-instance parameter overrides:
  ANSI-style `#( ... )` header, not body-declared `parameter` statements?
- Any `real` computed from parameters alone and never reassigned inside
  `analog`? Make it a `localparam`.
- A `<MODULE_NAME>_PARAM.vams` file: is it included only by its own top module,
  never by a sub-module it instantiates?

## 2026-07-01 — ADD — first stated from `sc_tripler`/`sc_switch` review
Prior pattern skeletons in this skill (`opamp.md`, `converter.md`, `sensor.md`)
still use body-declared `parameter` statements. That's not wrong Verilog-AMS,
but it's not the convention this repo's reviewer wants going forward — new
models should follow the ANSI-header + PARAM-file convention above. Existing
skeletons are left as-is (never delete a pitfall/pattern, only supersede) but
any model derived from them should be written the new way.

## 2026-07-03 — REVISE — `from`/`exclude` inside the ANSI header: Symphony nonconformance, not an LRM rule
`sc_switch.vams`/`sc_tripler_PARAM.vams` (per the ADD above) put `from (0:inf)`
range clauses directly inside the ANSI `#( ... )` parameter port list. Real
Symphony elaboration of that exact pattern (generic_switch, the sc_switch
rebrand) fails:
```
[Failure] Syntax error : received keyword 'from' while expecting ')'
```
Traced against VAMS-2023 Annex A.2 grammar before concluding anything:
`module_parameter_port_list ::= # ( parameter_declaration {, parameter_declaration} )`
and body-level `non_port_module_item ::= ... | parameter_declaration ;` both
resolve through the *same* `parameter_declaration -> list_of_param_assignments
-> param_assignment` chain, and `value_range` (`from`/`exclude`) attaches to
`param_assignment` itself (A.2.4/A.2.5). The grammar draws no distinction
between the ANSI-header and body-level positions — so `from`/`exclude` in the
ANSI header is legal per spec. Symphony's ADMS front end rejects it anyway.
**Treat this as a tool nonconformance to route around, not an LRM restriction
to cite as justification.**

Fix, superseding the SUPERSEDED-but-not-deleted examples above that show
`from (...)` inside `#( ... )`:
- ANSI header parameters stay **bare** — no `from`/`exclude` — to keep
  reliable per-instance override binding (the reason ANSI was adopted in the
  first place, see the ADD entry above).
- Guard the range at **runtime** instead, inside the module's own `analog`
  block: `@(initial_step) begin if (out of range) $display("WARNING ..."); end`,
  and a `localparam` clamp (`(x > 0.0) ? x : x_default`) used everywhere the
  raw parameter would otherwise be read. This is *more* defensive than
  elaboration-time rejection, not less — it reports a clear message and keeps
  the sim running on a defined value instead of a possibly opaque elaboration
  failure.
- A parameter that's purely a passthrough override into a sub-module (e.g. a
  top block forwarding `ron_tier1` straight into a `generic_switch` instance)
  does not need its own duplicate guard — the sub-module guards its own
  inputs. Only guard parameters a module actually reads in its own `<+`
  contributions.

See `src/models/converters/generic_switch.vams` for the reference
implementation of this pattern.
