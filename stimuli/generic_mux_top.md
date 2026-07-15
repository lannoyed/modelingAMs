# Stimulus Plan — `generic_mux_top`

Written plan only — no testbench, no `.do` scripts, no driver module. Sequences,
corners, and what each is meant to expose.

## Ports to drive

| Port | Kind | Not supplied by the model |
|---|---|---|
| `in[0:num_inputs-1]` | electrical (conservative), `num_inputs` independent channels | source/load impedance per channel, the source signals themselves |
| `out` | electrical (conservative) | load impedance, sink |
| `sel` | digital `wire [width-1:0]`, binary-coded | select-code generation/timing itself |
| `en` | digital `wire` | enable waveform itself |

## Core sequences

1. **Static channel scan** — for each valid `sel` code `0..num_inputs-1` in
   turn, hold `en=1` and that code for long enough to settle, with each
   `in[i]` driven to a distinct DC level (or a per-channel ID tone).
   Exposes: the correct channel reaches `out` at every code, `ron`
   attenuation/offset through the selected switch, and that every
   non-selected channel's leakage into `out` (via its `generic_switch`'s
   `roff`) stays negligible relative to the selected path.

2. **Sequential channel-to-channel toggle** — step `sel` through consecutive
   codes at a fixed cadence, `en=1` throughout, with distinct DC or slow-ramp
   levels on each `in[i]`. Exposes: the break-before-make behavior itself —
   confirm the outgoing channel's `generic_switch` conductance has decayed
   (over `tfall`) before the incoming one starts ramping (after the `tbbm`
   dead time), i.e. `out` never briefly sees two channels shorted together
   through their series Ron.

3. **`tbbm` too small (fault corner)** — repeat sequence 2 with `tbbm` set to
   ~0 or comparable to/smaller than `trise`/`tfall`. Exposes: the
   partial-overlap short flagged in the model's Limitations — with two input
   channels at different DC levels, watch for a transient current spike
   between them through `out` during the switch. Confirms the corner is real
   and that `tbbm >> max(trise, tfall)` is needed to avoid it, not just a
   theoretical concern.

4. **Out-of-range `sel`** — with `num_inputs` not a power of two (e.g. 3 or
   5), drive `sel` to a code `>= num_inputs`. Exposes: the decode's defined
   safe-idle behavior — all channels off, `out` floating to whatever the
   aggregate `roff` network leaves it at, rather than an undefined or
   accidentally-still-selected channel.

5. **`en` toggling, both directions** — with `sel` fixed on a valid code,
   drop `en` to 0 mid-selection, then reassert it. Exposes: `en=0` behaves
   exactly like the break path (immediate, no `tbbm` delay — nothing to
   "make" toward) and re-enabling behaves like a fresh make (delayed by
   `tbbm`), i.e. enable and select-driven switching share the same
   break-before-make treatment.

6. **`en` or `sel` at x/z** — drive `en` to `x`, and separately drive one or
   more `sel` bits to `x`, mid-sequence. Exposes: `en === 1'b1` and the
   `sel < num_inputs` comparison both fail safe on an unresolved bus — the
   decode falls to all-off rather than guessing a channel, matching
   `generic_switch`'s own `ctrl === 1` failure mode.

7. **Bad-parameter override** — instantiate with `num_inputs < 2`, or any of
   `ron`/`roff`/`trise`/`tfall` at 0 or negative, or `tbbm < 0`. Exposes: the
   `from (...)` guards in `generic_mux_top_PARAM.vams` reject elaboration
   with a clear diagnostic rather than sizing a zero/negative-width channel
   array or letting a bad switch parameter propagate silently into every
   instantiated `generic_switch`.

## Corners / parameter settings to exercise

| Parameter | Corner values | Why |
|---|---|---|
| `num_inputs` | 2 (minimum), a power of two (4, 8), and a non-power-of-two (3, 5) | exercises the smallest valid array, typical sizes, and the reachable-out-of-range-code path (sequence 4) |
| `tbbm` | 0, a few × `trise`/`tfall` (nominal), and comparable to/below `trise`/`tfall` (fault) | sequences 2 and 3 — the headline safety parameter of this model |
| `ron` | default, and an order of magnitude above/below | per-channel insertion loss/attenuation sensitivity, same as `generic_switch`'s own sweep |
| `roff` | default (~100 MOhm), and a "leaky" value (~1 MOhm) | confirms cross-channel leakage into `out` is visible and traceable to `roff`, not floored elsewhere |
| `sel` | every valid code, plus one out-of-range code if `num_inputs` isn't a power of two, plus `x` | sequences 1, 4, 6 |
| `en` | steady 1, toggled mid-sequence, `x` | sequences 1, 5, 6 |

## Translation notes (plain-English, next to the relevant sequence)

- **Break-before-make / `tbbm` (sequences 2–3):** "the gap that keeps two
  input channels from briefly touching each other through the mux." Too
  small and switching between channels can momentarily short whatever's
  connected to them together — the same shoot-through concern this repo
  already documents for SC-converter clock phases, just applied to a mux's
  own internal channel decode instead of an external two-phase clock.
- **Out-of-range `sel` (sequence 4):** "what the mux does when you ask it for
  a channel that doesn't exist." It goes to a defined all-off state rather
  than picking something arbitrary — the same "fail open, not fail
  ambiguous" philosophy as `generic_switch`'s `ctrl` handling.
- **`roff` leakage (sequence 1):** "how much of the channels you didn't pick
  still sneak through." Never exactly zero for a real switch — this model
  keeps that leakage visible and parametric instead of idealizing it away.
