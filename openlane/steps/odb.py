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
import sys
import json
import site
import shutil
from math import inf
from decimal import Decimal
from functools import reduce
from abc import abstractmethod
from typing import List, Literal, Optional, Tuple


from .common_variables import io_layer_variables
from .openroad import DetailedPlacement, GlobalRouting
from .step import ViewsUpdate, MetricsUpdate, Step, StepException, CompositeStep
from ..logging import warn, info, verbose
from ..config import Variable, Macro
from ..state import State, DesignFormat
from ..common import Path, get_script_dir

inf_rx = re.compile(r"\b(-?)inf\b")


class OdbpyStep(Step):
    inputs = [DesignFormat.ODB]
    outputs = [DesignFormat.ODB, DesignFormat.DEF]

    def run(self, state_in, **kwargs) -> Tuple[ViewsUpdate, MetricsUpdate]:
        kwargs, env = self.extract_env(kwargs)

        automatic_outputs = set(self.outputs).intersection(
            [DesignFormat.ODB, DesignFormat.DEF]
        )

        views_updates: ViewsUpdate = {}
        command = self.get_command()
        for output in automatic_outputs:
            filename = f"{self.config['DESIGN_NAME']}.{output.value.extension}"
            file_path = os.path.join(self.step_dir, filename)
            command.append(f"--output-{output.value.id}")
            command.append(file_path)
            views_updates[output] = Path(file_path)

        command += [
            str(state_in[DesignFormat.ODB]),
        ]

        python_path_elements = site.getsitepackages() + sys.path
        if current_pythonpath := env.get("PYTHONPATH"):
            python_path_elements.append(current_pythonpath)
        python_path_elements.append(os.path.join(get_script_dir(), "odbpy"))
        env["PYTHONPATH"] = ":".join(python_path_elements)

        generated_metrics = self.run_subprocess(
            command,
            env=env,
            **kwargs,
        )

        metrics_path = os.path.join(self.step_dir, "or_metrics_out.json")
        metrics_updates: MetricsUpdate = generated_metrics
        if os.path.exists(metrics_path):
            or_metrics_out = json.loads(open(metrics_path).read(), parse_float=Decimal)
            for key, value in or_metrics_out.items():
                if value == "Infinity":
                    or_metrics_out[key] = inf
                elif value == "-Infinity":
                    or_metrics_out[key] = -inf
            metrics_updates.update(or_metrics_out)

        return views_updates, metrics_updates

    def get_command(self) -> List[str]:
        metrics_path = os.path.join(self.step_dir, "or_metrics_out.json")

        tech_lefs = self.toolbox.filter_views(self.config, self.config["TECH_LEFS"])
        if len(tech_lefs) != 1:
            raise StepException(
                "Misconfigured SCL: 'TECH_LEFS' must return exactly one Tech LEF for its default timing corner."
            )

        lefs = ["--input-lef", str(tech_lefs[0])]
        for lef in self.config["CELL_LEFS"]:
            lefs.append("--input-lef")
            lefs.append(lef)
        if extra_lefs := self.config["EXTRA_LEFS"]:
            for lef in extra_lefs:
                lefs.append("--input-lef")
                lefs.append(lef)
        if (design_lef := self.state_in.result()[DesignFormat.LEF]) and (
            DesignFormat.LEF in self.inputs
        ):
            lefs.append("--design-lef")
            lefs.append(str(design_lef))
        return (
            [
                "openroad",
                "-exit",
                "-no_splash",
                "-metrics",
                str(metrics_path),
                "-python",
                self.get_script_path(),
            ]
            + self.get_subcommand()
            + lefs
        )

    @abstractmethod
    def get_script_path(self) -> str:
        pass

    def get_subcommand(self) -> List[str]:
        return []


