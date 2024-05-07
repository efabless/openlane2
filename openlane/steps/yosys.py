# Copyright 2023 Efabless Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os
import re
import io
import json
import fnmatch
import textwrap
import subprocess
from decimal import Decimal
from abc import abstractmethod
from typing import List, Literal, Optional, Set, Tuple

from .tclstep import TclStep
from .step import ViewsUpdate, MetricsUpdate, Step

from ..config import Variable, Config
from ..state import State, DesignFormat
from ..logging import debug, verbose, info
from ..common import Path, get_script_dir, Toolbox, TclUtils, process_list_file

starts_with_whitespace = re.compile(r"^\s+.+$")

yosys_cell_rx = r"cell\s+\S+\s+\((\S+)\)"


def _check_any_tristate(
    cells: List[str],
    tristate_patterns: List[str],
):
    for cell in cells:
        for tristate_pattern in tristate_patterns:
            if fnmatch.fnmatch(cell, tristate_pattern):
                return True

    return False


def _parse_yosys_check(
    report: io.TextIOBase,
    tristate_patterns: Optional[List[str]] = None,
    tristate_okay: bool = False,
    elaborate_only: bool = False,
) -> int:
    verbose("Parsing synthesis checks…")
    errors_encountered: int = 0
    last_warning = None
    current_warning = None

    tristate_patterns = tristate_patterns or []

    for line in report:
        if line.startswith("Warning:") or line.startswith("Found and reported"):
            last_warning = current_warning
            current_warning = line
            if last_warning is None:
                continue

            cells = re.findall(yosys_cell_rx, last_warning)

            if elaborate_only and "but has no driver" in last_warning:
                debug("Ignoring undriven cell in elaborate-only mode:")
                debug(last_warning)
            elif tristate_okay and (
                ("tribuf" in last_warning)
                or _check_any_tristate(cells, tristate_patterns)
            ):
                debug("Ignoring tristate-related error:")
                debug(last_warning)
            else:
                debug("Encountered check error:")
                debug(last_warning)
                errors_encountered += 1
        elif (
            starts_with_whitespace.match(line) is not None
            and current_warning is not None
        ):
            current_warning += line
        else:
            pass
    return errors_encountered


def _generate_read_deps(
    config: Config,
    toolbox: Toolbox,
    power_defines: bool = False,
) -> str:
    commands = "set ::_synlig_defines [list]\n"

    synth_defines = [
        f"PDK_{config['PDK']}",
        f"SCL_{config['STD_CELL_LIBRARY']}\"",
        "__openlane__",
        "__pnr__",
    ]
    synth_defines += (
        config.get("VERILOG_DEFINES") or []
    )  # VERILOG_DEFINES not defined for VHDLSynthesis
    for define in synth_defines:
        commands += f"verilog_defines {TclUtils.escape(f'-D{define}')}\n"
        commands += (
            f"lappend ::_synlig_defines {TclUtils.escape(f'+define+{define}')}\n"
        )

    scl_lib_list = toolbox.filter_views(config, config["LIB"])

    if power_defines:
        if power_define := config.get(
            "VERILOG_POWER_DEFINE"
        ):  # VERILOG_POWER_DEFINE not defined for VHDLSynthesis
            commands += f"verilog_defines {TclUtils.escape(f'-D{power_define}')}\n"
            commands += f"lappend ::_synlig_defines {TclUtils.escape(f'+define+{power_define}')}\n"

    # Try your best to use powered blackbox models if power_defines is true
    if power_defines and config["CELL_VERILOG_MODELS"] is not None:
        scl_blackbox_models = toolbox.create_blackbox_model(
            frozenset(config["CELL_VERILOG_MODELS"]),
            frozenset(["USE_POWER_PINS"]),
        )
        commands += f"read_verilog -sv -lib {scl_blackbox_models}\n"
    else:
        # Fall back to scl_lib_list if you cant
        for lib in scl_lib_list:
            lib_str = TclUtils.escape(str(lib))
            commands += (
                f"read_liberty -lib -ignore_miss_dir -setattr blackbox {lib_str}\n"
            )

    excluded_cells: Set[str] = set(config["EXTRA_EXCLUDED_CELLS"] or [])
    excluded_cells.update(process_list_file(config["SYNTH_EXCLUDED_CELL_FILE"]))
    excluded_cells.update(process_list_file(config["PNR_EXCLUDED_CELL_FILE"]))

    lib_synth = toolbox.remove_cells_from_lib(
        frozenset([str(lib) for lib in scl_lib_list]),
        excluded_cells=frozenset(excluded_cells),
    )
    commands += f"set ::env(SYNTH_LIBS) {TclUtils.escape(TclUtils.join(lib_synth))}\n"

    verilog_include_args = []
    if dirs := config.get("VERILOG_INCLUDE_DIRS"):
        for dir in dirs:
            verilog_include_args.append(f"-I{dir}")

    # Priorities from higher to lower
    format_list = (
        [
            DesignFormat.VERILOG_HEADER,
            DesignFormat.POWERED_NETLIST,
            DesignFormat.NETLIST,
            DesignFormat.LIB,
        ]
        if power_defines
        else [
            DesignFormat.VERILOG_HEADER,
            DesignFormat.NETLIST,
            DesignFormat.POWERED_NETLIST,
            DesignFormat.LIB,
        ]
    )
    for view, format in toolbox.get_macro_views_by_priority(config, format_list):
        view_escaped = TclUtils.escape(str(view))
        if format == DesignFormat.LIB:
            commands += (
                f"read_liberty -lib -ignore_miss_dir -setattr blackbox {view_escaped}\n"
            )
        else:
            commands += f"read_verilog -sv -lib {TclUtils.join(verilog_include_args)} {view_escaped}\n"

    if libs := config.get("EXTRA_LIBS"):
        for lib in libs:
            lib_str = TclUtils.escape(str(lib))
            commands += (
                f"read_liberty -lib -ignore_miss_dir -setattr blackbox {lib_str}\n"
            )

    if models := config["EXTRA_VERILOG_MODELS"]:
        for model in models:
            model_str = TclUtils.escape(str(model))
            commands += f"read_verilog -sv -lib {TclUtils.join(verilog_include_args)} {model_str}\n"

    return commands


