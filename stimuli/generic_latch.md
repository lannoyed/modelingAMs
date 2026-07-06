# Stimulus Plan — `generic_latch`

Written plan only — no testbench, no `.do` scripts, no driver module. Sequences,
corners, and what each is meant to expose. All ports are **digital by nature**;
any analog consumer converts `q`/`qn` through Symphony's automatic D2A (and
smooths at its own point of use), so nothing here drives an electrical node.

## Ports to drive

| Port | Kind | Not supplied by the model |
|---|---|---|
| `s`, `r` | digital `wire` | edge generation — the model reacts to the levels it's handed, it generates none |
| `q`, `qn` | digital `wire` (outputs) | observe only; `qn` is always the exact complement of `q` |

## Core sequences

1. **Set / reset / hold cycle** — the defining test. From a known start, pulse
   `s=1` (then back to 0), observe `q`→1 / `qn`→0 and confirm it **stays** high
   through the following `s=r=0` interval; then pulse `r=1`, observe `q`→0 /
   `qn`→1 and confirm it stays. Exposes: set, reset, and — critically — that
   `s=r=0` **holds** (the memory), rather than defaulting the output.

2. **Hold across a long idle** — after a set or reset, leave `s=r=0` for a long
   interval with no input activity. Exposes: the state is genuinely latched, not
   quietly decaying or re-defaulting; `q` is unchanged at the end of the idle.

3. **Illegal input `S=R=1`, all three `setdom` policies** — assert `s=r=1`
   simultaneously and hold it, once per `setdom` value. Exposes the Strategy
   selection:
   - `setdom=1` (set-dominant): `q`→1 while both are high.
   - `setdom=0` (reset-dominant): `q`→0 while both are high.
   - `setdom=-1` (hold): `q` keeps whatever it was before both went high.
   Also drive `s=r=1` → `s=r=0` (both released together) and note that the
   *last resolved* state persists (no glitch to an undefined level).

4. **Power-up state** — start the simulation with `s=r=0` from `t=0` and read
   `q` before any input edge, once with `qinit=0` and once with `qinit=1`.
   Exposes: the t=0 state is defined by `qinit` (0→`q` low, nonzero→`q` high),
   not left as `x`, so downstream logic never sees an unknown at start.

5. **x/z on an input** — drive `s` (or `r`) to `x`/`z`, or leave it undriven
   behind a connect boundary that resolves to `x`, mid-sequence while the other
   input is 0. Exposes: the `=== 1` case-equality reads the unresolved input as
   "not asserted", so the latch **holds** rather than spuriously setting or
   resetting — the safe failure mode for a memory element.

6. **Bad `setdom` override** — instantiate with `setdom` set to anything outside
   `{1,0,-1}` (e.g. `2`). Exposes: the `initial` guard's `$error` fires once at
   `t=0` with the offending value and instance path, halting the run rather than
   silently picking a policy.

## Corners / parameter settings to exercise

| Parameter | Corner values | Why |
|---|---|---|
| `setdom` | `1`, `0`, `-1` | the three illegal-input policies — sequence 3 |
| `qinit` | `0`, `1` | defined power-up either way — sequence 4 |
| `s`, `r` | clean 0/1 edges, near-simultaneous edges, and `x`/`z` | exercise set/reset/hold, the illegal state, and the unresolved-input hold path |

## Translation notes (plain-English, next to the relevant behavior)

- **Hold (`s=r=0`, sequences 1–2):** "this is the whole point of a latch — it
  remembers." No input, no change; the last set/reset sticks.
- **`setdom` (sequence 3):** "who wins when someone asserts set and reset at the
  same time." Set-dominant, reset-dominant, or 'don't move' — a policy choice,
  not a physical accident, so a design can pick the safe one for its context.
- **`qinit` (sequence 4):** "what the bit is at power-on." A real latch is a
  coin-flip at power-up; this pins it to a known value so a simulation starts
  from a defined state instead of propagating `x`.
- **x/z hold (sequence 5):** "what happens if the driving logic hasn't decided
  yet." The latch keeps its value — for a memory element, remembering is the
  right thing to do when the inputs are ambiguous.