@Step.factory.register()
class CheckMacroAntennaProperties(OdbpyStep):
    id = "Odb.CheckMacroAntennaProperties"
    name = "Check Antenna Properties of Macros Pins in Their LEF Views"
    inputs = OdbpyStep.inputs
    outputs = []

    def get_script_path(self):
        return os.path.join(
            get_script_dir(),
            "odbpy",
            "check_antenna_properties.py",
        )

    def get_cells(self) -> List[str]:
        macros = self.config["MACROS"]
        cells = []
        if macros:
            cells = list(macros.keys())
        return cells

    def get_report_path(self) -> str:
        return os.path.join(self.step_dir, "report.yaml")

    def get_command(self) -> List[str]:
        args = " ".join([f"--cell-name {name}" for name in self.get_cells()]).split()
        args += ["--report-file", self.get_report_path()]
        return super().get_command() + args

    def run(self, state_in, **kwargs) -> Tuple[ViewsUpdate, MetricsUpdate]:
        if not self.get_cells():
            info("No cells provided, skipping…")
            return {}, {}
        return super().run(state_in, **kwargs)


@Step.factory.register()
class CheckDesignAntennaProperties(CheckMacroAntennaProperties):
    id = "Odb.CheckDesignAntennaProperties"
    name = "Check Antenna Properties of Pins in The Generated Design LEF view"
    inputs = CheckMacroAntennaProperties.inputs + [DesignFormat.LEF]

    def get_cells(self) -> List[str]:
        return [self.config["DESIGN_NAME"]]


@Step.factory.register()
class ApplyDEFTemplate(OdbpyStep):
    """
    Copies the floorplan of a "template" DEF file for a new design, i.e.,
    it will copy the die area, core area, and non-power pin names and locations.
    """

    id = "Odb.ApplyDEFTemplate"
    name = "Apply DEF Template"

    config_vars = [
        Variable(
            "FP_DEF_TEMPLATE",
            Optional[Path],
            "Points to the DEF file to be used as a template.",
        ),
        Variable(
            "FP_TEMPLATE_MATCH_MODE",
            Literal["strict", "permissive"],
            "Whether to require that the pin set of the DEF template and the design should be identical. In permissive mode, pins that are in the design and not in the template will be excluded, and vice versa.",
            default="strict",
        ),
    ]

    def get_script_path(self):
        return os.path.join(
            get_script_dir(),
            "odbpy",
            "apply_def_template.py",
        )

    def get_command(self) -> List[str]:
        return super().get_command() + [
            "--def-template",
            self.config["FP_DEF_TEMPLATE"],
            f"--{self.config['FP_TEMPLATE_MATCH_MODE']}",
        ]

    def run(self, state_in, **kwargs) -> Tuple[ViewsUpdate, MetricsUpdate]:
        if self.config["FP_DEF_TEMPLATE"] is None:
            info("No DEF template provided, skipping…")
            return {}, {}

        views_updates, metrics_updates = super().run(state_in, **kwargs)
        design_area_string = self.state_in.result().metrics.get("design__die__bbox")
        if design_area_string:
            template_area_string = metrics_updates["design__die__bbox"]
            template_area = [Decimal(point) for point in template_area_string.split()]
            design_area = [Decimal(point) for point in design_area_string.split()]
            if template_area != design_area:
                warn(
                    "The die area specificied in FP_DEF_TEMPLATE is different than the design die area. Pin placement may be incorrect."
                )
                warn(
                    f"Design area: {design_area_string}. Template def area: {template_area_string}"
                )
        return views_updates, {}


@Step.factory.register()
class SetPowerConnections(OdbpyStep):
    """
    Uses JSON netlist and module information in Odb to add global power connections
    for macros in a design.
    """

    id = "Odb.SetPowerConnections"
    name = "Set Power Connections"
    inputs = [DesignFormat.JSON_HEADER, DesignFormat.ODB]

    def get_script_path(self):
        return os.path.join(get_script_dir(), "odbpy", "power_utils.py")

    def get_subcommand(self) -> List[str]:
        return ["set-power-connections"]

    def get_command(self) -> List[str]:
        state_in = self.state_in.result()
        return super().get_command() + [
            "--input-json",
            str(state_in[DesignFormat.JSON_HEADER]),
        ]


