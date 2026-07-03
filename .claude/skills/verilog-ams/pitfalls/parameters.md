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
- **Naming convention: `_top` vs. sub-module** (see the 2026-07-03 entries
  below for the full reasoning). Every model is one of two kinds, named and
  written accordingly:
  - **`<block>_top`** — the terminal module a testbench instantiates
    directly; nothing else in the repo instantiates it with overrides. Use
    the `<MODULE_NAME>_PARAM.vams` convention below, `from (...)` and all,
    for elaboration-time range checking.
  - **sub-module** — instantiated inside another module with per-instance
    named overrides (`#(.ron(ron_tier1), ...)`). Declare its own standalone
    ANSI parameters with sensible defaults, **no `from`/`exclude`**, and
    range-guard them at runtime instead (see the second 2026-07-03 entry).
- For a `_top` module with more than a handful of parameters, put the
  defaults in a sibling `<MODULE_NAME>_PARAM.vams` file and `` `include`` it
  **directly inside that module's `#( ... )` list**, so each default keeps its
  own `from (...)` range guard instead of losing it behind a `` `define``:
  ```verilog
  // sc_tripler_top_PARAM.vams
      parameter real c1 = 100n from (0:inf),   // note: comma-separated, no
      parameter real c2 = 100n from (0:inf)    // trailing comma on the last line
  ```
  ```verilog
  // sc_tripler_top.vams
  module sc_tripler_top #(
  `include "sc_tripler_top_PARAM.vams"
  ) ( ... );
  ```
  **Only `` `include`` a `_PARAM.vams` file inside `#( ... )`, never inside the
  module body.** Its content is a comma-chained run of complete
  `parameter_declaration`s with no terminating `;` — per VAMS-2023 Annex A.2,
  that shape is legal *only* inside `module_parameter_port_list`
  (`#( parameter_declaration {, parameter_declaration} )`); the module body
  requires each `parameter_declaration` to be its own `;`-terminated
  statement. Splicing the same file into the body will not parse.

  Sub-modules instantiated inside the top block (e.g. `generic_switch`) do
  **not** include that file themselves — they declare their own standalone
  ANSI parameters with sensible defaults, and receive the top block's actual
  values purely through instantiation overrides (`#(.ron(ron_tier1), ...)`).
  This keeps the parameter-file convention scoped to "one file per `_top`
  model" rather than a shared global constants file that every module reaches
  into directly.

## Fast check
- Every module meant to be instantiated with per-instance parameter overrides:
  ANSI-style `#( ... )` header, not body-declared `parameter` statements, and
  no `from`/`exclude` on it (runtime-guarded instead)?
- `_top` module: named `<block>_top`, parameters sourced from
  `<block>_top_PARAM.vams` spliced inside `#( ... )` (never the body), each
  with a `from (...)` guard?
- Any `real` computed from parameters alone and never reassigned inside
  `analog`? Make it a `localparam`.
- A `<MODULE_NAME>_PARAM.vams` file: is it included only inside its own top
  module's `#( ... )` list — never inside a module body, never by a
  sub-module it instantiates?

## 2026-07-01 — ADD — first stated from `sc_tripler`/`sc_switch` review
Prior pattern skeletons in this skill (`opamp.md`, `converter.md`, `sensor.md`)
still use body-declared `parameter` statements. That's not wrong Verilog-AMS,
but it's not the convention this repo's reviewer wants going forward — new
models should follow the ANSI-header + PARAM-file convention above. Existing
skeletons are left as-is (never delete a pitfall/pattern, only supersede) but
any model derived from them should be written the new way.

## 2026-07-03 — REVISE — `from`/`exclude` inside the ANSI header: Symphony nonconformance, not an LRM rule
**SUPERSEDED by the entry below** — this entry's fix over-generalized from a
single failing case (`generic_switch`, a bare standalone module) to *every*
ANSI header in the repo, including `sc_tripler`'s `` `include``-spliced
`_PARAM.vams` header, which was never actually shown to fail and was changed
without evidence. Kept for the grammar research, which still stands; the
"strip `from` from every ANSI header" conclusion below it does not.
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