verilog_rtl_cfg_vars = [
    Variable(
        "VERILOG_FILES",
        List[Path],
        "The paths of the design's Verilog files.",
    ),
    Variable(
        "VERILOG_DEFINES",
        Optional[List[str]],
        "Preprocessor defines for input Verilog files.",
        deprecated_names=["SYNTH_DEFINES"],
    ),
    Variable(
        "VERILOG_POWER_DEFINE",
        str,
        "Specifies the name of the define used to guard power and ground connections in the input RTL.",
        deprecated_names=["SYNTH_USE_PG_PINS_DEFINES", "SYNTH_POWER_DEFINE"],
        default="USE_POWER_PINS",
    ),
    Variable(
        "VERILOG_INCLUDE_DIRS",
        Optional[List[str]],
        "Specifies the Verilog `include` directories.",
    ),
    Variable(
        "USE_SYNLIG",
        bool,
        "Use the Synlig plugin to process files, which has better SystemVerilog parsing capabilities but may not be compatible with all Yosys commands and attributes.",
        default=False,
    ),
    Variable(
        "SYNLIG_DEFER",
        bool,
        "Uses -defer flag when reading files the Synlig plugin, which may improve performance by reading each file separately, but is experimental.",
        default=False,
    ),
]


class YosysStep(TclStep):
    config_vars = [
        Variable(
            "SYNTH_LATCH_MAP",
            Optional[Path],
            "A path to a file containing the latch mapping for Yosys.",
            pdk=True,
        ),
        Variable(
            "SYNTH_TRISTATE_MAP",
            Optional[Path],
            "A path to a file containing the tri-state buffer mapping for Yosys.",
            deprecated_names=["TRISTATE_BUFFER_MAP"],
            pdk=True,
        ),
        Variable(
            "SYNTH_CSA_MAP",
            Optional[Path],
            "A path to a file containing the carry-select adder mapping for Yosys.",
            deprecated_names=["CARRY_SELECT_ADDER_MAP"],
            pdk=True,
        ),
        Variable(
            "SYNTH_RCA_MAP",
            Optional[Path],
            "A path to a file containing the ripple-carry adder mapping for Yosys.",
            deprecated_names=["RIPPLE_CARRY_ADDER_MAP"],
            pdk=True,
        ),
        Variable(
            "SYNTH_FA_MAP",
            Optional[Path],
            "A path to a file containing the full adder mapping for Yosys.",
            deprecated_names=["FULL_ADDER_MAP"],
            pdk=True,
        ),
        Variable(
            "SYNTH_MUX_MAP",
            Optional[Path],
            "A path to a file containing the mux mapping for Yosys.",
            pdk=True,
        ),
        Variable(
            "SYNTH_MUX4_MAP",
            Optional[Path],
            "A path to a file containing the mux4 mapping for Yosys.",
            pdk=True,
        ),
        Variable(
            "USE_LIGHTER",
            bool,
            "Activates Lighter, an experimental plugin that attempts to optimize clock-gated flip-flops.",
            default=False,
        ),
        Variable(
            "LIGHTER_DFF_MAP",
            Optional[Path],
            "An override to the custom DFF map file provided for the given SCL by Lighter.",
        ),
    ]

    def get_command(self) -> List[str]:
        script_path = self.get_script_path()
        return ["yosys", "-c", script_path]

    @abstractmethod
    def get_script_path(self) -> str:
        pass

    def run(self, state_in: State, **kwargs) -> Tuple[ViewsUpdate, MetricsUpdate]:
        power_defines = False
        if "power_defines" in kwargs:
            power_defines = kwargs.pop("power_defines")

        kwargs, env = self.extract_env(kwargs)

        _deps_script = os.path.join(self.step_dir, "_deps.tcl")

        with open(_deps_script, "w") as f:
            f.write(
                _generate_read_deps(
                    self.config, self.toolbox, power_defines=power_defines
                )
            )

        env["_DEPS_SCRIPT"] = _deps_script

        return super().run(state_in, env=env, **kwargs)


