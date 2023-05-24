# 2.0.0-a32

* Better adherence to class structure and mutability principles
  * Create `GenericDict`, `GenericImmutableDict` to better handle immutable objects, i.e. `State`, `Config`
  * `State`, `Config` made immutable post-construction
    * Various rewrites to accomodate that
  * `Step`:
    * `.run`:
      * No longer has any default implementation
      * Is expected to return a tuple of **views updates** and **metrics updates** which are then applied to copies by `.start` to meet mutability requirements
    * `.start`:
      * Handles input checking
      * Handles creating new `State` object based on deltas
  * `Flow`
    * Stateful variables for `.start`, `.run`, and other internal methods made private
    * `.start` now only returns the final state object
    * Intermediate steps stored in `self.step_dir`
    * `self.step_dir` and other "mutations" to Flow object have 
      no effect on future `.start()` invocations, which are (more or less) idempotent
  * Remove `ConfigBuilder` and fold methods into `Config`
* Added `make host-docs` to Makefile

# 2.0.0-a31

* Replace OpenSTA binary name check with an environment variable, `OPENSTA`

# 2.0.0-a30

* Added ability to use `--dockerized` without further arguments to drop into a shell
* Reimplemented `--dockerized` - needs to be the first argument provided
* Reimplemented `--smoke-test` to not use a subprocess
  * `--smoke-test` doesn't attempt to handle `--dockerized` on its own anymore
* Fixed permissions bug when running a smoke test from a read-only filesystem
* Fixed race condition for temporary directories on macOS (and presumably Windows)

# 2.0.0-a29

* Added run-time type checkers for `SequentialFlow` `Substitute` dictionary
* Folded `init_with_config` into constructor and deprecate it
* Fixed `SequentialFlow` step substitution bug by moving variable compilation to
  instance instead of class

# 2.0.0-a28

* Added missing macro orientations
* Added missing `PDN_CFG` configuration variable
* Fixed crash when defining `SYNTH_READ_BLACKBOX_LIB`
* Streamlined all `read` messages in OpenROAD scripts and macro-related `read`
  messages in Yosys scripts.
* Cleaned up `YosysStep` hierarchy
* Cleaned up `synthesize.tcl`

> Thanks [@smunaut](https://github.com/smunaut) for the bug reports!

# 2.0.0-a27

* Added `cloup` library for better argument grouping/prettier `--help` with click
* Added ability to substitute steps with a certain `id` in a `SequentialFlow`
  with other Step classes
* Added `--only`, `--skip` to commandline interface for `SequentialFlow`s
* Changed processing of how `--from` and `--to` are done in `SequentialFlow`s
* Better delineation of class vs. instance variables in documentation
* Type checker now also checks functions without typed headers
* Fixed minor bugs with `Decimal` serialization and deserialization
* Class/step registry now case-insensitive
* Moved documentation dependencies to separate requirements file
* Removed `jupyter` from `requirements_dev.txt`- too many dependencies and can
  just be installed with `pip install jupyter`
* Various documentation improvements and fixes

# 2.0.0-a26

* Yosys steps now read macro netlists as a black-box if applicable
* Renamed STA steps to avoid ambiguity

# 2.0.0-a25

* Made optional/default handling more straightforward to fix issue where
  the default value of an Optional is not None.
* Fixed config var inheritance issue for `OpenROAD.ParasiticsSTA`

# 2.0.0-a24

* Add support for gf180mcuC to PDK monkey-patch procedure
* Update some PDK variables to be optional: `GPIO_PADS_LEF`, `IGNORE_DISCONNECTED_MODULES`
* Remove unused PDK variable: `CELL_CLK_PORT`

# 2.0.0-a23

* Added warning on multiple clocks in `base.sdc`
* Added usage of translation hook for SDC scripts
    * Folded `sdc_reader.tcl` into `io.tcl`
* Fixed calculation issue with I/O delays in `base.sdc`
* Fixed SPEF read invocation to include instance path
* Renamed multiple functions in `io.tcl` for clarity and to avoid aliasing
  Tcl built-in functions
* Tcl reproducibles now add entire environment delta vs. just "extracted" variables
    * Better handling of objects inside the design directory
    
# 2.0.0-a22

* Fixed a bug with initializing configurations using dictionaries.
* Added exception message for `InvalidConfig`.

# 2.0.0-a21

* Created a (very) rudimentary plugin system
    * Add ability to list detected plugins with flag `--list-plugins`
* Fixed a problem with reading SPEF files for macros
* Various documentation updates

# 2.0.0-a20

* Created a `Macro` definition object to replace a litany of variables.
    * `libs`, `spefs` and `sdf` files now use wildcards as keys, which will be
    matched against timing corners for loading, i.e., a SPEF with key `nom_*` will
    match timing corner `nom_tt_025C_1V80`.
        * This has been applied to PDK lib files, RCX rulesets and technology LEF
        files as well.
        * `Toolbox` object now has methods for matching the proper LIB/SPEF files.
* PDKs now list a `DEFAULT_CORNER` for picking LIB files as well as a list of
  `STA_TIMING` corners. 
* Expanded the range of valid types for `Variable`: these new classes are
  supported, all with theoretically infinite nesting:
    * `Dict`
    * `Union`
    * `Literal`
* `State` rewritten to support nested dictionaries and type annotations.
    * (Subclass of `Mapping`- Python 3.8 does not support subscripting `UserDict`. Yep.)
* Created a `config.json` for the caravel_upw example for testing purposes.
* Updated Magic, add new patch for Clang
* `self.state_in` is now always a future for consistency, but `run()` now takes
  a `state_in` which is guaranteed to be resolved.
* `EXTRA_LEFS`, `EXTRA_LIBS`, etc kept as a fallback for consistency.
* Remove `STA_PRE_CTS`- STA now always propagates clocks

# 2.0.0-a19

* Created new metric `synthesis__check_error__count` with a corresponding Checker, with said Checker being the new executor of the `QUIT_ON_SYNTH_CHECKS` variable
    * Check report parser imported from OpenLane 1
* Created `SYNTH_CHECKS_ALLOW_TRISTATE` to exclude unmapped tribufs from previous metric.
* Created new metric `design__xor_difference__count` with a corresponding Checker to flag a deferred error on XOR differences.
* Fixed a few typos.

# 2.0.0-a18

* Updated the smoke test to support PDK downloads to a different directory.
* Updated config builder to resolve the PDK root much earlier to avoid an issue where a crash would affect the issue reproducible.
* Updated `SYNTH_READ_BLACKBOX_LIB` to read the full `LIB` variable instead of `LIB_SYNTH`, which also fixes a crash when reading JSON headers.
* Updated post-GRT resizer timing script to re-run GRT before the repair: see https://github.com/The-OpenROAD-Project/OpenROAD/issues/3155
* Added a "yosys proc" to the JSON header generator (thanks @smnaut)
* Fixed a bug where random equidistant mode did not work for OpenROAD IO placer.

# 2.0.0-a17

* Fixed a crash when the SCL is specified via command-line.
* Fixed a changelog merge nightmare.

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
