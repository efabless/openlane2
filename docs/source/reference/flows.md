# Built-in Flows and their Configuration Variables
These flows come included with OpenLane. They use a variety of built-in steps to
either provide a general RTL-to-GDSII flow or more specific niches.

Each Flow's list configuration variables is essentially a sum of its included
steps and the "Universal" Flow Configuration Variables, which consist of two
parts:

```{toctree}
:maxdepth: 1

common_flow_vars
common_pdk_vars
```

If you're looking for documentation for the `Flow` Python classes themselves,
check the API reference [here](./api/flows/index).

## Flows

```{tip}
For a table of contents, press the following button on the top-right corner
of the page: <svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 1024 1024" height="16px" style="vertical-align: middle;">
    <path d="M408 442h480c4.4 0 8-3.6 8-8v-56c0-4.4-3.6-8-8-8H408c-4.4 0-8 3.6-8 8v56c0 4.4 3.6 8 8 8zm-8 204c0 4.4 3.6 8 8 8h480c4.4 0 8-3.6 8-8v-56c0-4.4-3.6-8-8-8H408c-4.4 0-8 3.6-8 8v56zm504-486H120c-4.4 0-8 3.6-8 8v56c0 4.4 3.6 8 8 8h784c4.4 0 8-3.6 8-8v-56c0-4.4-3.6-8-8-8zm0 632H120c-4.4 0-8 3.6-8 8v56c0 4.4 3.6 8 8 8h784c4.4 0 8-3.6 8-8v-56c0-4.4-3.6-8-8-8zM115.4 518.9L271.7 642c5.8 4.6 14.4.5 14.4-6.9V388.9c0-7.4-8.5-11.5-14.4-6.9L115.4 505.1a8.74 8.74 0 0 0 0 13.8z"></path>
</svg>
```

### Classic

```{eval-rst}

A flow of type :class:`openlane.flows.SequentialFlow` that is the most
similar to the original OpenLane 1.0 flow, running the Verilog RTL through
Yosys, OpenROAD, KLayout and Magic to produce a valid GDSII for simpler designs.

This is the default when using OpenLane via the command-line.

```

#### Using from the CLI

```sh
openlane --flow Classic [...]
```

#### Importing

