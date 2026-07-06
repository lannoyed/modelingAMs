# Stimulus Plan — `generic_sr_nonoverlap`

Written plan only — no testbench, no `.do` scripts, no driver module. Sequences,
corners, and what each is meant to expose.

## Ports to drive

| Port | Kind | Not supplied by the model |
|---|---|---|
| `clk` | digital `wire` (in) | the clock itself — drive from `generic_clkgen` or a plain square wave |
| `phi1`, `phi2` | digital `wire` (out) | any edge shaping — the consumer applies `transition()` at the analog boundary |

## Core sequences

1. **Periodic clock, measure the dead time** — drive `clk` with a steady
   square wave (from `generic_clkgen`) for many cycles. Exposes: the core
   invariant — `phi1` high while `clk` is low, `phi2` high while `clk` is high,
   and a non-overlap window of ~`tnov` on **every** transition where both
   phases are low. Confirm the forbidden "both high" state never appears.

2. **Break-before-make on each edge** — zoom on a single `clk` rising edge, then
   a falling edge. Exposes: the falling phase reaches `0` first and the rising
   phase only asserts after that `0` propagates through `tnov` — i.e. the dead
   time comes from the feedback delay, symmetric on both edges, not from an
   input skew.

3. **`tnov` approaching a half period** — drive a clock whose high/low time is
   only a small multiple of `tnov`, then push `tnov` up toward that half period.
   Exposes: the inertial `#(tnov)` delay progressively eats the usable phase
   width, and near/above a half period the pulse is swallowed — the realism red
   flag that `tnov` must stay comfortably below the clock's high/low time.

4. **`clk = x/z` at startup** — leave `clk` unresolved (or `x`) before the first
   valid edge. Exposes: `phi1`/`phi2` sit at `x` until `clk` resolves; once a
   clean clock arrives the latch settles into the correct alternating pattern.
   Downstream (`generic_switch`) treats a non-`1` phase as "off", so an
   unresolved startup fails safe (both switch sets open), not shorted.

5. **Overlap-fault check for a consumer** — chain into `sc_tripler_top` and
   compare against that model's deliberately-reachable shoot-through corner
   (driving overlapping phi1/phi2 directly). Exposes: this generator's whole
   purpose — it removes the overlap that the raw stimulus corner leaves in, so
   the flying-cap charge paths never short when phases come from here.

6. **Bad-parameter override** — instantiate with `tnov <= 0`. Exposes: the
   `initial` guard's `$error` fires at `t = 0` with the offending value and
   instance path (`%m`) and halts the run.

## Corners / parameter settings to exercise

| Parameter | Corner values | Why |
|---|---|---|
| `tnov` | the repo `` `timescale 1ns/10ps`` precision floor (~10 ps), a realistic value (~1 ns), and up toward a half period | dead-time width should scale with `tnov`; below ~10 ps the delay rounds toward zero (no dead time — a real floor from the fixed timescale), the large corner exposes pulse swallowing (sequence 3) |
| `clk` freq | matched so `tnov` is a small fraction of the half period, and one where it is not | ties the `tnov` corner to a concrete clock; confirms non-overlap is a fixed time, not a fixed fraction of the period |
| `clk` | clean square wave, and `x` at startup | sequences 1 and 4 |

## Translation notes (plain-English, next to the relevant sequence)

- **`tnov` (sequences 1–3):** "the guaranteed gap where both phases are off."
  Bigger `tnov` = safer against shoot-through but less time each phase is
  actually usable — the classic dead-time tradeoff, here set by one delay.
- **break-before-make (sequence 2):** "a phase can't turn on until the other
  has finished turning off." That ordering, not just the timing, is what
  protects the switched-capacitor charge paths downstream.
- **digital generation:** "the phases live in the digital simulator; the analog
  engine only stops at each edge." Same correct-for-AMS choice as
  `generic_clkgen` — no analog block, the consumer owns the edge via
  `transition()`.