@Step.factory.register()
class WriteVerilogHeader(OdbpyStep):
    """
    Writes a Verilog header of the module using information from the generated
    PDN, guarded by the value of ``VERILOG_POWER_DEFINE``, and the JSON header.
    """

    id = "Odb.WriteVerilogHeader"
    name = "Write Verilog Header"
    inputs = [DesignFormat.ODB, DesignFormat.JSON_HEADER]
    outputs = [DesignFormat.VERILOG_HEADER]

    config_vars = OdbpyStep.config_vars + [
        Variable(
            "VERILOG_POWER_DEFINE",
            str,
            "Specifies the name of the define used to guard power and ground connections in the output Verilog header.",
            deprecated_names=["SYNTH_USE_PG_PINS_DEFINES", "SYNTH_POWER_DEFINE"],
            default="USE_POWER_PINS",
        ),
    ]

    def get_script_path(self):
        return os.path.join(get_script_dir(), "odbpy", "power_utils.py")

    def get_subcommand(self) -> List[str]:
        return ["write-verilog-header"]

    def get_command(self) -> List[str]:
        state_in = self.state_in.result()
        return super().get_command() + [
            "--output-vh",
            os.path.join(self.step_dir, f"{self.config['DESIGN_NAME']}.vh"),
            "--input-json",
            str(state_in[DesignFormat.JSON_HEADER]),
            "--power-define",
            self.config["VERILOG_POWER_DEFINE"],
        ]

    def run(self, state_in, **kwargs) -> Tuple[ViewsUpdate, MetricsUpdate]:
        views_updates, metrics_updates = super().run(state_in, **kwargs)
        views_updates[DesignFormat.VERILOG_HEADER] = Path(
            os.path.join(self.step_dir, f"{self.config['DESIGN_NAME']}.vh")
        )
        return views_updates, metrics_updates


@Step.factory.register()
class ManualMacroPlacement(OdbpyStep):
    """
    Performs macro placement using a simple configuration file. The file is
    defined as a line-break delimited list of instances and positions, in the
    format ``instance_name X_pos Y_pos Orientation``.

    If no macro instances are configured, this step is skipped.
    """

    id = "Odb.ManualMacroPlacement"
    name = "Manual Macro Placement"

    config_vars = [
        Variable(
            "MACRO_PLACEMENT_CFG",
            Optional[Path],
            "Path to an optional override for instance placement instead of the `MACROS` object for compatibility with OpenLane 1. If both are `None`, this step is skipped.",
        ),
    ]

    def get_script_path(self):
        return os.path.join(get_script_dir(), "odbpy", "manual_macro_place.py")

    def get_command(self) -> List[str]:
        return super().get_command() + [
            "--config",
            os.path.join(self.step_dir, "placement.cfg"),
            "--fixed",
        ]

    def run(self, state_in: State, **kwargs) -> Tuple[ViewsUpdate, MetricsUpdate]:
        cfg_file = Path(os.path.join(self.step_dir, "placement.cfg"))
        if cfg_ref := self.config.get("MACRO_PLACEMENT_CFG"):
            warn(
                "Using 'MACRO_PLACEMENT_CFG' is deprecated. It is recommended to use the 'MACROS' object."
            )
            shutil.copyfile(cfg_ref, cfg_file)
        elif macros := self.config.get("MACROS"):
            instance_count = reduce(
                lambda x, y: x + len(y.instances), macros.values(), 0
            )
            if instance_count >= 1:
                with open(cfg_file, "w") as f:
                    for module, macro in macros.items():
                        if not isinstance(macro, Macro):
                            raise StepException(
                                f"Misconstructed configuration: macro definition for key {module} is not of type 'Macro'."
                            )
                        for name, data in macro.instances.items():
                            if data.location is not None:
                                if data.orientation is None:
                                    raise StepException(
                                        f"Instance {name} of macro {module} has a location configured, but no orientation."
                                    )
                                f.write(
                                    f"{name} {data.location[0]} {data.location[1]} {data.orientation}\n"
                                )
                            else:
                                verbose(
                                    f"Instance {name} of macro {module} has no location configured, ignoring…"
                                )

        if not cfg_file.exists():
            info(f"No instances found, skipping '{self.id}'…")
            return {}, {}

        return super().run(state_in, **kwargs)


@Step.factory.register()
class ReportWireLength(OdbpyStep):
    """
    Outputs a CSV of long wires, printed by length. Useful as a design aid to
    detect when one wire is connected to too many things.
    """

    outputs = []

    id = "Odb.ReportWireLength"
    name = "Report Wire Length"
    outputs = []

    def get_script_path(self):
        return os.path.join(get_script_dir(), "odbpy", "wire_lengths.py")

    def get_command(self) -> List[str]:
        return super().get_command() + [
            "--human-readable",
            "--report-out",
            os.path.join(self.step_dir, "wire_lengths.csv"),
        ]


