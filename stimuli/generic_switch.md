# Stimulus Plan — `generic_switch`

Written plan only — no testbench, no `.do` scripts, no driver module. Sequences,
corners, and what each is meant to expose.

## Ports to drive

| Port | Kind | Not supplied by the model |
|---|---|---|
| `p`, `n` | electrical (conservative) | source/load impedance, source or sink itself |
| `ctrl` | digital `wire` | edge generation — the model only smooths the edge it's handed, it doesn't generate one |

## Core sequences

1. **DC on / DC off** — hold `ctrl` at `1` (resp. `0`) and sweep a DC or slow
   ramp voltage across `p`/`n` at fixed source impedance. Exposes: `ron`
   (measure `I = V/ron` in the on state) and `roff` leakage (measure the
   residual `I` in the off state) independently, with no commutation
   transient in the picture.

2. **Single toggle, both edges** — step `ctrl` 0→1 then, after settling,
   1→0, with the surrounding circuit's `p`/`n` held at a fixed bias (e.g. a
   resistive divider). Exposes: the `trise`/`tfall`-shaped conductance
   transition itself — confirm the current step from `goff·V` to `gon·V` (or
   back) tracks `transition()`'s smoothed edge, not an instantaneous jump,
   and that turn-on is governed by `trise` while turn-off is governed by
   `tfall` (not swapped).

3. **Periodic toggle at target switching frequency** — square-wave `ctrl` at
   the frequency this instance will actually see in its parent circuit (e.g.
   `sc_tripler`'s `fsw`), with `p`/`n` in a representative loaded context
   (a cap or resistor, not open/floating). Exposes: whether `trise`/`tfall`
   are small enough relative to the switching period that the smoothed edge
   doesn't itself become a bottleneck on conduction time — a `trise`/`tfall`
   comparable to the on-time is a modeling-realism red flag worth catching
   here before it's buried inside a larger converter.

4. **x/z on `ctrl`** — drive `ctrl` to `x` (or leave it undriven behind a
   connect-module boundary that can resolve to `x`) at some point in a
   toggle sequence. Exposes: the `ctrl === 1` case-equality falls through to
   `goff` (the switch's failure mode is open, not shorted) on anything other
   than a clean `1`.

5. **Bad-parameter override** — instantiate with `ron`, `roff`, `trise`, or
   `tfall` overridden to `0` or a negative value, one at a time. Exposes: the
   `analog initial` guard's `$display` warning fires exactly once at `t=0`
   with the offending value and the clamp target, and the run continues on
   the clamped default rather than diverging or failing elaboration.

## Corners / parameter settings to exercise

| Parameter | Corner values | Why |
|---|---|---|
| `ron` | toward 0, and an order of magnitude above default | conduction-loss sensitivity; toward-0 isolates whatever's downstream of this switch from its own resistance |
| `roff` | default (~100 MOhm), and a much lower "leaky" value (~1 MOhm) | confirms off-state leakage is visible and scales as `1/roff`, not accidentally floored elsewhere |
| `trise`, `tfall` | fast (~0.1 ns) vs. slow, comparable to the parent circuit's switching period | edge speed should not change steady-state on/off current, only transition shape/convergence — see sequence 3 |
| `ctrl` | clean 0/1, and `x` | sequence 4 |

## Translation notes (plain-English, next to the relevant sequence)

- **`ron`/`roff` (sequence 1):** "how good a wire it is when on, how good an
  open it is when off." Both are finite by construction — a real switch is
  never a perfect short or a perfect open, and this model never divides by
  zero because of it.
- **`trise`/`tfall` (sequences 2–3):** "how fast the switch actually
  commutates, in conductance terms." This is a smoothing time for the solver
  as much as a physical edge time — too slow relative to the switching period
  and you're modeling a switch that never fully turns on.
- **`ctrl` = x (sequence 4):** "what happens if the digital side hasn't
  decided yet." The switch defaults open, which is the safer failure mode for
  most circuits than defaulting closed.
