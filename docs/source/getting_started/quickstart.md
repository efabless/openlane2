# Quick-Start Guide

## Overview

:::{note}
This page assumes you have already installed OpenLane. Check the sidebar to install OpenLane if you haven't already.
:::

This guide covers running the flow on existing desings, adding new designs and quick overview of the design directory structure.

## Using Configuration Files
Like with previous versions of OpenLane, you can use configuration files as specified in their reference manual [here](../reference/configuration.md). You would have to create a `config.json` or `config.tcl` file.

The entry point for using OpenLane with a configuration file is the Python `openlane` module.

In order to run the default flow on a given design, you need to execute the following command:

```sh
python3 -m openlane --dockerized <path/to/design/config>
```

```{note}
You will need to omit `--dockerized` if you're using a native installation method, such as Nix, Conda or just compiling your own tools from source.
```

For example, a design named `gcd` would have an invocation that looks something like this:

```sh
python3 -m openlane --dockerized ./gcd/config.json
```


## Using the API

```{warning}
The API cannot be used in dockerized mode, and is intended for native installation methods.
```

You may simply elect to write a Python script to configure and harden your design. For an SPM module with one file `./src/spm.v`, for example, you can use this script to place and route it.

```python
import openlane

Classic = openlane.Flow.factory.get("Classic")

flow = Classic.init_with_config(
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