# Pitfall: Dimensional balance in `<+` contributions

## Rule
Both sides of every `<+` must carry the same physical units. `V(x) <+ <volts>`,
`I(x) <+ <amps>`. Mixing compiles but is physically nonsense and misbehaves in solve.

## Habits
- Annotate each parameter's unit in a comment; carry units through the algebra.
- `gm*V()` -> amps (gm is S = A/V). `V()/R` -> amps. `I()*R` -> volts. Check each.
- `idt(x)` multiplies units by seconds; `ddt(x)` divides by seconds. Charge
  Q = idt(I) is coulombs; `I <+ ddt(Q)` closes the loop.

## Fast check
- For each `<+`, say the units of the branch and of the RHS. If they differ, the model
  is wrong even if it elaborates.
