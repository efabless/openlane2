# Writing Custom Steps
Just like you may write custom flows, you may also write custom steps to run
within those flows.

***Again***, please review OpenLane's high-level architecture [at this link](../reference/architecture.md).
This defines many of the terms used and enumerates strictures mentioned in this document.

## Generic Steps
Like flows, each Step subclass must:

* Implement the {meth}`openlane.steps.Step.run` method.
    * This step is responsible for the core logic of the step, which is arbitrary.
    * This method must return the final state generated after this step.

```{important}
Do NOT call the `run` method of any `Step` from outside of `Step` and its
subclasses- consider it a private method. `start` is class-independent and
does some incredibly important processing.

You should not be overriding `start` either.
```

But also, each Step is required to:

* Declare any required {class}`openlane.step.State` inputs in the {class}`openlane.step.Step.inputs`
  attribute.
    * This will enforce checking the input states for these views.
* Declare any potential state modifications in the {class}`openlane.step.Step.outputs`
    attribute.
    * This list is checked for completeness and validity- i.e. the {class}`Step`
    superclass WILL throw a `StepException` if a Step modifies any State variable
    it does not declare.
* Declare any used configuration variables in the {class}`openlane.step.Step.config_vars`
    attribute.


```{important}
Don't forget the [`Step` strictures](../reference/architecture.md#step-strictures).
Some of them are programmatically enforced, but some are not.
```

### Implementing `run`
The run header should look like this:

```python
def run(self, *args, **kwargs):
```

The `*args` and `**kwargs` allow subclasses to pass arguments to subprocesses-
more on that later.

First, you want to start by cloning `self.state_in`. You can do this using:
`state_out = super().run(*args, **kwargs)`. This is your output state, and
it is mutable inside `run`, so feel free to issue (valid) modifications.

You can access configuration variables- which are validated by this point- using
 `self.config[KEY]`. If you need to save files, you can get the step directory
 using `self.step_dir`. For example:

```python
design_name = self.config["DESIGN_NAME"]
output_path = os.path.join(self.step_dir, f"{design_name}.def")
```

```{note}
A step has access to:

* Its declared config_vars
* [All Common Flow Variables](../reference/flow_config_vars.md#universal-flow-configuration-variables)
* [All PDK/SCL Variables](../reference/pdk_config_vars.md)

Attempting to access any other variable is undefined behavior.
```

```{warning}
Ensure that, if your configuration variable is **Optional**, that you explicitly
check if the variable `is not None`. If the variable is not Optional, validation
will handle this check for you.
```

Otherwise, you're basically free to write any logic you desire, with one exception:

* If you're running a terminal subprocess you'd like to have OpenLane manage the
  logs for, please use {meth}`openlane.steps.Step.run_subprocess`,
  passing *args and **kwargs. It will manage
  I/O for the process, and allow the creation of report files straight from the
  logs- more on that later.

Do note that this is your opportunity to also extract and update {attr}`openlane.Step.metrics`.
## Creating Reports
You can create report files manually in Python, but if you're running a subprocess,
you can also write `%OL_CREATE_REPORT <name>.rpt` to stdout and everything until
`%OL_END_REPORT` will be forwarded to a file called `<name>.rpt` in the step dir
automatically.

## Tool-Specific Steps
The `Step` object makes heavy use of object-oriented programming to encourage
as much code reuse as possible. To that extent, there exists some more specialized
`Step` abstract base classes that deal with specific utilities:

### {class}`openlane.steps.TclStep` 
`TclStep` implements a `run` that works for most Tcl-based utilities.
This run calls a subprocess with the value of {meth}`openlane.steps.TclStep.get_command`,
and it emplaces all configuration variables as environment variables using this scheme:

* List variables are joined with a space character.
* Enumerations are replaced with the enumeration name.
* Booleans are replaced with `"1"` if True or `"0"` if false.
* Integers and Decimals are turned into Base-10 strings.

The state is also exposed to the TclStep as is:
* Input files are pointed to in variables with the format `CURRENT_<view name>`.
* Output paths are pointed to in the variables with the format `SAVE_<view name>`.

If a TclStep-based step fails, a reproducible is created, which can be submitted
to the respective repository of the tool.

Keep in mind that TclStep-based tools still have to define their `config_vars`,
`inputs` and `outputs`.

#### Subclasses
`TclStep` has various subclasses for a number of Tcl-based utilities:

* {class}`openlane.steps.OpenROADStep`
* {class}`openlane.steps.YosysStep`
* {class}`openlane.steps.MagicStep`

These subclasses acts as an abstract base class for steps that use their
respective utility. They have one abstract method, `get_script_path`.
Most steps subclassing them might not need to even override `run`.

Additionally, they comes with a common set of `config_vars` required by all invocations
of said tool; you can declare more for your step, however, as shown in this example.:

```python
config_vars = OpenROADStep.config_vars + [
    ...
]
```

Be sure to read the subclass's `run` docstring as they may contain critical information.