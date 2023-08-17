# 2.0.0-b5

* Added `refg::` to documentation
* Fixed issue where "worst clock skew" metrics were aggregated incorrectly
* Fixed issue with referencing files outside the design directory


# 2.0.0-b4

* Updated documentation for `run_subprocess`
* Updated Volare to `0.11.2`
* Fixed a bug with `Toolbox` method memoization
* Unknown key errors only emit a warning now if the key is used as a Variable's
  name *anywhere* linked to OpenLane. This allows using the same config file
  with multiple flows without errors.

# 2.0.0-b3

* Added ability to create reproducible for any step using instance method
  `Step.create_reproducible()`
* Added ability to load and run Step from Config and State JSON files, working
  for both existing step folders and new reproducibles
* Added new CLI- under either the script `openlane.steps` or
  `python3 -m openlane.steps`, exposing the two functionalities above.
* Added internal ability to load a Config without attempting to load the PDK
  configuration data- i.e., only rely on the user's input
* Extended `Meta` objects to support Step ID and OpenLane version.
* Moved tests from source tree to `test/` folder, refactoring as necessary
* Internal `utils` module folded into `common` module, with elements publicly
  documented
* Removed `tcl_reproducible`

# 2.0.0-b2

* Updated Magic to `952b20d`
* Added new variable, `MAGIC_EXT_SHORT_RESISTOR` to `Magic.SpiceExtraction`,
  disabled by default

# 2.0.0-b1

* Added unit testing and coverage reporting for core infrastructure features (80%+)
* Added running unit tests in the CI for different Python versions
* Moved CI designs out-of-tree
* Various documentation improvements
* Common Module
  * Created new TclUtils to handle common Tcl interactions, i.e., evaluating the
    environment and testing
  * Made Tcl environment evaluation no longer rely on the filesystem
  * Made Tcl environment evaluation restore the environment after the fact
  * Moved `Path` from State module to common
  * Moved parsing metric modifiers and such from Toolbox
* Config Module
  * Updated PDK migration script to be a bit more resilient
  * Fixed bug where `meta` did not get copied properly with `Config` copies
  * Rewrote configuration dictionary preprocessor again
* Flow Module
  * Sequential flows now handle duplicate Step IDs by adding a suffix
* Logging Module
  * Logging rewritten to use Python logger with rich handler, the latter of
  which suppressed during unit testing
 * State Module
  * `.save_snapshot()` now also saves a JSON representation of metrics
  * Fixed metric cloning
  * Step Module
  * Report start/end locii also end up in the log file
  * Utils
  * DRC module now uses `.` to separate category layer and rule in name

# 2.0.0-a55

* Updated OpenROAD to `02ea75b`
* Updated Volare to `0.9.2`
* Added guide on updating utilities with Nix

# 2.0.0-a54

* Updated Magic to `0afe4d8`:
```
Corrected an error introduced by the code added recently for support

of command logging, which caused the "select cell <instance>" command
option to become invalid;  this command option is used by the
parameterized cell generator and makes it impossible to edit the
parameterized cells.
```

# 2.0.0-a53

* Reworked Tcl unsafe string escaping to use home-cooked functions instead of
  "shlex"

# 2.0.0-a52

* Added three designs to the gf180mcu test set
* Magic GDS writes now check log for `Calma output error` before proceeding
  further
* Moved constraint variables to PDK
  * `SYNTH_CAP_LOAD` renamed to `OUTPUT_CAP_LOAD`
* Deprecated names for variables now take priority: allows overriding PDK
  variables properly
* Updated Magic to `8b3bb1a`
* Updated PDK to `78b7bc3`
* Updated Volare to `0.8.0` to support zstd-compressed PDKs
* Temporarily removed `manual_macro_placement_test` from the sky130 test set
  pending a weird bug

# 2.0.0-a51

* Updated Netgen to `87d8759`

# 2.0.0-a50

* JSON configuration files with `meta.version: 2` and dictionary configurations
  now both subject to stricter validation
    * Strings no longer automatically converted to lists, dicts, numbers, booleans, et cetera
    * Numbers no longer automatically converted to
    booleans
    * Unrecognized keys throw an error instead of a warning
* Steps now only keep a copy of configuration variables that are either common
  or explicitly declared
    * Explicitly declare global routing variables for resizer steps
    * Explicitly declare MagicStep variables for DRC step
* `CLOCK_PORT` type changed from `Optional[List[str]]` to `Union[str, List[str], None]`
* JSON globs behavior adjusted, now always returns `List` - conversion handled after preprocessing
* Rewrote `resolve.py` as a proper preprocessor
   * Proper recursion into Mappings and Sequences (so refs:: may be resolved in arbitrarily deep objects)
   * Defer most validation and conversion to `Config` object
* Fixed internal issue where `some_of` of a Union with more than two variables of which one is `None` just returns the same Union
* Fixed issue where `expr::` turns results into strings
* `µ`niformity, now all use `U+00B5 MICRO SIGN` 
* Removed default values that `ref::`/`expr::` other variables
* Removed unused variable

# 2.0.0-a49

* Made designs synthesized by Yosys keep their name after `chparam`

# 2.0.0-a48

* Created `openlane.flows.cloup_flow_opts`, which assigns a number of `cloup`
  commandline options to an external function for convenience.
* Moved handling of `last_run` inside `Flow.start`
* Moved handling of volare, setting log level and threadpool count to `cloup_flow_opts`

# 2.0.0-a47

* Update Magic, Netgen, and Yosys
* Made `SYNTH_ELABORATE_ONLY` functional
* Minor internal rearchitecture of `common` and commandline options

# 2.0.0-a46

