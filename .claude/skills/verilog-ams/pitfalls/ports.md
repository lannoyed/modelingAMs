# Pitfall: Port declaration style (Symphony)

## The failure
Mixing an **ANSI-style directioned port header** with a **body net
declaration** for the same port makes Symphony/ADMS reject the module:

```verilog
module generic_sr_nonoverlap #( parameter real tnov = 1.0 ) (
    input  clk,                    // ANSI header: direction, no net type
    output phi1,
    output phi2
);
    wire clk, phi1, phi2;          // <-- re-declares the ports as nets
    wire clk_b;
```

```
[Error] Symbol phi2 is already defined and cannot be redefined as net
```

## Root cause (LRM-grounded, not a Symphony quirk)
A directioned port in the ANSI header (`input clk`) is a **complete** port
declaration: with no explicit net type it *implicitly* declares `clk` as a net
of the default net type (`wire`). The body `wire clk;` is then a **second net
declaration of the same symbol** — a duplicate, which is an error. Per
IEEE 1800/1364 §23.2.2.1, once a port is declared in the ANSI header list it
"shall not be declared again" in a body net/variable declaration. This is
ordinary Verilog, so it fires the same way in every conformant tool, not just
Symphony — but the message ("already defined... as net") is what you'll see
here.

The mirror-image mistake is the same class: an ANSI `output clk` re-declared as
`reg clk;` in the body ("already defined... cannot be redefined as reg").

## Discipline declarations are the legal exception — do NOT confuse them
A **discipline** declaration in the body for an ANSI directioned analog port is
required and legal — it is not a net-type redeclaration:

```verilog
) (
    inout p, n,          // ANSI header: direction only, no discipline
    input wire ctrl
);
    electrical p, n;     // LEGAL: supplies the discipline the header omitted
```

`electrical p, n;` completes the port by associating a discipline; it does not
declare a second net of a conflicting type. This is exactly what the working
`generic_switch`/`sc_tripler_top` electrical models do. The rule to remember:
**body `wire`/`reg` for an ANSI directioned port = duplicate = error; body
`electrical`/`<discipline>` for an ANSI directioned port = required = fine.**

## The two legal port styles — pick one per port, never straddle
**Non-ANSI (the repo convention for digital `wire`/`reg` ports).** Header lists
bare names (each carries its own comment cleanly); direction + net/var type are
declared once in the body:

```verilog
) (
    clk,   // reference clock (digital wire)
    phi1,  // phase 1: high while clk is low
    phi2   // phase 2: high while clk is high
);
    input  wire clk;
    output wire phi1;
    output wire phi2;
    wire clk_b;        // internal nets are ordinary body declarations
```

For a procedurally-driven output, combine direction + variable type in the body
(`output reg clk;`) — legal in non-ANSI style, and what makes an output an
`always`-driven `reg`.

**Full-ANSI (also legal; what `generic_latch` uses).** Put the net type *in the
header* and declare nothing in the body:

```verilog
) (
    input  wire s, r,
    output wire q, qn
);
    reg qout, qnout;   // internal only — never re-names a port
```

Both compile. The bug is only the **half-ANSI straddle**: direction-in-header
*without* a net type, *plus* a body `wire`/`reg` line for that same port.

## Fast check
- Any port whose direction is in the ANSI `( ... )` list: is there also a
  `wire`/`reg` declaration for that same name in the body? If so, delete one
  side — either move the net type up into the header (full-ANSI) or strip the
  direction out of the header down to a bare name (non-ANSI).
- Body `wire`/`reg` lines: do any of them repeat a port name, or only name
  genuine internal nets (`clk_b`, `qout`)? Only internal names belong there.
- Analog ports: the body `electrical <ports>;` line is a discipline
  declaration, not a redeclaration — keep it.

## 2026-07-06 — ADD — first stated from the digital clock-gen review
Reproduced on `generic_sr_nonoverlap` (`input clk; ... wire clk, phi1, phi2;`)
and the same class on `generic_clkgen` (`input en; ... wire en;` plus
`output clk; ... reg clk;`). Both fixed to the non-ANSI form above (bare names
in the header, `input wire`/`output reg` in the body). `generic_latch` already
used the full-ANSI net-typed header and needed no change; `generic_switch`/
`sc_tripler_top` were never affected — their body `electrical ...;` lines are
discipline declarations, the legal exception, not net redeclarations.
