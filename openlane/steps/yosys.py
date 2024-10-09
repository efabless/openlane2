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
import io
import os
import shutil
import textwrap
import subprocess
from abc import abstractmethod
from typing import List, Literal, Optional, Set, Tuple

from .tclstep import TclStep
from .step import ViewsUpdate, MetricsUpdate, Step
from .pyosys import JsonHeader, verilog_rtl_cfg_vars, Synthesis, VHDLSynthesis

from ..config import Variable, Config
from ..state import State, DesignFormat
from ..logging import info
from ..common import Path, Toolbox, TclUtils, process_list_file

# Re-export for back-compat
JsonHeader
Synthesis
VHDLSynthesis


# This is now only used by EQY since we moved our Yosys scripts to Python.
def _generate_read_deps(
    config: Config,
    toolbox: Toolbox,
    power_defines: bool = False,
    tcl: bool = True,
) -> str:
    commands = ""

    synth_defines = [
        f"PDK_{config['PDK']}",
        f"SCL_{config['STD_CELL_LIBRARY']}",
        "__openlane__",
        "__pnr__",
    ]
    synth_defines += (
        config.get("VERILOG_DEFINES") or []
    )  # VERILOG_DEFINES not defined for VHDLSynthesis
    if tcl:
        commands += "set ::_synlig_defines [list]\n"
    for define in synth_defines:
        commands += f"verilog_defines {TclUtils.escape(f'-D{define}')}\n"
        if tcl:
            commands += (
                f"lappend ::_synlig_defines {TclUtils.escape(f'+define+{define}')}\n"
            )

    scl_lib_list = toolbox.filter_views(config, config["LIB"])

    if power_defines:
        if power_define := config.get(
            "VERILOG_POWER_DEFINE"
        ):  # VERILOG_POWER_DEFINE not defined for VHDLSynthesis
            commands += f"verilog_defines {TclUtils.escape(f'-D{power_define}')}\n"
            if tcl:
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
    if tcl:
        commands += (
            f"set ::env(SYNTH_LIBS) {TclUtils.escape(TclUtils.join(lib_synth))}\n"
        )

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


# No longer used by us, kept for back-compat
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
        Variable(
            "YOSYS_LOG_LEVEL",
            Literal["ALL", "WARNING", "ERROR"],
            "Which log level for Yosys. At WARNING or higher, the initialization splash is also disabled.",
            default="ALL",
        ),
    ]

    def get_command(self) -> List[str]:
        script_path = self.get_script_path()
        cmd = ["yosys", "-c", script_path]
        if self.config["YOSYS_LOG_LEVEL"] != "ALL":
            cmd += ["-Q"]
        if self.config["YOSYS_LOG_LEVEL"] == "WARNING":
            cmd += ["-q"]
        elif self.config["YOSYS_LOG_LEVEL"] == "ERROR":
            cmd += ["-qq"]
        return cmd

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


def _mk_eqy_script(
    step,
    fp: io.TextIOWrapper,
    processed_pdk: str,
    state: State,
    against_netlist: Optional[str] = None,
):
    def p(*args, **kwargs):
        print(*args, **kwargs, file=fp)

    p("[script]")
    p(_generate_read_deps(step.config, step.toolbox, tcl=False))
    p("blackbox")
    p("")

    # Gold
    p("[gold]")
    if against_netlist is not None:
        # against previous netlist
        p(
            f"read_verilog -formal -sv {processed_pdk} {state[DesignFormat.NETLIST_NO_PHYSICAL_CELLS]}",
        )
    else:
        # against RTL
        p(
            "read_verilog -formal -sv",
            end=" ",
        )
        for file in step.config["VERILOG_FILES"]:
            p(
                f"{file}",
                end=" ",
            )
    p("")

    # Gate
    p("[gate]")
    if after := against_netlist:
        p(
            f"read_verilog -formal -sv {processed_pdk} {after}",
        )
    else:
        p(
            f"read_verilog -formal -sv {processed_pdk} {state[DesignFormat.NETLIST_NO_PHYSICAL_CELLS]}",
        )

    # Script
    p("[script]")
    p(f"hierarchy -top {step.config['DESIGN_NAME']}")
    p("proc")
    p(f"prep -top {step.config['DESIGN_NAME']} -flatten")
    p("memory -nomap")
    p("async2sync")
    p("")

    # Write
    for mode in ["gold", "gate"]:
        p(f"[{mode}]")
        p(f"write_verilog {step.step_dir}/{mode}.v")

    # Strats
    p(
        textwrap.dedent(
            """
            [strategy sat]
            use sat
            depth 5
            
            [strategy bitwuzla]
            use sby
            depth 2
            engine smtbmc bitwuzla
            
            [strategy pdr]
            use sby
            engine abc pdr -rfi
            """
        )
    )


def _run_eqy(
    step: Step,
    state: State,
    against_netlist: Optional[str] = None,
    silent: bool = False,
):
    processed_pdk = os.path.join(step.step_dir, "formal_pdk.v")

    if shutil.which("eqy") is None:
        info("EQY is not installed. Skipping…")
        return {}

    if step.config["PDK"].startswith("sky130A"):
        subprocess.check_call(
            [
                "eqy.formal_pdk_proc",
                "--output",
                processed_pdk,
            ]
            + [str(model) for model in step.config["CELL_VERILOG_MODELS"]]
        )
    elif step.config.get("EQY_FORCE_ACCEPT_PDK"):
        subprocess.check_call(
            ["iverilog", "-E", "-o", processed_pdk, "-DFUNCTIONAL"]
            + [str(model) for model in step.config["CELL_VERILOG_MODELS"]]
        )
    else:
        info(f"PDK {step.config['PDK']} is not supported by EQY. Skipping…")
        return {}

    eqy_script_path = os.path.join(step.step_dir, f"{step.config['DESIGN_NAME']}.eqy")

    with open(eqy_script_path, "w", encoding="utf8") as f:
        if eqy_script := step.config.get("EQY_SCRIPT"):
            for line in open(eqy_script, "r", encoding="utf8"):
                f.write(line)
        else:
            _mk_eqy_script(
                step,
                f,
                processed_pdk,
                state,
                against_netlist=against_netlist,
            )
    work_dir = os.path.join(step.step_dir, "scratch")

    subprocess_result = step.run_subprocess(
        ["eqy", "-f", eqy_script_path, "-d", work_dir],
        log_to=os.path.join(step.step_dir, "eqy.log"),
        silent=silent,
    )

    os.unlink(os.path.join(work_dir, "partition.log"))  # Grows into the 10s of GBs

    return subprocess_result["generated_metrics"]


@Step.factory.register()
class EQY(Step):
    id = "Yosys.EQY"
    name = "Equivalence Check"

    inputs = [DesignFormat.NETLIST_NO_PHYSICAL_CELLS]
    outputs = []

    config_vars = (
        YosysStep.config_vars
        + verilog_rtl_cfg_vars
        + [
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
    )

    def run(self, state_in: State, **kwargs) -> Tuple[ViewsUpdate, MetricsUpdate]:
        return {}, _run_eqy(self, state_in, None)
