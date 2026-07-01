# Stimulus Plan — `sc_tripler`

Written plan only — no testbench, no `.do` scripts, no driver module. Sequences,
corners, and what each is meant to expose.

## Ports to drive

| Port | Kind | Not supplied by the model |
|---|---|---|
| `vin` | DC or slow ramp | source impedance, source itself |
| `phi1`, `phi2` | digital clock phases (`wire`) | dead-time/non-overlap timing, or deliberate overlap fault |
| `vout` load | current sink at `vout`, plus a reservoir cap if desired | load itself, output cap — both out of scope of this model |

`phi1`/`phi2` are independent digital ports (see STRATEGY) — the stimulus owns
all clock generation, including getting the dead-time right in the nominal
case. The output reservoir cap is likewise not part of this model — add it on
the stimulus/testbench side of `vout` if ripple filtering is needed.

## Core sequences

1. **Nominal periodic phase drive** — `phi1`/`phi2` as complementary square waves
   at the target `fsw`, each ~45% duty, separated by an explicit dead-time gap
   sized several multiples of `trise`/`tfall` (e.g. 5–10×) so neither phase is high
   during the other's transition. Run for enough cycles (tens to hundreds,
   depending on `c1`/`c2`/`ron`) to reach periodic steady state on `vout`.
   Exposes: nominal 3·Vin conversion, ripple shape, settling time.

2. **Vin DC sweep** — hold phases at nominal `fsw`/dead-time, sweep `vin` DC
   level across its intended operating range at fixed `Iload`.
   Exposes: linearity of `Vout ≈ 3·Vin − Iload·R_out` — confirms the 3:1 ratio
   holds across the input range and isn't corrupted by clamping/saturation
   effects that shouldn't exist in this ideal-switch model.

3. **fsw × Iload sweep (the SSL/FSL corner)** — for each `fsw` in a log-spaced
   sweep (e.g. a decade below to a decade above the cap/Ron corner frequency)
   and each `Iload` in a few steps, run to periodic steady state and record
   the droop `(3·Vin − Vout)/Iload`. Plot the resulting `R_out` vs. `fsw`.
   Exposes: the SSL asymptote (rising `R_out` as `fsw` drops, slope ∝ `1/fsw`)
   flattening into the FSL asymptote (flat, set by `ron_tier*`) — this is the
   headline characterization curve for the whole converter and the reason the
   model was built as a physical netlist rather than an algebraic one: the
   corner falls out of this sweep instead of being asserted.

4. **Ron isolation runs** — repeat sequence 3 with `ron_tier1/2/3` swept toward
   0 (isolates SSL, no resistive floor) and then swept up an order of
   magnitude (pushes the FSL floor up, corner frequency shifts left).
   Exposes: that the two asymptotes in sequence 3 really do trace back to cap
   size/fsw and switch resistance respectively, not to some other model
   artifact.

5. **Dead-time / shoot-through fault corner** — deliberately overlap `phi1`
   and `phi2` (zero or negative dead-time) for a short window.
   Exposes: the shoot-through path the confirmed netlist explicitly flags —
   with both phases high, `vin` sees a low-impedance path to `gnd` through
   whichever switches are on tier-1 (`S1a/S1b/S2a/S2b`) simultaneously with
   tier-2/3 paths engaged. Confirm this shows up as a current spike, not a
   convergence failure (the smooth `transition()` edges inside `sc_switch`
   should keep Newton happy even in this fault state).

6. **Load step** — step `Iload` between two levels with phases running at
   fixed `fsw`. Exposes: transient recovery time of `vout`, sized by whatever
   reservoir cap the stimulus adds externally, and the loop-free (this
   converter has no feedback) open-loop droop.

## Corners / parameter settings to exercise

| Parameter | Corner values | Why |
|---|---|---|
| `c1`, `c2` | min/typ/max flying-cap size | SSL term scales as `1/C`; shows in sequence 3 |
| `ron_tier1/2/3` | equal (default), then tier3 ≫ tier1 | matches real voltage-rating/area tradeoff; check FSL floor shifts as expected |
| `trise`/`tfall` | fast (~0.1 ns) vs. slow (~10 ns) | edge time should not change steady-state `Vout`, only transition smoothness/convergence |
| dead-time | nominal (several × `trise`/`tfall`), zero/negative (fault) | sequence 5 |
| `fsw` | spanning the SSL/FSL corner (sequence 3) | the headline characterization |
| `Iload` | no load, typical, near-dropout | droop and recovery behavior |

## Translation notes (plain-English, next to the relevant sequence)

- **R_out (SSL/FSL corner, sequence 3):** "how much the output sags per amp of
  load, and why." At low switching frequency, the caps don't get to fully
  transfer charge each cycle, so the converter looks like a big resistor set
  by `1/(C·fsw)` — switch faster or use bigger caps to shrink it. At high
  frequency, that term vanishes and what's left is just the switches' own
  resistance, referred through however many times each cap's charge moves per
  cycle — better switches are the only lever left there.
- **Switch-stress tiers (sequences 1, 5):** "which switches need to survive
  higher voltage." Tier-3 (`S4b`) sits across the full 3·Vin swing every
  discharge phase; a real implementation needs a correspondingly rated device
  and gate-drive level-shift there, not just a higher-current one.
- **Dead-time (sequence 5):** "the gap that keeps both halves of the circuit
  from being connected to each other at once." Too little (or negative) and
  you get a brief low-impedance shoot-through path instead of clean charge
  transfer.