@Step.factory.register()
class JsonHeader(YosysStep):
    id = "Yosys.JsonHeader"
    name = "Generate JSON Header"
    long_name = "Generate JSON Header"

    inputs = []
    outputs = [DesignFormat.JSON_HEADER]

    def get_script_path(self):
        return os.path.join(get_script_dir(), "yosys", "json_header.tcl")

    config_vars = YosysStep.config_vars + verilog_rtl_cfg_vars

    def run(self, state_in: State, **kwargs) -> Tuple[ViewsUpdate, MetricsUpdate]:
        return super().run(state_in, power_defines=True, **kwargs)


class SynthesisCommon(YosysStep):
    inputs = []  # The input RTL is part of the configuration
    outputs = [DesignFormat.NETLIST]

    config_vars = YosysStep.config_vars + [
        Variable(
            "SYNTH_CHECKS_ALLOW_TRISTATE",
            bool,
            "Ignore multiple-driver warnings if they are connected to tri-state buffers on a best-effort basis.",
            default=True,
        ),
        Variable(
            "SYNTH_AUTONAME",
            bool,
            "Generates names for netlist instances. This results in instance names that can be extremely long, but are more human-readable.",
            default=False,
        ),
        Variable(
            "SYNTH_STRATEGY",
            Literal[
                "AREA 0",
                "AREA 1",
                "AREA 2",
                "AREA 3",
                "DELAY 0",
                "DELAY 1",
                "DELAY 2",
                "DELAY 3",
                "DELAY 4",
            ],
            "Strategies for abc logic synthesis and technology mapping. AREA strategies usually result in a more compact design, while DELAY strategies usually result in a design that runs at a higher frequency. Please note that there is no way to know which strategy is the best before trying them.",
            default="AREA 0",
        ),
        Variable(
            "SYNTH_ABC_BUFFERING",
            bool,
            "Enables `abc` cell buffering.",
            default=False,
            deprecated_names=["SYNTH_BUFFERING"],
        ),
        Variable(
            "SYNTH_ABC_LEGACY_REFACTOR",
            bool,
            "Replaces the ABC command `drf -l` with `refactor` which matches older versions of OpenLane but is more unstable.",
            default=False,
        ),
        Variable(
            "SYNTH_ABC_LEGACY_REWRITE",
            bool,
            "Replaces the ABC command `drw -l` with `rewrite` which matches older versions of OpenLane but is more unstable.",
            default=False,
        ),
        Variable(
            "SYNTH_DIRECT_WIRE_BUFFERING",
            bool,
            "Enables inserting buffer cells for directly connected wires.",
            default=True,
            deprecated_names=["SYNTH_BUFFER_DIRECT_WIRES"],
        ),
        Variable(
            "SYNTH_SPLITNETS",
            bool,
            "Splits multi-bit nets into single-bit nets. Easier to trace but may not be supported by all tools.",
            default=True,
        ),
        Variable(
            "SYNTH_SIZING",
            bool,
            "Enables `abc` cell sizing (instead of buffering).",
            default=False,
        ),
        Variable(
            "SYNTH_NO_FLAT",
            bool,
            "A flag that disables flattening the hierarchy during synthesis, only flattening it after synthesis, mapping and optimizations.",
            default=False,
        ),
        Variable(
            "SYNTH_SHARE_RESOURCES",
            bool,
            "A flag that enables yosys to reduce the number of cells by determining shareable resources and merging them.",
            default=True,
        ),
        Variable(
            "SYNTH_ADDER_TYPE",
            Literal["YOSYS", "FA", "RCA", "CSA"],
            "Adder type to which the $add and $sub operators are mapped to.  Possible values are `YOSYS/FA/RCA/CSA`; where `YOSYS` refers to using Yosys internal adder definition, `FA` refers to full-adder structure, `RCA` refers to ripple carry adder structure, and `CSA` refers to carry select adder.",
            default="YOSYS",
        ),
        Variable(
            "SYNTH_EXTRA_MAPPING_FILE",
            Optional[Path],
            "Points to an extra techmap file for yosys that runs right after yosys `synth` before generic techmap.",
        ),
        Variable(
            "SYNTH_PARAMETERS",
            Optional[List[str]],
            "Key-value pairs to be `chparam`ed in Yosys, in the format `key1=value1`.",
        ),
        Variable(
            "SYNTH_ELABORATE_ONLY",
            bool,
            '"Elaborate" the design only without attempting any logic mapping. Useful when dealing with structural Verilog netlists.',
            default=False,
        ),
        Variable(
            "SYNTH_ELABORATE_FLATTEN",
            bool,
            "If `SYNTH_ELABORATE_ONLY` is specified, this variable controls whether or not the top level should be flattened.",
            default=True,
            deprecated_names=["SYNTH_FLAT_TOP"],
        ),
        # Variable(
        #     "SYNTH_SDC_FILE",
        #     Optional[Path],
        #     "Specifies the SDC file read during all Synthesis steps",
        # ),
    ]

    def get_script_path(self):
        return os.path.join(get_script_dir(), "yosys", "synthesize.tcl")

    def run(self, state_in: State, **kwargs) -> Tuple[ViewsUpdate, MetricsUpdate]:
        kwargs, env = self.extract_env(kwargs)

        if self.config["USE_LIGHTER"]:
            lighter_dff_map = self.config["LIGHTER_DFF_MAP"]
            if lighter_dff_map is None:
                scl = self.config["STD_CELL_LIBRARY"]
                try:
                    raw = subprocess.check_output(
                        ["lighter_files", scl], encoding="utf8"
                    )
                    files = raw.strip().splitlines()
                    lighter_dff_map = Path(files[0])
                except FileNotFoundError:
                    self.warn(
                        "Lighter not found or not set up with OpenLane: If you're using a manual Lighter install, try setting LIGHTER_DFF_MAP explicitly."
                    )
                except subprocess.CalledProcessError:
                    self.warn(f"{scl} not supported by Lighter.")

            env["_LIGHTER_DFF_MAP"] = lighter_dff_map

        # env["_SDC_IN"] = (
        #     self.config["SYNTH_SDC_FILE"] or self.config["FALLBACK_SDC_FILE"]
        # )

        views_updates, metric_updates = super().run(state_in, env=env, **kwargs)

        stats_file = os.path.join(self.step_dir, "reports", "stat.json")
        stats_str = open(stats_file).read()
        stats = json.loads(stats_str, parse_float=Decimal)

        metric_updates = {}
        metric_updates["design__instance__count"] = stats["design"]["num_cells"]
        if chip_area := stats["design"].get("area"):  # needs nonzero area
            metric_updates["design__instance__area"] = chip_area

        cells = stats["design"]["num_cells_by_type"]
        safe = ["$assert"]
        unmapped_cells = [
            cells[y] for y in cells.keys() if y not in safe and y.startswith("$")
        ]
        metric_updates["design__instance_unmapped__count"] = sum(unmapped_cells)

        check_error_count_file = os.path.join(
            self.step_dir, "reports", "pre_synth_chk.rpt"
        )
        metric_updates["synthesis__check_error__count"] = 0
        if os.path.exists(check_error_count_file):
            metric_updates["synthesis__check_error__count"] = _parse_yosys_check(
                open(check_error_count_file),
                self.config["TRISTATE_CELLS"],
                self.config["SYNTH_CHECKS_ALLOW_TRISTATE"],
                self.config["SYNTH_ELABORATE_ONLY"],
            )

        return views_updates, metric_updates