* Start on API cleanup in preparation for beta
* Common and Logging isolated into own modules
* Improved documentation on various parts of the codebase.
* Delineated `public`, `private` and `protected` class members:
  * If undocumented or starts with `__`, private
  * If decorated with `@openlane.common.protected`, protected
  * Else public
* Class members renamed to reflect the above
* Adjusted documentation generation to use RST and proper titles
* Flow progress bar hooks encapsulated in new `FlowProgressBar` object
  * Old methods still exist, issue a `DeprecationWarning`

## API Breaks

* Top level `import openlane` now only has the version. To get access to `Flow` or `Step`, try `from openlane.flows import Flow`
* `Flow.get`/`Step.get` no longer exist: use `Flow.factory.get`/`Step.factory.get` instead
* `openlane.common.internal` decorator replaced with `openlane.common.protected`
* `Step` objects no longer hold a reference to parent flow
  * `Step.start` now takes `self.step_dir` as a required argument when running non-interactive flows
  * A faster migration method inside a Flow is  `step.start()` -> `self.start_step(step)`

# 2.0.0-a45

* Made Magic DRC report parser more robust, handling multiple rules, etc
* Updated documentation for various related variables
* Fixed bug causing PNR-excluded cells being used during resizer-based OpenROAD steps 

# 2.0.0-a44

* Added support for multiple corners during CTS using the `CTS_CORNERS` variable
* Added support for multiple corners during resizer steps using the `RSZ_CORNERS` variable
* Internally reworked OpenROAD resizer and CTS steps to share a common base class

# 2.0.0-a43

* Added `io_placer` and `manual_macro_placemnt_test` to CI
* Fixed `MAGTYPE` for `Magic.WriteLEF`
* Fixed bug with reading `EXTRA_LEFS` in Magic steps 

# 2.0.0-a42

* Added support for instances to `RSZ_DONT_TOUCH_RX`
* Added support for `RSZ_DONT_TOUCH_LIST` to resizer steps
* `inverter` design used to configure the above two
* Added ignore for `//` key in JSON config files
* Added two new variables for `Yosys.Synthesis`; `SYNTH_DIRECT_WIRE_BUFFERING` and `SYNTH_SPLITNETS`
* Fixed bug with Yosys report parsing
* Fixed issue in `usb_cdc_core` masked by aforementioned bug

# 2.0.0-a41

* Updated Magic to `9b131fa`
* Updated Magic LEF writing script
* Ensured consistency of Tcl script logging prefixes

# 2.0.0-a40

* Fixed a bug with extracting variables from Tcl config files when the variable
  is already set in the environment
* Fixed a bug with saving lib and SDF files
* Fixed `check_antennas.tcl` being mis-named

# 2.0.0-a39

* Added mechanism for subprocesses to write metrics via stdout, `%OL_METRIC{,_I,_F}`, used for OpenSTA
* Added violation summary table to post-PNR STA
* Reworked multi-corner STA: now run across N processes with the step being responsible for aggregation
* Made handling `Infinity` metrics more robust
* Fixed names of various metrics to abide with conventions:
  * `magic__drc_errors` -> `magic__drc_error__count`
  * `magic__illegal__overlaps` -> `magic__illegal_overlap__count`
* Removed splash messages from OpenROAD, OpenSTA

# 2.0.0-a38

* Added full test-suite added to CI
  * Like OpenLane 1, a "fastest test set" runs with every PR and an "extended test set" runs daily
* Added Nix building, intra-CI caching and installation as composite actions
  * Nix derivation now cached intra-CI even if running without access to secrets
  * Fixed issue where channel was mis-named
  * Smoke test on all platforms using `nix-shell`
* Docker image re-implemented: One layer with proper settings for PATH and
  PYTHONPATH
  * Docker image smoke-tested independently of Nix
* Fixed bug with Tcl configurations
* Fixed issue with `Yosys.Synthesis` producing false-positive checks
* Updated various design configs

# 2.0.0-a37

* Added `MAX_TRANSITION_CONSTRAINT` to `base.sdc` (if set)
* Added `MAX_TRANSITION_CONSTRAINT` -> `SYNTH_MAX_TRAN` translation behavior in `base.sdc`
* Removed attempt(s) to calculate a default value for `MAX_TRANSITION_CONSTRAINT` in `all.tcl`, `openroad/cts.tcl` and `yosys/synth.tcl`

# 2.0.0-a36

* Added a commandline option `-j/--jobs` to add a maximum cap on subprocesses.
* Added a global ThreadPoolExecutor object for all subprocesses to `common`.
  * Accessible for external scripts and plugins via `openlane.get_tpe` and `openlane.set_tpe`
* Folded `--list-plugins` into `--version`
* Renamed `ROUTING_CORES` to `DRT_THREADS`
* Removed `RCX_CORES`, step now uses global ThreadPoolExecutor

# 2.0.0-a35

* Revert magic to [`a33d7b7`](https://github.com/RTimothyEdwards/magic/commit/a33d7b78b54d8456769d08236f91f9be31784267),
  last known-good version before a LEF writing bug

# 2.0.0-a34

* Added ability to disable reproducibles on a per-class level
* Updated SDF to support N-corners
* Fixed bug with writing LIB/SDF views

# 2.0.0-a33

* Bump supported PDK to `af34855`
* Rename 3 PDK variables to match OpenLane 1
  * `FP_PDN_RAILS_LAYER` -> `FP_PDN_RAIL_LAYER`
  * `FP_PDN_UPPER_LAYER` -> `FP_PDN_HORIZONTAL_LAYER`
  * `FP_PDN_LOWER_LAYER` -> `FP_PDN_VERTICAL_LAYER`

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