## 2026-07-03 — REVISE — narrowed: `_top` vs. sub-module, not "no `from` anywhere"
Correction to the entry above. `generic_switch`'s bare, self-authored ANSI
header (`parameter real ron = 50e-3 from (0:inf), ...` typed directly, no
`` `include``) is the *only* construct with an actual reproduced Symphony
failure. `sc_tripler`'s original header — `` `include``-splicing
`_PARAM.vams`'s `from (0:inf)`-bearing content inside `#( ... )` — was never
shown to fail and was reverted back to that original form (module renamed
`sc_tripler_top` per the naming convention below).

The two constructs differ in a way that matters regardless of the unexplained
Symphony error: **override-binding reliability is a sub-module concern, not a
`_top`-module concern.** `generic_switch` gets instantiated with `#(.ron(...),
...)` overrides repeatedly (by `sc_tripler_top`); a `_top` module is the
terminal block a testbench instantiates, never itself overridden by anything
else in this repo. So:
- **`_top` modules** keep the ANSI-header + `_PARAM.vams` + `from (...)`
  convention as originally written — elaboration-time bounding, and
  override-binding reliability isn't in play since nothing overrides a `_top`
  module's parameters.
- **Sub-modules** (instantiated with per-instance overrides) keep bare ANSI
  headers with **runtime** guards (`@(initial_step)` + `localparam` clamp, per
  the entry above) — this is where the one confirmed `from`-in-ANSI-header
  failure actually lives, and where override-binding reliability is the
  reason the header can't be reshuffled to work around it.

Naming convention: `<block>` → `<block>_top` signals "PARAM.vams + `from`,
elaboration-time bounding, never instantiated-with-overrides." No suffix on a
module signals "bare ANSI header, runtime-guarded, gets instantiated with
overrides." `sc_tripler` → `sc_tripler_top`; `generic_switch` needed no rename
(already a sub-module, already runtime-guarded).

Also confirmed (LRM-grounded, not just empirical): a `_PARAM.vams` file's
comma-chained, semicolon-free `parameter_declaration` list is *only* legal
spliced inside `#( ... )`. Moving that same `` `include`` into a module body —
tried as an intermediate fix — does not parse; body-level parameter
declarations each need their own terminating `;`. See the "Rules" section
above for the corrected, precise statement of both conventions.

## 2026-07-03 (later still) — REVISE — sub-module runtime guard: `$error`, not clamp-and-warn
Refines the runtime-guard mechanism from the two entries above (the
`_top`-vs-sub-module split itself is unchanged). Original version clamped an
out-of-range override to the module's own default (`(x > 0.0) ? x :
x_default`) and reported it with `$display`, so the sim kept running on a
substituted value. Simpler and more honest: `$error` at `@(initial_step)` on
the raw parameter, no clamp, no substituted default:
```verilog
if (tfall <= 0.0)
  $error("generic_switch %m: tfall=%g out of range (0:inf)", tfall);
```
A bad override is a configuration mistake, not a recoverable runtime
condition — silently continuing on a value the caller didn't ask for hides
the mistake instead of surfacing it. `$error` halts the run with the
offending value and instance path (`%m`) instead. No `_default` localparams,
no `_g`-suffixed clamped variables — `gon`/`goff` (and anywhere else a guarded
parameter is used) read the raw parameter directly, since if it were
out-of-range `$error` has already stopped elaboration before those values
matter. See `src/models/converters/generic_switch.vams` for the current
reference implementation.

## 2026-07-03 (final) — REVISE — guard block: plain `initial`, not `analog`/`@(initial_step)`
Further refines the same guard, same conclusion elsewhere unchanged. Symphony
accepts exactly **one `analog` block per module** — note this sits in tension
with VAMS-2023 §6.2's own text ("A module definition may have multiple analog
blocks... internally combine into a single analog block in the order that
[they] appear"), so, same pattern as the ANSI-header `from` finding, treat it
as a tool restriction to design around, not a spec rule. Nesting the guard
inside the main `analog` block via `@(initial_step)` (or giving it its own
`analog initial` block, which not all tools support as a separate top-level
construct either) both risk colliding with that one-block limit or the
guard's own syntax. A plain digital `initial` block has no such
restriction — Verilog allows any number of them — and `$error`/parameter
reads work identically there since parameters are elaboration-time constants
regardless of domain:
```verilog
initial begin
  if (tfall <= 0.0)
    $error("generic_switch %m: tfall=%g out of range (0:inf)", tfall);
end

analog begin
  I(p, n) <+ ...;
end
```
One `initial` block for guards, one `analog` block for the physics — never
merge the two, and never add a second `analog` block to hold more guards.
