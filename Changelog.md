# 2.0.0-a17
* Fixed a crash when the SCL is specified via command-line.
# 2.0.0-a16

* Reimplement DRC database using `lxml`
* Makefile `venv` creation updated
* Misc. aesthetic bugfixes for sequential flows

# 2.0.0-a14

* Add steps to extract, preserve and check power connections:
    * `Checker.DisconnectedPins`: Checker for `ReportDisconnectedPins`.
    * `Odb.ReportDisconnectedPins`: Report disconnected instance pins in a design.
    * `Yosys.JsonHeader`: RTL to a JSON Header.
    * `Odb.SetPowerConnections`: Uses JSON generated in `Yosys/JsonHeader` and module information in Odb to add global connections for macros in a design.
* Add `IGNORE_DISCONNECTED_MODULES` as a PDK variable, as some cells need to be ignored.
* Rename `SYNTH_USE_PG_PINS_DEFINES` to `SYNTH_POWER_DEFINE`.
* Rename `CHECK_UNMAPPED_CELLS` to `QUIT_ON_UNMAPPED_CELLS`.
* Rename various metrics.
* Change various configuration variables for included `caravel_upw` design.
* Fix `DIODE_INSERTION_STRATEGY` translations
* Allow overriding from CLI when using Tcl configuration files.


# 2.0.0-a13

## Documentation
* Built-in flows now have full generated documentation akin to steps.
* Built-in steps now document their inputs, outputs and each built-in step has a human-readable text description.
* Rewrite the RTL-to-GDS guides.
* Add an architectural overview of OpenLane 2+.
* Document pin config file format.
* Add guides on writing custom flows AND custom steps.
* Add a migration guide from OpenLane 1.
* Port contributor's guide from OpenLane 1.
* Removed default values from Jupyter Notebook.

## Functional
* `Config` is now immutable, `.copy()` can now take kwargs to override one or more values.
* `TapDecapInsertion` -> `TapEndcapInsertion` (more accurate)
* Dropped requirement for description to match between two variables to be "equal:" It is sometimes favorable to have a slightly different description in another step.
* `OpenInKLayout`/`OpenInOpenROAD` turned into sequential flows with one step instead of hacks.
* Fixed a bug where `OpenInKLayout` would exit instantly.
* Updated and fixed `Optimizing` demo flow, as well as delisting it.
* Port https://github.com/The-OpenROAD-Project/OpenLane/pull/1723 to OpenLane 2.
* Remove `Odb.ApplyDEFTemplate` from default flow.

# 2.0.0-a12

* Fixes a bug where if OpenLane is invoked from the same directory as the design,
  KLayout stream-outs would break.

# 2.0.0-a11

* Update OpenROAD, Add ABC patch to use system zlib
* Adds SDC files as an input to `OpenROADStep`, `NetlistSTA` and `LayoutSTA` steps
* Add `sdc_reader.tcl`: a hook script for reading in SDC files while handling deprecated variables
* Replace deprecated variables in base.sdc
    * Properly use TIME_DERATING_CONSTRAINT in base.sdc 
    * Properly use SYNTH_DRIVING_CELL in base.sdc
    * Properly use SYNTH_CLK_DRIVING_CELL in base.sdc

# 2.0.0-a10

* Add `wrapper.tcl` to capture errors in Magic scripts.
* Fix instances of a deprecated variable was used in Magic scripts.

# 2.0.0-a9

* Add port diode insertion script.
* Fix formula for calculating `FP_TARGET_DENSITY_PCT`.

# 2.0.0-a8

* Update `volare` dependency.
* Update `magic` version + make `magic` nix derivation more resilient.

# 2.0.0-a7

* Add the custom diode insertion script as a `Step` (disabled by default).
* `Flow` objects are now passed explicitly to child `Step` objects, removing earlier stack inspection code.
* `flow_config_vars` now only affect steps running inside a Flow.

# 2.0.0-a6

* Add validation on step exit.

# 2.0.0-a5

* Fix a small path resolution issue.

# 2.0.0-a4

* Add basic CI that builds for Linux, macOS and Docker
* Various improvements to Dockerization so that `openlane --dockerized` can run on Windows

# 2.0.0-a3

* Fixed an issue where KLayout scripts exited silently.

# 2.0.0-a2

* Handle `PDK_ROOT`, `PDK` and `STD_CELL_LIBRARY` environment variables.
* Unify environment inspection by using `os.environ`- eliminated getenv
* KLayout scripts no longer accept environment variables.
* Updated Docker images for consistency.
* Added ReadTheDocs configuration.

# 2.0.0-a1

* Update smoke test
* Fix bug with default variables

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
