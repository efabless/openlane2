# Writing Custom Flows
As configurable as the default ("Classic") flow may be, there are some designs
that would simply be too complex to implement using the existing flow.

For example, hardening a macro + padframe for a top level design is too complex
using the Classic flow, and may require you to write your own custom-based flow.

***First of all***, please review OpenLane's high-level architecture [at this link](../reference/architecture.md).
This defines many of the terms and enumerates strictures used in this document.

## Custom Sequential Flows
### In Configuration Files
If your custom sequential flow entirely relies on built-in steps, you can actually specify
a flow entirely in the `config.json` file, with no API access needed:

```json
{
    "meta": {
        "version": 2,
        "flow": [
            "Yosys.Synthesis",
            "Misc.LoadBaseSDC",
            "OpenROAD.Floorplan",
            "OpenROAD.TapDecapInsertion",
            "OpenROAD.GeneratePDN",
            "OpenROAD.IOPlacement",
            "OpenROAD.GlobalPlacement",
            "OpenROAD.DetailedPlacement",
            "OpenROAD.GlobalRouting",
            "OpenROAD.DetailedRouting",
            "OpenROAD.FillInsertion",
            "Magic.StreamOut",
            "Magic.DRC",
            "Magic.SpiceExtraction",
            "Netgen.LVS"
        ]
    },
    ...
}
```

### Using the API
You'll need to import the `Flow` class as well as any steps you intend to use.

An equivalent flow to the one above would look like this:

```python
from openlane.flows import SequentialFlow
from openlane.steps import Yosys, Misc, OpenROAD, Magic, Netgen

class MyFlow(SequentialFlow):
    Steps = [
        Yosys.Synthesis,
        Misc.LoadBaseSDC,
        OpenROAD.Floorplan,
        OpenROAD.TapDecapInsertion,
        OpenROAD.GeneratePDN,
        OpenROAD.IOPlacement,
        OpenROAD.GlobalPlacement,
        OpenROAD.DetailedPlacement,
        OpenROAD.GlobalRouting,
        OpenROAD.DetailedRouting,
        OpenROAD.FillInsertion,
        Magic.StreamOut,
        Magic.DRC,
        Magic.SpiceExtraction,
        Netgen.LVS
    ]
```

You may then instantiate and start the flow as shown:

```python
flow = MyFlow.init_with_config(
    {
        "PDK": "sky130A",
        "DESIGN_NAME": "spm",
        "VERILOG_FILES": ["./src/spm.v"],
        "CLOCK_PORT": "clk",
        "CLOCK_PERIOD": 10,
    },
    design_dir=".",
)
flow.start()
```

The {method}`openlane.flows.Flow.start` method will return a tuple comprised of:
* The final output state ({math}`State_{n}`).
* A list of all step objects created during the running of this flow object.

```{important}
Do NOT call the `run` method of any `Flow` from outside of `Flow` and its
subclasses- consider it a private method. `start` is class-independent and
does some incredibly important processing.

You should not be subclassing `start` either.
```

## Fully Customized Flows
Each `Flow` subclass must:

* Declare the steps used in the {attr}`openlane.flows.Flow.Steps` attribute.
    * The steps are examined so their configuration variables can be validated ahead of time.
* Implement the {method}`openlane.flows.Flow.run` method.
    * This step is responsible for the core logic of the flow, i.e., instantiating
    steps and calling them.
    * This method must return the final state and a list of step objects created.

You may notice you are allowed to do pretty much anything inside the `run` method.
While that may indeed enable you to perform arbitrary logic in a Flow, it is 
recommended that you write Steps, keeping the logic in the Flow to a minimum.

You may instantiate and use steps inside flows as follows:

```python
synthesis = Yosys.Synthesis(
    config=self.config,
    state_in=...,
    flow=self,
)
synthesis.start()

sdc_load = Misc.LoadBaseSDC(
    config=self.config,
    state_in=synthesis.state_out,
    flow=self
)
```

While you may not modify the configuration object {attr}`openlane.flows.Flow.config`,
you can slightly modify the configuration used by each step using the config object's
{method}`openlane.config.Config.copy` method, which allows you to supply overrides as follows:

```python3
config_altered = config.copy(FP_CORE_UTIL=9)
```

Which will create a new configuration object with one or more attributes modified.
You can pass these to steps as you desire.

Another advantage of this over sequential flows is that you can handle Step failures
more elegantly, i.e., by trying something else when a particular Step (or set of steps) fail.
There are a lot of possibilities.

### Reporting Progress
Correctly-written steps will by default output a log to the terminal, but, running
in a flow, there will always be a progress bar at the bottom of the terminal:

```
Classic - Stage 17 - CTS ━━━━━━━━━━━━━━━━━╺━━━━━━━━━━━━━━━━━━━━━━ 16/37 0:00:20
```

The Flow object has methods to manage this progress bar:
    * {method}`openlane.flows.Flow.set_max_stage_count`
    * {method}`openlane.flows.Flow.start_stage`
    * {method}`openlane.flows.Flow.end_stage`.

They are to be called from inside the `run` method. In Sequential Flows,
{math}`|Steps| = |Stages| = n`, but in custom flows, stages can incorporate any
number of steps. This is useful for example when running series of steps in parallel
as shown in the next section, where incrementing by step is not exactly viable.

### Mutli-Threading
```{important}
The `Flow` object is NOT thread-safe. If you're going to run one or more steps
in parallel, please follow this guide on how to do so.
```

The `Flow` object offers a method to run steps asynchronously, {method}`openlane.config.Config.start_step_async`.
This method returns a [`Future`](https://en.wikipedia.org/wiki/Futures_and_promises)
encapsulating a State object, which can then be used as an input to future Steps.

This approach creates a dependency chain between steps, so if you attempt to
inspect the last Future from a set of asynchronous steps, it will automatically
run the required steps, in parallel if need be.

Here is a demo flow built on exactly this principle. It works across two stages:
* The Synthesis Exploration - tries multiple synthesis strategies in *parallel*.
    The best-performing strategy in terms of minimizing the area makes it to the
    next stage.
* Floorplanning and Placement - tries FP and placement with a high utilization.
    * If the high utilization fails, a lower is fallen back to as a suggestion.

```{literalinclude} ../../../openlane/flows/optimizing.py
---
language: python
start-after: "@Flow.factory.register()"
---
```