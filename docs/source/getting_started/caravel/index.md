### SPM as a macro for [Caravel](https://caravel-harness.readthedocs.io/en/latest/)

Often a design by itself serves no purpose unless interfaced with and/or
integrated into another design or a chip. We are going to harden the `spm`
design again but this time we will have it as a
[Caravel User Project](https://caravel-user-project.readthedocs.io/en/latest/)
macro for the chip [Caravel](https://caravel-harness.readthedocs.io/en/latest/)

```{admonition} About Caravel
:class: seealso

The Efabless Caravel chip is a ready-to-use test harness for creating designs
with the Google/Skywater 130nm Open PDK. The Caravel harness comprises of base
functions supporting IO, power, and configuration as well as drop-in modules for
a management SoC core, and an approximately 3000um x 3600um open project area
for the placement of user IP blocks.

Check [Caravel](https://caravel-harness.readthedocs.io/en/latest/) for more
information.
```

#### RTL updates

We begin by updating the RTL needed for integration of the spm into Caravel.

1. Create a new directory `~/my_designs/spm-user_project_wrapper/` and

   ```console
   [nix-shell:~/openlane2]$ mkdir -p ~/my_designs/spm-user_project_wrapper
   ```

1. Add the following new RTL to
   `~/my_designs/spm-user_project_wrapper/SPM_example.v`:

   ````{dropdown} SPM_example.v

   ```{literalinclude} ../../../../openlane/examples/spm-user_project_wrapper/SPM_example.v

   ```

   ````

1. Also add `~/my_designs/spm-user_project_wrapper/user_project_wrapper.v`:

   ````{dropdown} user_project_wrapper

   ```{literalinclude} ../../../../openlane/examples/spm-user_project_wrapper/user_project_wrapper.v

   ```

   ````

1. Finally, we need an additional file
   `~/my_designs/spm-user_project_wrapper/defines.v` which is required by
   Caravel User Project.

   ````{dropdown} defines.v

   ```{literalinclude} ../../../../openlane/examples/spm-user_project_wrapper/defines.v
   ```

   ````

```{seealso}
Check out
[Caravel User Project's documentation on Verilog Integration](https://caravel-user-project.readthedocs.io/en/latest/#verilog-integration)
for information about the changes that were done to the RTL.
```

(configuration-user-project-wrapper)=
#### Configuration

Then we need to create a configuration file to pass to the flow. OpenLane has
an interactive tool to do just that:

```console
[nix-shell:~/my_designs/spm-user_project_wrapper]$ openlane.config create-config
Please input the file name for the configuration file [config.json]: config.json
Enter the base directory for your design [.]: .
Enter the design name (which should be equal to the HDL name of your top module): user_project_wrapper
Enter the name of your design's clock port: wb_clk_i
Enter your desired clock period in nanoseconds: 25
Input the RTL source file #0 (Ctrl+D to stop): defines.v
Input the RTL source file #1 (Ctrl+D to stop): SPM_example.v
Input the RTL source file #2 (Ctrl+D to stop): user_project_wrapper.v
```

#### Running the flow

Let's try running the flow:

```console
[nix-shell:~/openlane2]$ openlane ~/my_designs/spm-user_project_wrapper/config.json
```

#### Addressing issues

The flow will fail with the following message:

```text
[ERROR PPL-0024] Number of IO pins (637) exceeds maximum number of available positions (220).
Error: ioplacer.tcl, 56 PPL-0024
```

The reason that happens is that when we change the RTL of the design we
changed the IO pin interface of the design to match the interface needed by
Caravel User Project.

Caravel User Project needs a lot of IO pins. By default, the flow will
attempt to create a floorplan using a utilization of 50%. Relative to the cells
in the design, there are too many IO pins to fit in such a floorplan.

This can be solved by setting a lower utilization value. You will find out that
about 5% utilization is needed for the floorplan to succeed. This is controlled
by `FP_CORE_UTIL` {py:class}`Variable <openlane.config.Variable>`.

Update the configuration as follows:

```json
{
  "DESIGN_NAME": "user_project_wrapper",
  "CLOCK_PERIOD": 25,
  "CLOCK_PORT": "wb_clk_i",
  "VERILOG_FILES": [
    "dir::./defines.v",
    "dir::./SPM_example.v",
    "dir::./user_project_wrapper.v"
  ],
  "FP_CORE_UTIL": 5
}
```

Then run the flow again:

```console
[nix-shell:~/openlane2]$ openlane ~/my_designs/spm-user_project_wrapper/config.json
```

#### Examining the results

Let's view the layout:

```console
[nix-shell:~/openlane2]$ openlane --last-run --flow openinklayout ~/my_designs/spm-user_project_wrapper/config.json
```

```{figure} ./spm-caravel-user-project-util.png

SPM with 5% utilization
```

```{tip}
You can control the visible layers in KLayout by right-clicking in the
layers area and selecting hide all layers. Then double click on the layers that
you want to view. In this figure, only `met2.pin`, `met3.pin`, and
`prBoundary.boundary` are shown.
```

As shown above, there are a lot of pins needed by the design and certainly, a
floorplan with 50% utilization wouldn't fit all the pins.

---

#### Caravel Integration

Caravel User Project is a macro inside Caravel. To be able to use
any design as a Caravel User Project, it has to match the footprint
that Caravel is expecting so we can't rely on `FP_CORE_UTIL`.

##### IO Pins

The top-level design Caravel is expecting any Caravel User Project
to have the IO pins at specific locations and with specific dimensions. We can
achieve that by using the variable `FP_DEF_TEMPLATE`. `FP_DEF_TEMPLATE` is a
`DEF` file that is used as a template for the design's floorplan. IOs pin shapes
and locations are copied from the template DEF file over to our design. In
addition, the same die area is used as the one in the template DEF file.

Save this file
[template.def](../../../../openlane/examples/spm-user_project_wrapper/template.def),
in your design's directory which should be
`~/my_designs/spm-user_project_wrapper/`. Then update the design's configuration
by adding `FP_DEF_TEMPLATE` variable:

```json
{
  "DESIGN_NAME": "user_project_wrapper",
  "VERILOG_FILES": ["dir::./defines.v", "dir::./SPM_example.v"],
  "CLOCK_PERIOD": 25,
  "CLOCK_PORT": "wb_clk_i",
  "FP_DEF_TEMPLATE": "dir::./template.def",
  "FP_SIZING": "absolute",
  "DIE_AREA": [0, 0, 2920, 3520]
}
```

##### Power Distribution Network (PDN)

A macro's Power Distribution Network (`PDN`) is responsible for the delivery of
power to cells in the design. A macro's internal PDN is exposed through pins
as an interface for integration with other designs. These pins are similar to
data IO pins but often much larger.

Here is another example of a macro that is fully integrated inside Caravel:

```{figure} ./caravel-1.png
:align: center

Example of a macro integrated inside Caravel
```

This figure displays Caravel chip. The highlighted rectangle is where
Caravel User Project is. Let's zoom in at the top right corner of this
area.

```{figure} ./caravel-pdn-2.png
:align: center

Top right corner of macro integrated inside Caravel
```

As highlighted there are power rings surrounding our wrapper. connectivity
between the wrapper rings and the chip is done through the highlighted light
blue `met3` wires.

Our `PDN` of Caravel User Project has to be configured to look like
the figure shown above. This is done by using a collection of variables that are
responsible for controlling the shape, location, and metal layers of the `PDN`
pins offering the power interface of the macro.

Let's add these variables to our configuration file:

```json
{
  "DESIGN_NAME": "user_project_wrapper",
  "VERILOG_FILES": ["dir::./defines.v", "dir::./SPM_example.v"],
  "CLOCK_PERIOD": 25,
  "CLOCK_PORT": "wb_clk_i",
  "FP_DEF_TEMPLATE": "dir::./template.def",
  "FP_SIZING": "absolute",
  "DIE_AREA": [0, 0, 2920, 3520],
  "FP_PDN_CORE_RING": 1,
  "FP_PDN_CORE_RING_VWIDTH": 3.1,
  "FP_PDN_CORE_RING_HWIDTH": 3.1,
  "FP_PDN_CORE_RING_VOFFSET": 12.45,
  "FP_PDN_CORE_RING_HOFFSET": 12.45,
  "FP_PDN_CORE_RING_VSPACING": 1.7,
  "FP_PDN_CORE_RING_HSPACING": 1.7,
  "FP_PDN_VWIDTH": 3.1,
  "FP_PDN_HWIDTH": 3.1,
  "FP_PDN_VSPACING": "expr::(5 * $FP_PDN_CORE_RING_VWIDTH)",
  "FP_PDN_HSPACING": "expr::(5 * $FP_PDN_CORE_RING_HWIDTH)"
}
```

```{seealso}
Visit {step}`OpenROAD.GeneratePDN` for more information about each
of the above variables.
```

Caravel is a chip with multiple power domains. We need to match these domains
in our configuration by adding `VDD_NETS` and `GND_NETS` variables:

```json
{
  "DESIGN_NAME": "user_project_wrapper",
  "VERILOG_FILES": ["dir::./defines.v", "dir::./SPM_example.v"],
  "CLOCK_PERIOD": 25,
  "CLOCK_PORT": "wb_clk_i",
  "FP_DEF_TEMPLATE": "dir::./template.def",
  "FP_SIZING": "absolute",
  "DIE_AREA": [0, 0, 2920, 3520],
  "FP_PDN_CORE_RING": 1,
  "FP_PDN_CORE_RING_VWIDTH": 3.1,
  "FP_PDN_CORE_RING_HWIDTH": 3.1,
  "FP_PDN_CORE_RING_VOFFSET": 12.45,
  "FP_PDN_CORE_RING_HOFFSET": 12.45,
  "FP_PDN_CORE_RING_VSPACING": 1.7,
  "FP_PDN_CORE_RING_HSPACING": 1.7,
  "FP_PDN_VWIDTH": 3.1,
  "FP_PDN_HWIDTH": 3.1,
  "FP_PDN_VSPACING": "expr::(5 * $FP_PDN_CORE_RING_VWIDTH)",
  "FP_PDN_HSPACING": "expr::(5 * $FP_PDN_CORE_RING_HWIDTH)",
  "VDD_NETS": ["vccd1", "vccd2", "vdda1", "vdda2"],
  "GND_NETS": ["vssd1", "vssd2", "vssa1", "vssa2"]
}
```

##### Timing Constraints

```{admonition} STA and timing closure guide
:class: important

It is highly recommended that you read the
[STA and timing closure guide](https://docs.google.com/document/d/13J1AY1zhzxur8vaFs3rRW9ZWX113rSDs63LezOOoXZ8/)
to fully understand this section.
```

Finally, to achieve a timing-clean Caravel User Project design integrated into
Caravel, it is crucial to satisfy specific timing constraints at the boundary
I/Os. The provided Caravel User Project
[SDC file](../../../../openlane/examples/spm-user_project_wrapper/base_sdc_file.sdc)
guides the tools to ensure proper timing performance of the design interfacing
with Caravel. The SDC file mainly defines:

1. Clock Network:

   Specifying clock characteristics and effects such as:

   - Primary clock port and period
   - Clock uncertainty, transition, and latency.

1. Design rules:

   Specifying the maximum limit for transition time and for fanout. The tools
   apply the minimum of the limits set by the technology libraries and the
   SDC.

1. I/O timing constraints:

   Specifying the expected delay range for signals to arrive at inputs and to be
   valid at the outputs. As well as, the inputs transition time ranges and
   expected loads on the outputs.

1. Timing exceptions:

   By default, the tools assume that data launched at a path startpoint is
   captured at all path endpoints within one clock cycle. Whenever a path is not
   intended to operate in this manner, a timing exception should be defined such
   as:

   - False paths: specifies paths that are not required to be analyzed.
   - Multicycle paths: specifies the required number of clock cycles to
     propagate the data for certain paths rather than the default one clock
     cycle.

   In Caravel User Project SDC file, it specifies that some ports require 2
   clock cycles which relaxes the setup constraints on these ports and hence
   avoids over-optimizations.

1. On-chip Variations:

   To model {term}`On-chip variation` effects, a derate factor is applied to
   specify the margin on all delays. A typical value for `sky130` is `5%`.

```{admonition} Static Timing Analysis on Caravel *and* Caravel User Project
:class: tip

A final STA check with the Caravel User Project integrated into Caravel is
required to achieve timing closure. While having a successful flow run without
any timing violations indicates that almost certainly the design is
timing-clean, this final combined simulation ensures that.
```

Download
[this SDC file](../../../../openlane/examples/spm-user_project_wrapper/base_sdc_file.sdc),
and place it in our design directory `~/my_design/spm-user_project_wrapper/`.
Then set the variables {var}`OpenROAD.STAPostPNR::SIGNOFF_SDC_FILE` and
{var}`OpenROAD.STAPostPNR::PNR_SDC_FILE` to point to the downloaded file to be
able to apply these constraints during implementation and signoff while running
the flow. Our final configuration looks like this:

```json
{
  "DESIGN_NAME": "user_project_wrapper",
  "VERILOG_FILES": ["dir::./defines.v", "dir::./SPM_example.v"],
  "CLOCK_PERIOD": 25,
  "CLOCK_PORT": "wb_clk_i",
  "FP_DEF_TEMPLATE": "dir::./template.def",
  "FP_SIZING": "absolute",
  "DIE_AREA": [0, 0, 2920, 3520],
  "FP_PDN_CORE_RING": 1,
  "FP_PDN_CORE_RING_VWIDTH": 3.1,
  "FP_PDN_CORE_RING_HWIDTH": 3.1,
  "FP_PDN_CORE_RING_VOFFSET": 12.45,
  "FP_PDN_CORE_RING_HOFFSET": 12.45,
  "FP_PDN_CORE_RING_VSPACING": 1.7,
  "FP_PDN_CORE_RING_HSPACING": 1.7,
  "FP_PDN_VWIDTH": 3.1,
  "FP_PDN_HWIDTH": 3.1,
  "FP_PDN_VSPACING": "expr::(5 * $FP_PDN_CORE_RING_VWIDTH)",
  "FP_PDN_HSPACING": "expr::(5 * $FP_PDN_CORE_RING_HWIDTH)",
  "VDD_NETS": ["vccd1", "vccd2", "vdda1", "vdda2"],
  "GND_NETS": ["vssd1", "vssd2", "vssa1", "vssa2"],
  "PNR_SDC_FILE": "dir::./base_sdc_file.sdc",
  "SIGNOFF_SDC_FILE": "dir::./base_sdc_file.sdc"
}
```
