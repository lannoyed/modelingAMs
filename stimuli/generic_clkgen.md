# Stimulus Plan — `generic_clkgen`

Written plan only — no testbench, no `.do` scripts, no driver module. Sequences,
corners, and what each is meant to expose.

## Ports to drive

| Port | Kind | Not supplied by the model |
|---|---|---|
| `en` | digital `wire` (in) | the enable waveform itself — the model only reacts to the edges it is handed |
| `clk` | digital `reg`/wire (out) | any edge shaping — the consumer applies `transition()` at the analog boundary, not this model |

## Core sequences

1. **Steady enable, measure period/duty** — hold `en = 1` and let the clock
   free-run for many cycles. Exposes: that the period equals `tperiod` (ns) and
   the high-time equals `duty*tperiod` to within the `` `timescale`` precision
   (1 ps). Confirms the derived `thigh`/`tlow` split and that edges land on
   exact, drift-free times (period is constant cycle-to-cycle, not creeping).

2. **Enable gating, both edges** — start with `en = 0`, assert `en = 1` for a
   burst of cycles, then de-assert. Exposes: the clock parks at a clean `0`
   while disabled, starts a full cycle on enable, and finishes the current
   period before parking on disable (never a truncated/runt pulse). Note where
   the enable edge falls relative to a clock edge to make the up-to-one-period
   disable latency unambiguous.

3. **`en = x/z`** — drive `en` to `x` (or leave it undriven behind a
   connect-module boundary that resolves to `x`) mid-burst. Exposes: the
   `en === 1` case-equality parks `clk` low on anything other than a clean `1`
   — the safe idle failure mode, matching `generic_switch`'s `ctrl` handling.

4. **Feed a downstream consumer** — route `clk` into `generic_sr_nonoverlap`
   (and on into `sc_tripler_top`'s switches). Exposes: that the digital `clk`
   crosses into the analog side purely through the consumer's `transition()` —
   this model contributes nothing analog, so the analog solver only sees a
   breakpoint per edge (the whole point of generating the clock digitally).

5. **Bad-parameter override** — instantiate with `tperiod <= 0`, or `duty` at
   `0`, `1`, or outside `(0:1)`, one at a time. Exposes: the `initial` guard's
   `$error` fires at `t = 0` with the offending value and instance path (`%m`)
   and halts the run, rather than emitting a zero/negative-width or degenerate
   clock.

## Corners / parameter settings to exercise

| Parameter | Corner values | Why |
|---|---|---|
| `tperiod` | the parent circuit's real switching period (ns), plus ~decade above/below | period should track `tperiod`; the short end checks that the 1 ps precision floor is still a small fraction of the half period (~0.1% for a 1 ns period), the long end that the event count stays sane |
| `duty` | 0.5, and a deliberately asymmetric value (e.g. 0.3) | confirms `thigh`/`tlow` split independently and that a non-50% clock is available for a downstream generator that needs it |
| `tperiod` near the precision floor | a period whose half approaches ~1 ps (i.e. `tperiod` ~ 0.002 ns) | exposes the fixed `` `timescale 1ns/1ps`` (repo-wide) precision floor on edge placement — the point below which this generator can no longer resolve the intended timing |
| `en` | clean 0/1 burst, and `x` | sequences 2 and 3 |

## Translation notes (plain-English, next to the relevant sequence)

- **`tperiod`/`duty` (sequence 1):** "how long each tick is (in ns) and how long
  it stays high each tick." Both are exact by construction here — a behavioural
  timing source, so no jitter and no phase noise; add those only if the study
  needs them.
- **digital generation (sequence 4):** "the clock lives in the digital
  simulator, so the analog engine only stops at each edge instead of grinding
  through a fast oscillating node." This is the reason the model has no analog
  block at all — it is the correct-for-AMS choice, not a simplification.
- **`en = x` (sequence 3):** "what happens before the digital side has decided."
  The clock idles low, the safe default, rather than free-running on an
  ambiguous enable.
