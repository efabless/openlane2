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
from ..logging import warn, info
from ..config import Variable, Macro
from ..state import State, DesignFormat
from ..common import Path, get_script_dir

inf_rx = re.compile(r"\b(-?)inf\b")


class OdbpyStep(Step):
    inputs = [DesignFormat.ODB]
    outputs = [DesignFormat.ODB, DesignFormat.DEF]

    def run(self, state_in, **kwargs) -> Tuple[ViewsUpdate, MetricsUpdate]:
        kwargs, env = self.extract_env(kwargs)

        out_paths = {}

        command = self.get_command()
        for output in [DesignFormat.ODB, DesignFormat.DEF]:
            filename = f"{self.config['DESIGN_NAME']}.{output.value.extension}"
            file_path = os.path.join(self.step_dir, filename)
            command.append(f"--output-{output.value.id}")
            command.append(file_path)
            out_paths[output] = Path(file_path)

        command += [
            str(state_in[DesignFormat.ODB]),
        ]

        python_path_elements = site.getsitepackages()
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

        views_updates: ViewsUpdate = {}
        for output in [DesignFormat.ODB, DesignFormat.DEF]:
            views_updates[output] = out_paths[output]

        return views_updates, metrics_updates

    def get_command(self) -> List[str]:
        metrics_path = os.path.join(self.step_dir, "or_metrics_out.json")

        tech_lefs = self.toolbox.filter_views(self.config, self.config["TECH_LEFS"])
        if len(tech_lefs) != 1:
            raise StepException(
                "Misconfigured SCL: 'TECH_LEFS' must return exactly one Tech LEF for its default timing corner."
            )

        lefs = ["--input-lef", tech_lefs[0]]
        for lef in self.config["CELL_LEFS"]:
            lefs.append("--input-lef")
            lefs.append(lef)
        if extra_lefs := self.config["EXTRA_LEFS"]:
            for lef in extra_lefs:
                lefs.append("--input-lef")
                lefs.append(lef)
        return (
            [
                "openroad",
                "-exit",
                "-no_splash",
                "-metrics",
                metrics_path,
                "-python",
                self.get_script_path(),
            ]
            + self.get_subcommand()
            + lefs
        )

    @abstractmethod
    def get_script_path(self):
        pass

    def get_subcommand(self) -> List[str]:
        return []


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
        ]

    def run(self, state_in, **kwargs) -> Tuple[ViewsUpdate, MetricsUpdate]:
        if self.config["FP_DEF_TEMPLATE"] is None:
            info("No DEF template provided, skipping…")
            return {}, {}
        return super().run(state_in, **kwargs)


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
        return os.path.join(get_script_dir(), "odbpy", "set_power_connections.py")

    def get_command(self) -> List[str]:
        state_in = self.state_in.result()
        return super().get_command() + [
            "--input-json",
            str(state_in[DesignFormat.JSON_HEADER]),
        ]


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
                            f.write(
                                f"{name} {data.location[0]} {data.location[1]} {data.orientation}\n"
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
    id = "Odb.ReportDisconnectedPins"
    name = "Report Disconnected Pins"

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
                f"'{self.get_obstruction_variable().name}' is not defined. Skipping {self.id}…"
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
            "A manhattan distance above which a diode is recommended to be inserted by the heuristic inserter. If not specified, the heuristic algorithm.",
            units="µm",
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
