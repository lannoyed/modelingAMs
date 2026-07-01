# Pattern: Op-amps / LDOs / Filters (conservative `electrical`)

## When to use
Blocks that load their nodes (draw/source current) and obey KCL/KVL. Modeled with
`electrical` discipline, `V()`/`I()` access, `<+` contributions.

## Spec template
- Ports: inp, inn, out, vdd, vss (all `electrical`).
- Params: gain [V/V], gbw [Hz], rout [Ohm], vos [V], slew [V/s], vmax/vmin (rails).
  Every one range-guarded.
- Equations: single-pole rolloff via `laplace_nd`; slew via `slew()`; output clamp via
  smooth tanh limiter, NOT a hard `if`.

## Vetted skeleton
```verilog
`include "disciplines.vams"
`include "constants.vams"

module opamp1p(inp, inn, out, vdd, vss);
  // Single-pole op-amp macromodel. Why: fastest-converging small-signal model that
  // still captures GBW, slew, and rail clamp for closed-loop AC/tran.
  inout inp, inn, out, vdd, vss;
  electrical inp, inn, out, vdd, vss;

  parameter real gain  = 1.0e5 from (0:inf);      // open-loop DC gain [V/V]
  parameter real gbw   = 10e6  from (0:inf);      // gain-bandwidth [Hz]
  parameter real rout  = 100.0 from (0:inf);      // output resistance [Ohm]
  parameter real vos   = 0.0   from [-10m:10m];   // input offset [V]
  parameter real slewr = 10e6  from (0:inf);      // slew rate [V/s]

  real vin, vpole, vclamp, vhi, vlo, wp;

  analog begin
    wp  = gbw / gain;                             // dominant pole [rad/s] = GBW/A0
    vhi = V(vdd) - 0.2;  vlo = V(vss) + 0.2;      // rail headroom
    vin = V(inp, inn) + vos;

    // dominant pole: first-order lag, differentiable -> Newton-friendly
    vpole = slew( laplace_nd(vin, {gain}, {1, 1/wp}), slewr );

    // smooth rail clamp (no hard if -> avoids convergence kinks)
    vclamp = vlo + (vhi - vlo)*(0.5 + 0.5*tanh(4.0*(vpole-(vhi+vlo)/2)/(vhi-vlo)));

    V(out, vss) <+ vclamp - V(vss);
    I(out)      <+ (V(out) - vclamp) / rout;      // rout sets output drive
  end
endmodule
```

## Stimulus plan (what to drive — report, not a driver module)
- **Small-signal sweep:** differential input swept across its linear range to expose DC
  gain and the onset of clamping. Corners: min/typ/max `gain`, `vos` extremes.
- **Large step:** input step spanning most of the rail range to exercise `slewr` — the
  interesting behavior is the slope limit, so size the step so slewing dominates.
- **Rail approach:** drive the input so the output is pushed toward each rail to
  confirm the smooth clamp engages without a kink.
- Translation: "GBW = how fast the amp reacts; low GBW => sluggish closed-loop response
  and possible ringing." Note this next to whichever sequence probes speed.

## Extensions
- LDO: pass-device `I(out) <+ gm*V(err)` + load-reg loop + PSRR pole.
- Filters: cascade `laplace_nd` biquads; each biquad its own instance (composition).
