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

3. **Illegal input `S=R=1`, all `sr11` policies** — assert `s=r=1`
   simultaneously and hold it, once per `sr11` value. Two things to observe
   every time: (a) a `$warning` fires on entry (the input is illegal
   regardless of which value it resolves to), and (b) the outputs take the
   selected value:
   - `sr11=2` **both-low** (`q=0, qn=0`) — the cross-coupled **NOR** behavior;
     confirm `qn` is *not* the complement of `q` here.
   - `sr11=3` **both-high** (`q=1, qn=1`) — the cross-coupled NAND behavior.
   - `sr11=1` set-dominant (`q=1, qn=0`); `sr11=0` reset-dominant (`q=0, qn=1`).
   - `sr11=4` hold — `q`/`qn` keep whatever they were before both went high.
   Then drive `s=r=1` → `s=r=0` (both released together) and note the forced
   value **persists** as an "undefined until re-driven" state — this
   behavioral model deliberately does *not* reproduce the NOR deassertion
   race, and the `$warning` already flagged that you're off the reliable path.

4. **Power-up state** — start the simulation with `s=r=0` from `t=0` and read
   `q` before any input edge, once with `qinit=0` and once with `qinit=1`.
   Exposes: the t=0 state is defined by `qinit` (0→`q` low, nonzero→`q` high),
   not left as `x`, so downstream logic never sees an unknown at start.

5. **x/z on an input** — drive `s` (or `r`) to `x`/`z`, or leave it undriven
   behind a connect boundary that resolves to `x`, mid-sequence while the other
   input is 0. Exposes: the `=== 1` case-equality reads the unresolved input as
   "not asserted", so the latch **holds** rather than spuriously setting or
   resetting — the safe failure mode for a memory element.

6. **Bad `sr11` override** — instantiate with `sr11` set to anything outside
   `{0,1,2,3,4}` (e.g. `7`). Exposes: the `initial` guard's `$error` fires once
   at `t=0` with the offending value and instance path, halting the run rather
   than silently picking a policy.

## Corners / parameter settings to exercise

| Parameter | Corner values | Why |
|---|---|---|
| `sr11` | `2` (NOR default), `3` (NAND), `1`/`0` (set/reset-dom), `4` (hold) | the illegal-input policies — sequence 3; `2` is the cross-coupled-NOR match |
| `qinit` | `0`, `1` | defined power-up either way — sequence 4 |
| `s`, `r` | clean 0/1 edges, near-simultaneous edges, and `x`/`z` | exercise set/reset/hold, the illegal state, and the unresolved-input hold path |

## Translation notes (plain-English, next to the relevant behavior)

- **Hold (`s=r=0`, sequences 1–2):** "this is the whole point of a latch — it
  remembers." No input, no change; the last set/reset sticks.
- **`sr11` (sequence 3):** "what the outputs do when someone asserts set and
  reset at once — a state no design should rely on (hence the `$warning`)." The
  default `2` mirrors a real cross-coupled NOR latch: both outputs go low. The
  other values cover NAND (both high) and the set/reset-dominant and hold
  conventions used by behavioral standard-cell latches.
- **`qinit` (sequence 4):** "what the bit is at power-on." A real latch is a
  coin-flip at power-up; this pins it to a known value so a simulation starts
  from a defined state instead of propagating `x`.
- **x/z hold (sequence 5):** "what happens if the driving logic hasn't decided
  yet." The latch keeps its value — for a memory element, remembering is the
  right thing to do when the inputs are ambiguous.
