# 2.0.0-dev16
* Remove `FP_PDN_MACRO_HOOKS` for `caravel_upw`
* Disable `QUIT_ON_SYNTH_CHECKS` for `caravel_upw`
* Rename `SYNTH_USE_PG_PINS_DEFINES` to `SYNTH_POWER_DEFINES`
* Rename `CHECK_UNMAPPED_CELLS` to `QUIT_ON_UNMAPPED_CELLS`
* Add `IGNORE_DISCONNECTED_MODULES` for `disconnected_pins.py`. Ignoring some cells is necessary for example conb cell in sky130
* Add `./openlane/scripts/odbpy/disconnected_pins.py` that reports disconnected instance pins in the design
* Add `./openlane/scripts/odbpy/set_power_connections.py`
* Rename metrics:
    - `route__max__wirelength` -> `route__wirelength__max`
    - `die__area` -> `design__die__bbox`
    - `core__area` -> `design__core__bbox`
    - `lvs__total__errors` -> `design__lvs_errors__count`
    - `lvs__device_count_difference` -> `design__lvs_device_difference__count`
    - `lvs__net_count_differences` -> `design__lvs_net_differences__count`
    - `lvs__property_fails` -> `design__lvs_property_fails__count`
    - `lvs__unmatched_devices` -> `design__lvs_unmatched_devices__count`
    - `lvs__unmatched_nets` -> `design__lvs_unmatched_nets__count`
    - `lvs__unmatched_pins` -> `design__lvs_unmatched_pins__count`
* Add steps:
    - `DisconnectedPins`: Checker for `ReporDisconnectedPins`.
    - `ReportDisconnectedPins`: Report disconnected instance pins in a design.
    - `JsonHeader`: RTL to JSON.
    - `SetPowerConnections`: Uses JSON generated in `JsonHeader` and modules information in odb to add global connections for macros in a design.

# 2.0.0-dev15

* `log` -> `info`
* Add mitigation for KLayout None variables.
* `logging` isolated from `common` into its own module
* CLI now accepts either a value or a string for log levels.
* CLI now prints help if no arguments are provided.
* Fix issue where `rich` eats the cursor if it exits by interrupt.

# 2.0.0-dev14

* Multiple logging levels specified via CLI. Can also be set via `set_log_level` in the API.
* Updated all `run_subprocess` invocations to create a log, named after the `Step`'s `id` by default.
* Fixed issue with `ROUTING_CORES` not using the computer's total core count by default.
* Fixed an issue with Tcl config files where `DESIGN_DIR` was resolved relatively, which greatly confused KLayout.

# 2.0.0-dev13

* Add ApplyDEFTemplate step.
* Update most `odbpy` CLIs to accept multiple LEF files.

# 2.0.0-dev12

* Cleaned up build system.
* Add support for OpenROAD with `or-tools` on macOS.

# 2.0.0-dev11

* Added `QUIT_ON_SYNTH_CHECKS`
* Added  `QUIT_ON_UNMAPPED_CELLS`
* Added metric `design__instance_unmapped__count`
* Allowed `MetricChecker` to raise `StepError`

# 2.0.0-dev10
* Updated OpenROAD to `6de104d` and KLayout to `0.28.5`.
* OpenROAD builds now use system boost to cut on build times.
* Added new dedicated interactive mode to replace "Step-by-step" API: activated by calling `ConfigBuilder.interactive`, which replaced `per_step`.
    * State, Config and Toolbox for `Step`s all become implicit and rely on global variables.
    * On the other hand, `config=` must now be passed explicitly to non-interactive flows.
* Added Markdown-based IPython previews for `Step` and `Config` objects.
    * Added an API to render `DEF` or `GDS` files to PNG files to help with that.
* Changed API for KLayout Python scripts to be a bit more consistent.
* Renamed a number of variables for consistency.
* Tweaked documentation slightly for consistency.

# 2.0.0-dev9

* Moved `State` to its own submodule.
* Fixed bug with loading default SCL.

# 2.0.0-dev8

* Added a step-by-step API for OpenLane.
    * Involves new `ConfigBuilder` method, `per_step`, which creates configuration files that can be incremented per-step.
    * This mode is far more imperative and calls may have side effects.
* Added an example IPython notebook to use the aforementioned API.
    * Add a number of APIs to display `State` as a part of a notebook.
* Added various default values for `Step` so it can be used without too many parameters. (`config` is still required, but `state_in` will become an empty state if not provided.)
* Moved various documentation functions to the `Variable` object so they can also be used by IPython.
* Updated documentation for `Variable` object.
* Various documentation updates and fixes.

# 2.0.0-dev7

* More build fixes.

# 2.0.0-dev6

* Added magic builds to macOS
* Fixed KLayout builds on macOS
* Tweaks to Nix build scripts
* Removed hack to make KLayout work on macOS
* Removed NoMagic flow

# 2.0.0-dev5

* Fixed commandline `--flow` override.
* Removed call-stack based inference of `state_in` argument for steps: a step initialized without a `state_in` will have an empty in-state.
* Changed signature of `Flow.run`, `Flow.start` to return `(State, List[Step])`, returning only the last state as the per-step states can be accessed via `step[i].state_out`.
* Removed distinction between the `Step.id` and it factory-registered string: the ID is now used for the factory, in the format `Category.Step` for the built-in steps.
* Fixed `--from` and `--to`, also add validation and case-insensitivity.
* Various bugfixes to Tcl script packager.

# 2.0.0-dev4

* Fix `Optimizing` flow.

# 2.0.0-dev3

* Remove Mako as requirement, migrate relevant code.

# 2.0.0-dev2

* Updated installation instructions.
* Separated variables step-by-step.
* Various fixes to environment variables, especially when using OpenROAD Odb Python scripts.
* Add specialized steps to check and/or quit on specific metrics and/or variables.

# 2.0.0-dev1

* Rewrite OpenLane in Python using a new, Flow-based architecture.
* Add packaging using the Nix Package Manager to replace the Docker architecture.
* Added transparent Dockerization using `--dockerized` commandline argument, with images also built using Nix.