```python
from openlane.flows import Flow

Classic = Flow.factory.get("Classic")
```
#### Included Steps
* [`Yosys.JsonHeader`](./step_config_vars.md#Yosys.JsonHeader)
* [`Yosys.Synthesis`](./step_config_vars.md#Yosys.Synthesis)
* [`Checker.YosysUnmappedCells`](./step_config_vars.md#Checker.YosysUnmappedCells)
* [`Checker.YosysChecks`](./step_config_vars.md#Checker.YosysChecks)
* [`Misc.LoadBaseSDC`](./step_config_vars.md#Misc.LoadBaseSDC)
* [`OpenROAD.STAPrePNR`](./step_config_vars.md#OpenROAD.STAPrePNR)
* [`OpenROAD.Floorplan`](./step_config_vars.md#OpenROAD.Floorplan)
* [`Odb.SetPowerConnections`](./step_config_vars.md#Odb.SetPowerConnections)
* [`Odb.ManualMacroPlacement`](./step_config_vars.md#Odb.ManualMacroPlacement)
* [`OpenROAD.TapEndcapInsertion`](./step_config_vars.md#OpenROAD.TapEndcapInsertion)
* [`OpenROAD.IOPlacement`](./step_config_vars.md#OpenROAD.IOPlacement)
* [`Odb.CustomIOPlacement`](./step_config_vars.md#Odb.CustomIOPlacement)
* [`OpenROAD.GeneratePDN`](./step_config_vars.md#OpenROAD.GeneratePDN)
* [`OpenROAD.GlobalPlacement`](./step_config_vars.md#OpenROAD.GlobalPlacement)
* [`OpenROAD.STAMidPNR`](./step_config_vars.md#OpenROAD.STAMidPNR)
* [`Odb.DiodesOnPorts`](./step_config_vars.md#Odb.DiodesOnPorts)
* [`Odb.HeuristicDiodeInsertion`](./step_config_vars.md#Odb.HeuristicDiodeInsertion)
* [`OpenROAD.RepairDesign`](./step_config_vars.md#OpenROAD.RepairDesign)
* [`OpenROAD.DetailedPlacement`](./step_config_vars.md#OpenROAD.DetailedPlacement)
* [`OpenROAD.CTS`](./step_config_vars.md#OpenROAD.CTS)
* [`OpenROAD.STAMidPNR-1`](./step_config_vars.md#OpenROAD.STAMidPNR-1)
* [`OpenROAD.ResizerTimingPostCTS`](./step_config_vars.md#OpenROAD.ResizerTimingPostCTS)
* [`OpenROAD.STAMidPNR-2`](./step_config_vars.md#OpenROAD.STAMidPNR-2)
* [`OpenROAD.GlobalRouting`](./step_config_vars.md#OpenROAD.GlobalRouting)
* [`OpenROAD.ResizerTimingPostGRT`](./step_config_vars.md#OpenROAD.ResizerTimingPostGRT)
* [`OpenROAD.STAMidPNR-3`](./step_config_vars.md#OpenROAD.STAMidPNR-3)
* [`OpenROAD.DetailedRouting`](./step_config_vars.md#OpenROAD.DetailedRouting)
* [`Checker.TrDRC`](./step_config_vars.md#Checker.TrDRC)
* [`Odb.ReportDisconnectedPins`](./step_config_vars.md#Odb.ReportDisconnectedPins)
* [`Checker.DisconnectedPins`](./step_config_vars.md#Checker.DisconnectedPins)
* [`Odb.ReportWireLength`](./step_config_vars.md#Odb.ReportWireLength)
* [`Checker.WireLength`](./step_config_vars.md#Checker.WireLength)
* [`OpenROAD.FillInsertion`](./step_config_vars.md#OpenROAD.FillInsertion)
* [`OpenROAD.RCX`](./step_config_vars.md#OpenROAD.RCX)
* [`OpenROAD.STAPostPNR`](./step_config_vars.md#OpenROAD.STAPostPNR)
* [`OpenROAD.IRDropReport`](./step_config_vars.md#OpenROAD.IRDropReport)
* [`Magic.StreamOut`](./step_config_vars.md#Magic.StreamOut)
* [`KLayout.StreamOut`](./step_config_vars.md#KLayout.StreamOut)
* [`Magic.WriteLEF`](./step_config_vars.md#Magic.WriteLEF)
* [`KLayout.XOR`](./step_config_vars.md#KLayout.XOR)
* [`Checker.XOR`](./step_config_vars.md#Checker.XOR)
* [`Magic.DRC`](./step_config_vars.md#Magic.DRC)
* [`Checker.MagicDRC`](./step_config_vars.md#Checker.MagicDRC)
* [`Magic.SpiceExtraction`](./step_config_vars.md#Magic.SpiceExtraction)
* [`Checker.IllegalOverlap`](./step_config_vars.md#Checker.IllegalOverlap)
* [`Netgen.LVS`](./step_config_vars.md#Netgen.LVS)
* [`Checker.LVS`](./step_config_vars.md#Checker.LVS)

<hr />

### OpenInKLayout

```{eval-rst}

This 'flow' actually just has one step that opens the LEF/DEF from the
initial state object in KLayout. Fancy that.

Intended for use with run tags that have already been run with
another flow, i.e.: ::

  openlane [...]
  openlane --last-run --flow OpenInKLayout [...]

```

#### Using from the CLI

```sh
openlane --flow OpenInKLayout [...]
```

#### Importing

```python
from openlane.flows import Flow

OpenInKLayout = Flow.factory.get("OpenInKLayout")
```
#### Included Steps
* [`KLayout.OpenGUI`](./step_config_vars.md#KLayout.OpenGUI)

<hr />

### OpenInOpenROAD

```{eval-rst}

This 'flow' actually just has one step that opens the ODB from
the initial state object in OpenROAD.

Intended for use with run tags that have already been run with
another flow, i.e. ::

  openlane [...]
  openlane --last-run --flow OpenInOpenROAD [...]

```

#### Using from the CLI

```sh
openlane --flow OpenInOpenROAD [...]
```

#### Importing

```python
from openlane.flows import Flow

OpenInOpenROAD = Flow.factory.get("OpenInOpenROAD")
```
#### Included Steps
* [`OpenROAD.OpenGUI`](./step_config_vars.md#OpenROAD.OpenGUI)

<hr />