@Step.factory.register()
class ReportDisconnectedPins(OdbpyStep):
    """
    Creates a table of disconnected pins in the design, updating metrics as
    appropriate.

    Disconnected pins may be marked "critical" if they are very likely to
    result in a dead design. We determine if a pin is critical as follows:

    * For the top-level macro: for these four kinds of pins: inputs, outputs,
    power inouts, and ground inouts, at least one of each kind must be connected
    or else all pins of a certain kind are counted as critical disconnected
    pins.
    * For instances:
        * Any unconnected input is a critical disconnected pin.
        * If there isn't at least one output connected, all disconnected
            outputs are critical disconnected pins.
        * Any disconnected power inout pins are critical disconnected pins.

    The metrics ``design__disconnected_pin__count`` and
    ``design__critical_disconnected_pin__count`` is updated. It is recommended
    to use the checker ``Checker.DisconnectedPins`` to check that there are
    no critical disconnected pins.
    """

    id = "Odb.ReportDisconnectedPins"
    name = "Report Disconnected Pins"

    config_vars = OdbpyStep.config_vars + [
        Variable(
            "IGNORE_DISCONNECTED_MODULES",
            Optional[List[str]],
            "Modules (or cells) to ignore when checking for disconnected pins.",
            pdk=True,
        ),
    ]

    def get_script_path(self):
        return os.path.join(get_script_dir(), "odbpy", "disconnected_pins.py")

    def get_command(self) -> List[str]:
        command = super().get_command()
        if ignored_modules := self.config["IGNORE_DISCONNECTED_MODULES"]:
            for module in ignored_modules:
                command.append("--ignore-module")
                command.append(module)
        return command


@Step.factory.register()
class AddRoutingObstructions(OdbpyStep):
    id = "Odb.AddRoutingObstructions"
    name = "Add Obstructions"
    config_vars = [
        Variable(
            "ROUTING_OBSTRUCTIONS",
            Optional[List[str]],
            "Add routing obstructions to the design. If set to `None`, this step is skipped."
            + " Format of each obstruction item is: layer llx lly urx ury.",
            units="µm",
            default=None,
            deprecated_names=["GRT_OBS"],
        ),
    ]

    def get_obstruction_variable(self):
        return self.config_vars[0]

    def get_script_path(self):
        return os.path.join(get_script_dir(), "odbpy", "defutil.py")

    def get_subcommand(self) -> List[str]:
        return ["add_obstructions"]

    def get_command(self) -> List[str]:
        command = super().get_command()
        if obstructions := self.config[self.config_vars[0].name]:
            for obstruction in obstructions:
                command.append("--obstructions")
                command.append(obstruction)
        return command

    def run(self, state_in, **kwargs) -> Tuple[ViewsUpdate, MetricsUpdate]:
        if self.config[self.get_obstruction_variable().name] is None:
            info(
                f"'{self.get_obstruction_variable().name}' is not defined. Skipping '{self.id}'…"
            )
            return {}, {}
        return super().run(state_in, **kwargs)


@Step.factory.register()
class RemoveRoutingObstructions(AddRoutingObstructions):
    id = "Odb.RemoveRoutingObstructions"
    name = "Remove Obstructions"

    def get_subcommand(self) -> List[str]:
        return ["remove_obstructions"]


@Step.factory.register()
class AddPDNObstructions(AddRoutingObstructions):
    id = "Odb.AddPDNObstructions"
    name = "Add PDN obstructions"

    config_vars = [
        Variable(
            "PDN_OBSTRUCTIONS",
            Optional[List[str]],
            "Add routing obstructions to the design before PDN stage. If set to `None`, this step is skipped."
            + " Format of each obstruction item is: layer llx lly urx ury.",
            units="µm",
            default=None,
        ),
    ]


@Step.factory.register()
class RemovePDNObstructions(RemoveRoutingObstructions):
    id = "Odb.RemovePDNObstructions"
    name = "Remove PDN obstructions"

    config_vars = AddPDNObstructions.config_vars


