# Corners and Static-Timing Analysis

To ensure a chip can continue to function under various conditions, the chip
must undergo static timing analysis under different **timing corners**.

The timing corners are a combination of characteristics, specifically four, two
being as a result of the process:

* **Parasitic/Interconnect Corners**: Metal layers may have slightly different
  geometry based on manufacturing, which will affect the wires' parasitics
  (capacitance and resistance.)
* **Transistor Corners**: Also called "process corners", more commonly, variance
  in transistor carrier mobility, denoted as follows:
  * `s`, `t`, `f` for whether NMOS transistors are slow, typical, or fast respectively.
  * Another `s`, `t`, `f` but for PMOS transistors.
  For example, a corner with fast NMOS and PMOS would be denoted `ff`.
  See https://en.wikipedia.org/wiki/Process_corners#FEOL_corners for more info.

And two that are dependent on the operation environment:

* **Temperature**: A higher temperature causes transistors to switch slower.
* **Voltage**: A higher voltage causes transistors to switch faster.

Common EDA files incorporate these corners as follows:

* `.spef` files are usually a function of interconnect corners, but temperature,
  voltage and process corners may also affect the parasitic values at smaller nodes.

* `.spice` files usually incorporate a specific combination of interconnect and transistor corners, but temperature and voltage are continuously variable.

* `.lib` files characterize a circuit at a full corner.
    * For standard cells, the parasitic effect is minimal, leading to the common
      acronym "PVT": **P**rocess/Transistor Corner, **V**oltage and **T**emperature
      for their lib files.
    * For macros, the parasitic effect is signficiant, and a lib file for one
      parasitic corner is not necessary applicable for others. 

```{note}
The default extraction utility for OpenLane, OpenROAD OpenRCX, only accounts for
the interconnect corner.
```

## Violations

STA reports two kinds of violations:
* Setup violations: A register's data input was changed too soon before a clock edge.
  Setup violations do not necessarily mean a dead chip, however the final chip
  may have to run at a lower clock, which is not acceptable for some applications.
* Hold violations: A register's data output was changed too soon AFTER a clock edge.
  Chips with hold violations are effectively dead- infamously, MPW-1's management
  controller had a hold violation and designers had to resort to extraordinary
  measures to revive them.

Here are some good videos about the MPW-1 saga:
  * M. Venn, "MPW1 silicon arrived! What went wrong?", *ZeroToASIC*, YouTube. Online: https://www.youtube.com/watch?v=lw9ucvgQJjk
  * S. Munaut, "Bringing chips back from the dead : MPW-1 Show-off", *Sylvain Munaut's Channel*, YouTube. Online: https://www.youtube.com/watch?v=f_G5ad8SbHo

## Default Flow Configuration
In its current state, the default OpenLane flow allows SCLs to configure the following:

* A list of PVT-corners with names that correspond to `.lib` files
* A list of interconnect corners with arbitrary names that *may* correspond to any of:
  * `TECH_LEF`

The sky130A/sky130_fd_sc_hd SCL, for example, comes with configurations for these corners:

* PVT: Corner data stored in [`LIB`](../reference/pdk_config_vars.md#LIB)

| Name | Process {NMOS, PMOS} | Voltage (V) | Temperature (C) | Corresponding File |
| - | - | - | - | - |
| "tt_025C_1v80" | {T, T} | 1.8 | 25 | `sky130_fd_sc_hd__tt_025C_1v80.lib` |
| "ss_100C_1v60" | {S, S} | 1.6 | 100 | `sky130_fd_sc_hd__ss_100C_1v60.lib` |
| "ff_n40C_1v95" | {F, F} | 1.95 | -40 | `sky130_fd_sc_hd__ff_n40C_1v95.lib` |

* Interconnect: Corner data stored in [`TECH_LEFS`](../reference/pdk_config_vars.md#TECH_LEFS) and [`RCX_RULESETS`](../reference/pdk_config_vars.md#RCX_RULESETS)

| Name | Description | Corresponding Technology LEF | Corresponding Ruleset |
| - | - | - | - | 
| "nom" | The nominal interconnect corner | `sky130_fd_sc_hd__nom.tlef` | `rules.openrcx.sky130A.nom.calibre` |
| "min" | The minimal interconnect corner | `sky130_fd_sc_hd__min.tlef` | `rules.openrcx.sky130A.min.calibre` |
| "max" | The maximum interconnect corner | `sky130_fd_sc_hd__max.tlef` | `rules.openrcx.sky130A.max.calibre` |

As a user, you are free to override these values as you would any other PDK/SCL
variables, however, it is your responsibility to keep the consistent: if you alte

For most STA invocations, the **first** PVT corner will be used (timing does not
incorporate parasitics until the very end.)

<!-- TODO: MCSTA/Macro >