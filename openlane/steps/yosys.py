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
import subprocess
import textwrap
from decimal import Decimal
from abc import abstractmethod
from typing import List, Literal, Optional, Tuple

from .tclstep import TclStep
from .step import ViewsUpdate, MetricsUpdate, Step

from ..config import Variable, Config
from ..state import State, DesignFormat
from ..logging import debug, verbose, info, warn
from ..common import Path, get_script_dir, Toolbox, TclUtils

starts_with_whitespace = re.compile(r"^\s+.+$")


def _parse_yosys_check(
    report: io.TextIOBase,
    tristate_okay: bool = False,
) -> int:
    verbose("Parsing synthesis checks…")
    errors_encountered: int = 0
    current_warning = None

    for line in report:
        if line.startswith("Warning:") or line.startswith("Found and reported"):
            if current_warning is not None:
                if tristate_okay and "tribuf" in current_warning:
                    debug("Ignoring tristate-related error:")
                    debug(current_warning)
                else:
                    debug("Encountered check error:")
                    debug(current_warning)
                    errors_encountered += 1
            current_warning = line
        elif (
            starts_with_whitespace.match(line) is not None
            and current_warning is not None
        ):
            current_warning += line
        else:
            pass
    return errors_encountered


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
        Optional[str],
        "Specifies the name of the define used to guard power and ground connections",
        deprecated_names=["SYNTH_USE_PG_PINS_DEFINES", "SYNTH_POWER_DEFINE"],
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
            "A path to a file contianing the latch mapping for Yosys.",
            pdk=True,
        ),
        Variable(
            "SYNTH_TRISTATE_MAP",
            Optional[Path],
            "A path to a file contianing the tri-state buffer mapping for Yosys.",
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
        kwargs, env = self.extract_env(kwargs)

        lib_list = [
            str(e) for e in self.toolbox.filter_views(self.config, self.config["LIB"])
        ]
        lib_synth = self.toolbox.remove_cells_from_lib(
            frozenset(lib_list),
            excluded_cells=frozenset(
                [
                    str(self.config["SYNTH_EXCLUSION_CELL_LIST"]),
                    str(self.config["PNR_EXCLUSION_CELL_LIST"]),
                ]
            ),
            as_cell_lists=True,
        )

        env["SYNTH_LIBS"] = " ".join(lib_synth)
        env["FULL_LIBS"] = " ".join(lib_list)

        macro_libs = self.toolbox.get_macro_views(
            self.config,
            DesignFormat.LIB,
        )
        if len(macro_libs) != 0:
            env["MACRO_LIBS"] = " ".join([str(lib) for lib in macro_libs])

        macro_nls = self.toolbox.get_macro_views(
            self.config,
            DesignFormat.NETLIST,
            unless_exist=DesignFormat.LIB,
        )
        if len(macro_nls) != 0:
            env["MACRO_NLS"] = " ".join([str(nl) for nl in macro_nls])

        return super().run(state_in, env=env, **kwargs)


@Step.factory.register()
class JsonHeader(YosysStep):
    id = "Yosys.JsonHeader"
    inputs = []
    outputs = [DesignFormat.JSON_HEADER]

    def get_script_path(self):
        return os.path.join(get_script_dir(), "yosys", "json_header.tcl")

    config_vars = YosysStep.config_vars + verilog_rtl_cfg_vars


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
                "AREA 4",
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
            default=True,
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
                    warn(
                        "Lighter not found or not set up with OpenLane: If you're using a manual Lighter install, try setting LIGHTER_DFF_MAP explicitly."
                    )
                except subprocess.CalledProcessError:
                    warn(f"{scl} not supported by Lighter.")

            env["_lighter_dff_map"] = lighter_dff_map

        views_updates, metric_updates = super().run(state_in, **kwargs)

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
                self.config["SYNTH_CHECKS_ALLOW_TRISTATE"],
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


def _generate_read_deps(
    config: Config,
    toolbox: Toolbox,
    power_defines: bool = False,
    include_scls: bool = True,
) -> str:
    commands = ""

    if synth_defines := config["VERILOG_DEFINES"]:
        for define in synth_defines:
            flag = TclUtils.escape(f"-D{define}")
            commands += f"verilog_defines {flag}\n"

    if power_defines:
        if define := config["VERILOG_POWER_DEFINE"]:
            flag = TclUtils.escape(f"-D{define}")
            commands += f"verilog_defines {flag}"

    for lib in toolbox.filter_views(config, config["LIB"]):
        lib_str = TclUtils.escape(str(lib))
        commands += f"read_liberty -lib -ignore_miss_dir -setattr blackbox {lib_str}\n"

    for lib in toolbox.get_macro_views(config, DesignFormat.LIB):
        lib_str = TclUtils.escape(str(lib))
        commands += f"read_liberty -lib -ignore_miss_dir -setattr blackbox {lib_str}\n"

    verilog_include_args = []
    if dirs := config["VERILOG_INCLUDE_DIRS"]:
        for dir in dirs:
            verilog_include_args.append(f"-I{dir}")

    leftover_macro_nls = toolbox.get_macro_views(
        config,
        DesignFormat.NETLIST,
        unless_exist=DesignFormat.LIB,
    )
    for nl in leftover_macro_nls:
        nl_str = TclUtils.escape(str(nl))
        commands += (
            f"read_verilog -sv -lib {TclUtils.join(verilog_include_args)} {nl_str}\n"
        )

    if models := config["EXTRA_VERILOG_MODELS"]:
        for model in models:
            model_str = TclUtils.escape(str(model))
            commands += f"read_verilog -sv -lib {TclUtils.join(verilog_include_args)} {model_str}\n"

    return commands


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
