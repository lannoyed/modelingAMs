# Pattern: Data Converters & PLLs (mixed-signal: sampling + quantization)

## When to use
Blocks crossing the analog/digital boundary: ADC, DAC, PLL/DLL. Core challenge is
sampling instants, quantization, and connect-rule boundaries.

## Design-pattern hooks
- **Strategy** for the quantizer: swappable rounding/dithering via a parameter so one
  ADC shell tests ideal vs. non-ideal quantization.
- **Factory** for corner/config selection (resolution, Vref) so one module family
  covers a spec sweep without duplication.

## Vetted skeleton — ideal N-bit sampling ADC
```verilog
`include "disciplines.vams"
`include "constants.vams"

module adc_ideal #(parameter integer nbits = 12) (vin, vref, clk, dout);
  // Why: golden reference for a real ADC. Ideal sample-and-quantize; validate the
  // downstream logic before adding INL/DNL/noise non-idealities.
  input  vin, vref, clk;
  output [nbits-1:0] dout;
  electrical vin, vref;
  logic clk;
  logic [nbits-1:0] dout;

  parameter real tap = 0.0 from [0:inf);          // aperture delay [s]

  integer code, levels;
  real    lsb, vsample;

  analog begin
    levels = (1 << nbits);
    lsb    = V(vref) / levels;
  end

  // sample on clk edge — event domain, keep out of analog block
  always @(posedge clk) begin
    vsample = V(vin);                             // analog potential at the edge
    code    = vsample / lsb;                      // truncate = ideal quantize
    if (code < 0)        code = 0;
    if (code > levels-1) code = levels-1;
    dout <= #(tap) code;
  end
endmodule
```

## PLL note
Model phase, not the carrier, for speed: VCO phase via `Phase <+ idt(kvco*V(vctrl))`,
PFD/CP as charge events, loop filter as `laplace_nd`. Full-carrier PLLs converge
slowly — model phase-domain for strategy work, full-carrier only if unavoidable.

## Stimulus plan (what to drive — report, not a driver module)
- **Full-scale ramp:** slow input ramp from 0 to Vref to exercise every code — the
  sequence that exposes the transfer curve and any code gaps.
- **Clock sequence:** a periodic clock at the target sample rate; note the aperture
  `tap` setting so the intended sampling instant is unambiguous.
- **Corners:** `nbits` at min/typ/max resolution; Vref at supply extremes (Factory-
  style config selection) to show the LSB scaling.
- **Boundary note:** `dout` is `logic`; state the l2e/e2l connectrule feeding
  downstream so the plan is self-contained.
- Translation: "ENOB = effective bits after real noise/distortion; 12-bit ideal but
  9.5 ENOB means noise eats ~2.5 bits of resolution."

## Boundary caution
`V()` reads in `always` blocks are sampled values, not continuous — never `<+`
contribute from an `always` block. See `pitfalls/connect_rules.md`.

## 2026-07-01 — ADD — switched-capacitor / charge-pump converters
A distinct sub-class from the sampling ADC above: SC converters (voltage
multipliers/dividers, charge pumps) move charge between flying caps on
non-overlapping clock phases rather than sampling a continuous input.

- **Model the physical netlist, not an algebraic transfer function.** Build
  the actual switch+cap topology as conservative `electrical` nodes. An
  averaged model (`Vout = N*Vin - Iout*R_out`, with `R_out` derived from SSL/
  FSL formulas) is a second, independently-maintained expression of the same
  physics — it drifts from the real netlist the moment cap sizes or switch
  Ron change without the formula being re-derived by hand. Let output
  impedance and its SSL/FSL corner **emerge** from a transient `fsw`x`Iload`
  sweep in the STIMULI stage instead.
- **Reusable switch sub-module, not eight copy-pasted conductances.** One
  `sc_switch`-style module (electrical `p`,`n`; digital `wire ctrl`; ANSI
  parameters `ron`, `roff`) instantiated once per phase switch. Strategy
  pattern on `ron` (0 isolates the SSL asymptote in a sweep; raising it brings
  in FSL — same equation, no branching). Factory-style tier selection: if the
  topology has N distinct voltage-stress tiers (a series-stacking topology
  usually does — each node sits at a different multiple of Vin), expose one
  `ron_tier{1..N}` parameter per tier at the top level rather than one
  parameter per switch instance.
- **Clock phases are digital `wire` ports, driven entirely externally** — no
  internal non-overlap/dead-time generator in the model (separation of
  concerns: a model contains no drive source). This also keeps a deliberate
  phase-overlap (shoot-through) corner reachable from the STIMULI stage
  instead of architected away.
- **Reservoir/output caps and the load are out of scope of the converter
  model.** They belong on the stimulus/testbench side of the output port —
  don't add a "convenience" output cap just because the topology usually has
  one nearby in a real board.
- Smoothing and connect-module conventions: see `pitfalls/connect_rules.md`
  (2026-07-01 revision) and `pitfalls/convergence.md` — `transition()` is
  called directly on the digital `wire` control signal inside the switch's
  own analog block, no hand-declared connect module. Parameter conventions
  (ANSI headers, `localparam` for derived constants, the `<MODULE_NAME>_PARAM.vams`
  file) are in `pitfalls/parameters.md`.