@Step.factory.register()
class CustomIOPlacement(OdbpyStep):
    """
    Places I/O pins using a custom script, which uses a "pin order configuration"
    file.

    Check the reference documentation for the structure of said file.
    """

    id = "Odb.CustomIOPlacement"
    name = "Custom I/O Placement"
    long_name = "Custom I/O Pin Placement Script"

    config_vars = io_layer_variables + [
        Variable(
            "FP_PIN_ORDER_CFG",
            Optional[Path],
            "Path to the configuration file. If set to `None`, this step is skipped.",
        ),
        Variable(
            "QUIT_ON_UNMATCHED_IO",
            bool,
            "Exit on unmatched pins in a provided `FP_PIN_ORDER_CFG` file.",
            default=True,
            deprecated_names=["FP_IO_UNMATCHED_ERROR"],
        ),
    ]

    def get_script_path(self):
        return os.path.join(get_script_dir(), "odbpy", "io_place.py")

    def get_command(self) -> List[str]:
        length = max(
            self.config["FP_IO_VLENGTH"],
            self.config["FP_IO_HLENGTH"],
        )

        return super().get_command() + [
            "--config",
            self.config["FP_PIN_ORDER_CFG"],
            "--hor-layer",
            self.config["FP_IO_HLAYER"],
            "--ver-layer",
            self.config["FP_IO_VLAYER"],
            "--hor-width-mult",
            str(self.config["FP_IO_VTHICKNESS_MULT"]),
            "--ver-width-mult",
            str(self.config["FP_IO_HTHICKNESS_MULT"]),
            "--hor-extension",
            str(self.config["FP_IO_HEXTEND"]),
            "--ver-extension",
            str(self.config["FP_IO_VEXTEND"]),
            "--length",
            str(length),
            (
                "--unmatched-error"
                if self.config["QUIT_ON_UNMATCHED_IO"]
                else "--ignore-unmatched"
            ),
        ]

    def run(self, state_in, **kwargs) -> Tuple[ViewsUpdate, MetricsUpdate]:
        if self.config["FP_PIN_ORDER_CFG"] is None:
            info("No custom floorplan file configured, skipping…")
            return {}, {}
        return super().run(state_in, **kwargs)


@Step.factory.register()
class PortDiodePlacement(OdbpyStep):
    """
    Unconditionally inserts diodes on design ports diodes on ports,
    to mitigate the `antenna effect <https://en.wikipedia.org/wiki/Antenna_effect>`_.

    Useful for hardening macros, where ports may get long wires that are
    unaccounted for when hardening a top-level chip.

    The placement is **not legalized**.
    """

    id = "Odb.PortDiodePlacement"
    name = "Port Diode Placement Script"

    config_vars = [
        Variable(
            "DIODE_ON_PORTS",
            Literal["none", "in", "out", "both"],
            "Always insert diodes on ports with the specified polarities.",
            default="none",
        ),
        Variable(
            "GPL_CELL_PADDING",
            Decimal,
            "Cell padding value (in sites) for global placement. Used by this step only to emit a warning if it's 0.",
            units="sites",
            pdk=True,
        ),
    ]

    def get_script_path(self):
        return os.path.join(get_script_dir(), "odbpy", "diodes.py")

    def get_subcommand(self) -> List[str]:
        return ["place"]

    def get_command(self) -> List[str]:
        cell, pin = self.config["DIODE_CELL"].split("/")

        return super().get_command() + [
            "--diode-cell",
            cell,
            "--diode-pin",
            pin,
            "--port-protect",
            self.config["DIODE_ON_PORTS"],
            "--threshold",
            "Infinity",
        ]

    def run(self, state_in: State, **kwargs) -> Tuple[ViewsUpdate, MetricsUpdate]:
        if self.config["DIODE_ON_PORTS"] == "none":
            warn("'DIODE_ON_PORTS' is set to 'none': skipping…")
            return {}, {}

        if self.config["GPL_CELL_PADDING"] == 0:
            warn(
                "'GPL_CELL_PADDING' is set to 0. This step may cause overlap failures."
            )

        return super().run(state_in, **kwargs)


