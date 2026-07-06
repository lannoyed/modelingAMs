# Pitfall: Port & net declaration style (Symphony)

## Symptom
```
[Error] Symbol phi2 is already defined and cannot be redefined as net
```
on every `wire` port of a module, at elaboration.

## Root cause
Splitting a `wire` port across the **ANSI header** and a **body net
declaration**. An ANSI-style port header already *implicitly declares each
port as a `wire` net*, so re-declaring those same names as `wire` in the body
is a second declaration of the same symbol:

```verilog
// WRONG — direction in ANSI header, then wire re-declared in body
module generic_sr_nonoverlap #(
    parameter real tnov = 1
) (
    input  clk,
    output phi1,
    output phi2
);
    wire clk, phi1, phi2;   // [Error] Symbol phi1 already defined ...
    wire clk_b;
```

This is **specifically about re-declaring the net type `wire`.** Attaching a
*discipline* to a header-directioned port in the body is fine and is the normal
Verilog-AMS idiom — e.g. `generic_switch` does `inout p, n;` in the header and
`electrical p, n;` in the body without error, because `electrical` associates a
discipline rather than redeclaring a net. The clash only happens with a
duplicate **net-type** (`wire`) declaration.

## Fix — declare each port's direction + net type in exactly ONE place
Two forms work; pick by whether you need the port net in the body.

**A. All-in-header (ANSI), when you never touch the port net again in the body:**
```verilog
) (
    input  wire clk,
    output wire phi1,
    output wire phi2
);
```
(this is the `input wire ctrl` form in `generic_switch` — one declaration, no
body redeclaration.)

**B. Non-ANSI (Verilog-1995) port style — the portable choice when the body
needs port/internal nets (e.g. an internal `clk_b`), or you just prefer
grouping the port declarations in the body:** bare names in the `( ... )` list,
then one combined `direction net-type;` statement per port in the body:
```verilog
module generic_sr_nonoverlap #(
    parameter real tnov = 1      // non-overlap dead time [s]; must be > 0
) (
    clk,   // reference clock (digital wire)
    phi1,  // phase 1
    phi2   // phase 2
);
    input  wire clk;
    output wire phi1;
    output wire phi2;
    wire clk_b;                  // internal net — no conflict now
```

**Never** put the direction in the ANSI header and then re-declare the port as
`wire` in the body (the WRONG example above). That is the one combination that
triggers the error.

## Scope note
This is orthogonal to the **parameter** ANSI-header convention in
`parameters.md`: the `#( ... )` *parameter* port list stays ANSI regardless of
which port style you choose above. Form B keeps the ANSI `#( ... )` parameter
header and only moves the *signal* ports to Verilog-1995 style — the two lists
are independent.

## Fast check
- Any port declared with a direction in the ANSI header **and** re-declared as
  `wire` in the body? Remove one — that's the "already defined" error.
- Module body needs an internal `wire` or wants to reference a port net? Use
  form B (bare names in `( ... )`, `input wire ...;` in the body), not a
  header direction plus a body `wire` redeclaration.

## 2026-07-06 — ADD — first stated from `generic_sr_nonoverlap`
A non-overlapping-clock generator written with `input clk, output phi1, output
phi2` in the ANSI header plus `wire clk, phi1, phi2;` in the body failed
Symphony elaboration with "Symbol phi2 is already defined and cannot be
redefined as net" on all three ports. Switched to non-ANSI port style (form B):
bare `clk, phi1, phi2` in the port list, `input wire clk; output wire phi1;
output wire phi2;` in the body. Compiles. Recorded here as the reference
pattern for any module whose body needs to declare or reference its `wire`
ports.
