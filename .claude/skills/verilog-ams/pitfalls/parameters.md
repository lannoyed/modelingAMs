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
