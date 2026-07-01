# Pattern: Sensors / Transducers (physical-domain -> electrical)

## When to use
Blocks mapping a non-electrical quantity (temperature, pressure, light, acceleration)
to an electrical output. Job: documented transfer function + realistic dynamics
(bandwidth, noise, nonlinearity).

## Structure (separation of concerns)
Three composed layers:
1. **Physical input** — signal-flow discipline (`voltage`) carrying the stimulus.
2. **Transducer core** — transfer function + sensitivity + offset + nonlinearity.
3. **Electrical front-end** — output impedance, bandwidth pole, noise.

## Vetted skeleton — generic linear-ish sensor
```verilog
`include "disciplines.vams"
`include "constants.vams"

module sensor_lin(phys, out, gnd);
  // Why: parameterized transducer. Sensitivity/offset/BW explicit so the same shell
  // models a thermistor, pressure cell, or photodiode by re-param.
  input  phys;              // physical stimulus, signal-flow
  inout  out, gnd;          // electrical output
  voltage phys;
  electrical out, gnd;

  parameter real sens   = 10m  from (0:inf);      // sensitivity [V per phys-unit]
  parameter real offset = 0.0  from [-1:1];       // output offset [V]
  parameter real nl2    = 0.0  from [-1:1];       // 2nd-order nonlinearity coeff
  parameter real fbw    = 1e3  from (0:inf);      // output -3dB bandwidth [Hz]
  parameter real vn     = 10u  from [0:inf);      // input-referred noise [V/rtHz]

  real x, vraw, wp;

  analog begin
    x    = V(phys);
    vraw = offset + sens*x + nl2*sens*x*x;        // transfer + nonlinearity
    wp   = `M_TWO_PI * fbw;

    V(out, gnd) <+ laplace_nd(vraw, {1}, {1, 1/wp});   // bandwidth-limited output
    V(out, gnd) <+ white_noise(vn*vn, "sensor_noise");
  end
endmodule
```

## Stimulus plan (what to drive — report, not a driver module)
- **Physical sweep:** the physical input swept across its full measurement span to
  expose the transfer curve — slope should read `sens`, intercept `offset`.
- **Nonlinearity probe:** drive toward the span extremes where `nl2` bows the curve
  most, so the second-order term is visible rather than buried.
- **Dynamic step:** a step in the physical input to exercise the bandwidth pole `fbw`
  (how fast the output tracks a sudden change).
- **Corners:** `sens`, `offset`, `fbw` at their range limits.
- Translation: "Sensitivity = millivolts per unit measured; low sensitivity => the ADC
  after it needs more gain."

## Extensions
- Self-heating: add a `thermal` node, couple dissipated power back.
- Ratiometric: scale output by `V(vref)` so supply variation cancels.