@Step.factory.register()
class DiodesOnPorts(CompositeStep):
    """
    Unconditionally inserts diodes on design ports diodes on ports,
    to mitigate the `antenna effect <https://en.wikipedia.org/wiki/Antenna_effect>`_.

    Useful for hardening macros, where ports may get long wires that are
    unaccounted for when hardening a top-level chip.

    The placement is legalized by performing detailed placement and global
    routing after inserting the diodes.

    Prior to beta 16, this step did not legalize its placement: if you would
    like to retain the old behavior without legalization, try
    ``Odb.PortDiodePlacement``.
    """

    id = "Odb.DiodesOnPorts"
    name = "Diodes on Ports"
    long_name = "Diodes on Ports Protection Routine"

    Steps = [
        PortDiodePlacement,
        DetailedPlacement,
        GlobalRouting,
    ]

    def run(self, state_in: State, **kwargs) -> Tuple[ViewsUpdate, MetricsUpdate]:
        if self.config["DIODE_ON_PORTS"] == "none":
            warn("'DIODE_ON_PORTS' is set to 'none': skipping…")
            return {}, {}
        return super().run(state_in, **kwargs)


@Step.factory.register()
class FuzzyDiodePlacement(OdbpyStep):
    """
    Runs a custom diode placement script to mitigate the `antenna effect <https://en.wikipedia.org/wiki/Antenna_effect>`_.

    This script uses the `Manhattan length <https://en.wikipedia.org/wiki/Manhattan_distance>`_
    of a (non-existent) wire at the global placement stage, and places diodes
    if they exceed a certain threshold. This, however, requires some padding:
    `GPL_CELL_PADDING` and `DPL_CELL_PADDING` must be higher than 0 for this
    script to work reliably.

    The placement is *not* legalized.

    The original script was written by `Sylvain "tnt" Munaut <https://github.com/smunaut>`_.
    """

    id = "Odb.FuzzyDiodePlacement"
    name = "Fuzzy Diode Placement"

    config_vars = [
        Variable(
            "HEURISTIC_ANTENNA_THRESHOLD",
            Decimal,
            "A Manhattan distance above which a diode is recommended to be inserted by the heuristic inserter. If not specified, the heuristic algorithm.",
            units="µm",
            pdk=True,
        ),
        Variable(
            "GPL_CELL_PADDING",
            Decimal,
            "Cell padding value (in sites) for global placement. Used by this step only to emit a warning if it's 0.",
            units="sites",
            pdk=True,
        ),
    ]

    def get_script_path(self):
        return os.path.join(get_script_dir(), "odbpy", "diodes.py")

    def get_subcommand(self) -> List[str]:
        return ["place"]

    def get_command(self) -> List[str]:
        cell, pin = self.config["DIODE_CELL"].split("/")

        threshold_opts = []
        if threshold := self.config["HEURISTIC_ANTENNA_THRESHOLD"]:
            threshold_opts = ["--threshold", threshold]

        return (
            super().get_command()
            + [
                "--diode-cell",
                cell,
                "--diode-pin",
                pin,
            ]
            + threshold_opts
        )

    def run(self, state_in: State, **kwargs) -> Tuple[ViewsUpdate, MetricsUpdate]:
        if self.config["GPL_CELL_PADDING"] == 0:
            warn(
                "'GPL_CELL_PADDING' is set to 0. This step may cause overlap failures."
            )

        return super().run(state_in, **kwargs)


@Step.factory.register()
class HeuristicDiodeInsertion(CompositeStep):
    """
    Runs a custom diode insertion routine to mitigate the `antenna effect <https://en.wikipedia.org/wiki/Antenna_effect>`_.

    This script uses the `Manhattan length <https://en.wikipedia.org/wiki/Manhattan_distance>`_
    of a (non-existent) wire at the global placement stage, and places diodes
    if they exceed a certain threshold. This, however, requires some padding:
    `GPL_CELL_PADDING` and `DPL_CELL_PADDING` must be higher than 0 for this
    script to work reliably.

    The placement is then legalized by performing detailed placement and global
    routing after inserting the diodes.

    The original script was written by `Sylvain "tnt" Munaut <https://github.com/smunaut>`_.

    Prior to beta 16, this step did not legalize its placement: if you would
    like to retain the old behavior without legalization, try
    ``Odb.FuzzyDiodePlacement``.
    """

    id = "Odb.HeuristicDiodeInsertion"
    name = "Heuristic Diode Insertion"
    long_name = "Heuristic Diode Insertion Routine"

    Steps = [
        FuzzyDiodePlacement,
        DetailedPlacement,
        GlobalRouting,
    ]