@Step.factory.register()
class Synthesis(SynthesisCommon):
    """
    Performs synthesis and technology mapping on Verilog RTL files
    using Yosys and ABC, emitting a netlist.

    Some metrics will also be extracted and updated, namely:

    * ``design__instance__count``
    * ``design__instance_unmapped__count``
    * ``design__instance__area``
    """

    id = "Yosys.Synthesis"
    name = "Synthesis"

    config_vars = SynthesisCommon.config_vars + verilog_rtl_cfg_vars


@Step.factory.register()
class VHDLSynthesis(SynthesisCommon):
    """
    Performs synthesis and technology mapping on VHDL files
    using Yosys, GHDL and ABC, emitting a netlist.

    Some metrics will also be extracted and updated, namely:

    * ``design__instance__count``
    * ``design__instance_unmapped__count``
    * ``design__instance__area``
    """

    id = "Yosys.VHDLSynthesis"
    name = "Synthesis (VHDL)"

    config_vars = SynthesisCommon.config_vars + [
        Variable(
            "VHDL_FILES",
            List[Path],
            "The paths of the design's VHDL files.",
        ),
    ]


@Step.factory.register()
class EQY(YosysStep):
    id = "Yosys.EQY"
    name = "Equivalence Check"
    long_name = "RTL/Netlist Equivalence Check"

    inputs = [DesignFormat.NETLIST]
    outputs = []

    config_vars = YosysStep.config_vars + [
        Variable(
            "EQY_SCRIPT",
            Optional[Path],
            "An optional override for the automatically generated EQY script for more complex designs.",
        ),
        Variable(
            "MACRO_PLACEMENT_CFG",
            Optional[Path],
            "This step will warn if this deprecated variable is used, as it indicates Macros are used without the new Macro object.",
        ),
        Variable(
            "EQY_FORCE_ACCEPT_PDK",
            bool,
            "Attempt to run EQY even if the PDK's Verilog models are supported by this step. Will likely result in a failure.",
            default=False,
        ),
    ]

    def get_command(self) -> List[str]:
        script_path = self.get_script_path()
        work_dir = os.path.join(self.step_dir, "scratch")
        return ["eqy", "-f", script_path, "-d", work_dir]

    def get_script_path(self) -> str:
        return os.path.join(self.step_dir, f"{self.config['DESIGN_NAME']}.eqy")

    def run(self, state_in: State, **kwargs) -> Tuple[ViewsUpdate, MetricsUpdate]:
        processed_pdk = os.path.join(self.step_dir, "formal_pdk.v")

        if self.config["PDK"].startswith("sky130A"):
            subprocess.check_call(
                [
                    "eqy.formal_pdk_proc",
                    "--output",
                    processed_pdk,
                ]
                + [str(model) for model in self.config["CELL_VERILOG_MODELS"]]
            )
        elif self.config["EQY_FORCE_ACCEPT_PDK"]:
            subprocess.check_call(
                ["iverilog", "-E", "-o", processed_pdk, "-DFUNCTIONAL"]
                + [str(model) for model in self.config["CELL_VERILOG_MODELS"]]
            )
        else:
            info(
                f"PDK {self.config['PDK']} is not supported by the EQY step. Skipping…"
            )
            return {}, {}

        with open(self.get_script_path(), "w", encoding="utf8") as f:
            if eqy_script := self.config["EQY_SCRIPT"]:
                for line in open(eqy_script, "r", encoding="utf8"):
                    f.write(line)
            else:
                script = textwrap.dedent(
                    """
                    [script]
                    {dep_commands}
                    blackbox

                    [gold]
                    read_verilog -formal -sv {files}

                    [gate]
                    read_verilog -formal -sv {processed_pdk} {nl}

                    [script]
                    hierarchy -top {design_name}
                    proc
                    prep -top {design_name} -flatten

                    memory -nomap
                    async2sync

                    [gold]
                    write_verilog {step_dir}/gold.v
                    
                    [gate]
                    write_verilog {step_dir}/gate.v

                    [strategy sat]
                    use sat
                    depth 5

                    [strategy pdr]
                    use sby
                    engine abc pdr -rfi

                    [strategy bitwuzla]
                    use sby
                    depth 2
                    engine smtbmc bitwuzla
                    """
                ).format(
                    design_name=self.config["DESIGN_NAME"],
                    dep_commands=_generate_read_deps(self.config, self.toolbox),
                    files=TclUtils.join(
                        [str(file) for file in self.config["VERILOG_FILES"]]
                    ),
                    nl=state_in[DesignFormat.NETLIST],
                    processed_pdk=processed_pdk,
                    step_dir=self.step_dir,
                )
                f.write(script)

        return super().run(state_in, **kwargs)
