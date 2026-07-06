# Stimulus Plan  `sc_doubler_top`

Written plan only  no testbench, no `.do` scripts, no driver module. Sequences,
corners, and what each is meant to expose.

## Ports to drive

| Port | Kind | Not supplied by the model |
|---|---|---|
| `vin` | electrical (conservative) | DC source, series source impedance, AC modulation |
| `vout` | electrical (conservative) | output reservoir capacitor, load resistor/current sink |
| `gnd` | electrical (conservative) | reference node (typically 0 V) |
| `phi1`, `phi2` | digital `wire` | non-overlapping clock phases, dead-time control |

## Core sequences

1. **Ideal DC transfer (Vout = 2*Vin)**  hold `phi1` and `phi2` in their
   respective steady states (phi1=1, phi2=0 for charge; phi1=0, phi2=1 for
   discharge) with a slow switching frequency (<< 1/(2*pi*Rload*Cout)) so the
   output settles completely between phases. Drive `vin` with a DC sweep from
   0 V to the maximum rated input. Exposes: the ideal 2:1 voltage gain in
   steady-state, confirming the topology sums Vin + Vc1 = 2*Vin at the output
   node. Verify Vout tracks 2*Vin across the sweep range.

2. **Switching transient at nominal fsw**  drive `vin` with a fixed DC value
   (e.g., 1 V), `phi1` and `phi2` with a 50% duty cycle square wave at the
   target switching frequency fsw, non-overlapping with dead-time tdead.
   Place a load (e.g., 1 kOhm resistor to ground) on `vout`. Exposes: the
   charge-transfer ripple on Vout, the SSL/FSL output impedance corner, and
   whether the flying capacitor C1 fully charges/discharges within each
   phase. Confirm Vout averages ~2*Vin with expected ripple amplitude.

3. **Phase overlap fault**  drive `phi1` and `phi2` with overlapping high
   states (violate non-overlap). Drive `vin` with a fixed DC value. Exposes:
   shoot-through current path from Vin through both switch networks directly
   to Vout/GND, creating a low-impedance path that collapses the output and
   draws excessive current. Confirm the model does not diverge or error -- it
   faithfully represents the fault condition as a modeling artifact to be
   caught by the stimulus.

4. **Phase dead-time sweep**  drive `phi1` and `phi2` with a fixed fsw but
   sweep the dead-time tdead from 0 to a significant fraction of the period
   (e.g., 0 to 40%). Drive `vin` with a fixed DC value and a load on `vout`.
   Exposes: the trade-off between shoot-through prevention (longer dead-time)
   and effective conduction time (shorter dead-time). Confirm Vout remains
   stable and the average output voltage scales appropriately with reduced
   conduction window.

5. **Load step transient**  drive `vin` with a fixed DC value, `phi1`/`phi2`
   at nominal fsw with dead-time. Step the load on `vout` from no-load to a
   heavy load (e.g., 1 kOhm to 100 Ohm). Exposes: the output impedance and
   settling time of the converter under load transients. Confirm Vout sags
   by an amount consistent with the SSL/FSL corner and recovers within the
   expected time constant.

6. **Input ripple rejection**  drive `vin` with a DC value plus a small AC
   ripple (e.g., 100 mVpp at 1 kHz), `phi1`/`phi2` at nominal fsw. Place a load
   on `vout`. Exposes: how much of the input ripple appears at the output.
   For an ideal SC doubler with no output capacitor, the input ripple is
   sampled and appears at the output scaled by the transfer function. Confirm
   the ripple at Vout is approximately 2x the input ripple (ideal case).

## Corners / parameter settings to exercise

| Parameter | Corner values | Why |
|---|---|---|
| `c1` | 10 nF, 100 nF, 1 uF | flying cap size affects charge per cycle and output ripple; smaller caps = more ripple, larger caps = slower settling |
| `ron_tier1`, `ron_tier2` | 10 mOhm (near-ideal), 50 mOhm (default), 100 mOhm, 1 Ohm | switch resistance affects conduction losses and FSL; higher Ron = lower efficiency and higher output impedance |
| `roff` | 100 MOhm (default), 1 MOhm (leaky) | off-state leakage affects efficiency when switches are off; lower roff = more leakage current |
| `trise`, `tfall` | 0.1 ns (fast), 1 ns (default), 10 ns (slow) | switch edge speed affects commutation smoothness for Newton; too slow relative to period means switch never fully turns on |
| `fsw` | 100 kHz, 1 MHz, 10 MHz | switching frequency affects ripple frequency and magnitude; higher fsw = smaller ripple but higher switching losses |
| `tdead` | 0 ns (no dead-time), 10 ns, 50 ns | dead-time affects shoot-through prevention vs. conduction time |

## Translation notes (plain-English, next to the relevant sequence)

- **Ideal DC transfer (sequence 1):** "does it actually double the voltage?" The
  core functionality check -- without this passing, nothing else matters. In
  the ideal case with no load and settled switching, Vout should equal 2*Vin.
- **Switching transient (sequence 2):** "how does it behave when actually
  switching?" Confirms the model captures the dynamic behavior, not just the
  steady-state DC transfer. The ripple amplitude and average output voltage
  should match expectations based on C1, fsw, and load.
- **Phase overlap fault (sequence 3):** "what happens if the phases overlap?"
  This is a deliberate fault condition to ensure the model doesn't hide
  design errors. The shoot-through should be visible as excessive current and
  collapsed output voltage.
- **Phase dead-time sweep (sequence 4):** "how much dead-time is too much?"
  Finds the point where dead-time starts to significantly reduce the effective
  output voltage due to reduced conduction window.
- **Load step transient (sequence 5):** "how fast does it recover from a load
  change?" The settling time and voltage sag reveal the output impedance and
  dynamic performance.
- **Input ripple rejection (sequence 6):** "does input noise show up at the
  output?" For an ideal SC converter, input ripple is sampled and appears at
  the output scaled by the transfer function (2x for a doubler).

## Topology reminder

```
Phase 1 (phi1=1, phi2=0):
  vin ----S1a---- c1_top
                 |
  gnd ----S1b---- c1_bot
  
  C1 charges to Vin

Phase 2 (phi1=0, phi2=1):
  vin ----S2a---- c1_bot
                 |
  c1_top ----S2b---- vout
  
  C1 in series with Vin: Vout = Vin + Vc1 = 2*Vin
```

Switch stress tiers:
- **tier 1 (<= Vin):** S1a, S1b (only see Vin during charge phase)
- **tier 2 (<= 2*Vin):** S2a, S2b (see up to 2*Vin during discharge phase)
