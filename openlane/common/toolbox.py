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
import uuid
import shutil
import fnmatch
import tempfile
import subprocess
from enum import IntEnum
from decimal import Decimal
from functools import lru_cache
from typing import (
    Any,
    Callable,
    Dict,
    FrozenSet,
    Iterable,
    Mapping,
    Optional,
    Tuple,
    List,
    Union,
)

import libparse
from deprecated.sphinx import deprecated


from .misc import Path, mkdirp
from .metrics import aggregate_metrics
from .design_format import DesignFormat
from .generic_dict import GenericImmutableDict, is_string
from ..logging import debug, warn, err


class Toolbox(object):
    """
    An assisting object shared by a Flow and all its constituent Steps.

    The toolbox may create artifacts that are cached to avoid constant re-creation
    between steps.
    """

    def __init__(self, tmp_dir: str) -> None:
        self.tmp_dir = tmp_dir

        mkdirp(self.tmp_dir)

        self.remove_cells_from_lib = lru_cache(16, True)(self.remove_cells_from_lib)  # type: ignore
        self.create_blackbox_model = lru_cache(16, True)(self.create_blackbox_model)  # type: ignore

    @deprecated(
        version="2.0.0b1",
        reason="Use 'aggregate_metrics' from 'openlane.common'",
        action="once",
    )
    def aggregate_metrics(
        self,
        input: Dict[str, Any],
        aggregator_by_metric: Dict[str, Tuple[Any, Callable[[Iterable], Any]]],
    ) -> Dict[str, Any]:
        return aggregate_metrics(input, aggregator_by_metric)

    def filter_views(
        self,
        config: Mapping[str, Any],
        views_by_corner: Mapping[str, Union[Path, Iterable[Path]]],
        timing_corner: Optional[str] = None,
    ) -> List[Path]:
        """
        Given a mapping from (wildcards of) corner names to views, this function
        enumerates all views matching either the default timing corner or
        an explicitly-provided override.

        :param config: The configuration. Used solely to extract the default corner.
        :param views_by_corner: The mapping from (wild cards) of vorner names to
            views.
        :param corner: An explicit override for the default corner. Must be a
            fully qualified IPVT corner.
        :returns: The created list
        """
        timing_corner = timing_corner or config["DEFAULT_CORNER"]
        result: List[Path] = []

        for key, value in views_by_corner.items():
            if not fnmatch.fnmatch(timing_corner, key):
                continue
            if is_string(value):
                result += [value]  # type: ignore
            else:
                result += list(value)  # type: ignore

        return result

    def get_macro_views(
        self,
        config: Mapping[str, Any],
        view: DesignFormat,
        timing_corner: Optional[str] = None,
        unless_exist: Optional[DesignFormat] = None,
    ) -> List[Path]:
        """
        For :class:`Config` objects (or similar Mappings) that have Macro
        information, this function gets all Macro views matching a certain
        :class:`DesignFormat` for either the default timing corner or an
        explicitly-provided override.

        :param config: The configuration.
        :param view: The design format to return views of.
        :param timing_corner: An explicit override for the default corner set
            by the configuration.
        :param corner: An explicit override for the default corner. Must be a
            fully qualified IPVT corner.
        :param unless_exist: If a Macro also has a view for this DesignFormat,
            do not return a result for the requested DesignFormat.

            Useful for if you want to return say, Netlists if reliable LIB files
            do not exist.
        :returns: A list of the Macro views matched by the process described
            above.
        """
        from ..config import Macro

        timing_corner = timing_corner or config["DEFAULT_CORNER"]
        macros = config["MACROS"]
        result: List[Path] = []

        if macros is None:
            return result

        for module, macro in macros.items():
            if not isinstance(macro, Macro):
                raise TypeError(
                    f"Misconstructed configuration: macro definition for key {module} is not of type 'Macro'."
                )

            views = macro.view_by_df(view)
            if views is None:
                continue

            if unless_exist is not None:
                entry = macro.view_by_df(unless_exist)
                if entry is not None:
                    alt_views = entry
                    if isinstance(alt_views, dict):
                        alt_views = self.filter_views(config, alt_views, timing_corner)
                    elif not isinstance(alt_views, list):
                        alt_views = [alt_views]
                    if len(alt_views) != 0:
                        continue
            if isinstance(views, dict):
                views_filtered = self.filter_views(config, views, timing_corner)
                result += views_filtered
            elif isinstance(views, list):
                result += views
            elif views is not None:
                result += [Path(views)]

        return [element for element in result if str(element) != Path._dummy_path]

    def get_timing_files(
        self,
        config: Mapping[str, Any],
        timing_corner: Optional[str] = None,
        prioritize_nl: bool = False,
    ) -> Tuple[str, List[str]]:
        """
        Returns the lib files for a given configuration and timing corner.

        :param config: A configuration object or a similar mapping.
        :param timing_corner:
            A fully qualified IPVT corner to get SCL libs for.

            If not specified, the value for `DEFAULT_CORNER` from the SCL will
            be used.
        :param prioritize_nl:
            Do not return lib files for macros that have gate-Level Netlists and
            SPEF views.

            If set to ``false``, only lib files are returned.
        :returns: A tuple of:
            * The name of the timing corner
            * A heterogenous list of files
                - Lib files are returned as-is
                - Netlists are returned as-is
                - SPEF files are returned in the format "{instance_name}@{spef_path}"

            It is left up to the step or tool to process this list as they see
            fit.
        """
        from ..config import Macro

        timing_corner = timing_corner or config["DEFAULT_CORNER"]

        result: List[Union[str, Path]] = []
        result += self.filter_views(config, config["LIB"], timing_corner)

        if len(result) == 0:
            warn(f"No SCL lib files found for {timing_corner}.")

        macros = config["MACROS"]
        if macros is None:
            macros = {}

        for module, macro in macros.items():
            if not isinstance(macro, Macro):
                raise TypeError(
                    f"Misconstructed configuration: macro definition for key {module} is not of type 'Macro'."
                )
            if prioritize_nl:
                netlists = macro.nl
                spefs = self.filter_views(
                    config,
                    macro.spef,
                    timing_corner,
                )
                if len(netlists) and not len(spefs):
                    warn(
                        f"Netlists found for macro {module}, but no parasitics extraction found at corner {timing_corner}. The netlist cannot be used for timing on this module."
                    )
                elif len(spefs) and not len(netlists):
                    warn(
                        f"Parasitics extraction(s) found for macro {module} at corner {timing_corner}, but no netlist found. The parasitics cannot be used for timing on this module."
                    )
                elif len(spefs) and len(netlists):
                    debug(f"Adding {[netlists + spefs]} to timing info…")
                    result += netlists
                    for spef in spefs:
                        for instance in macro.instances:
                            result.append(f"{instance}@{spef}")
                    continue
            # NL/SPEF not prioritized or not found
            libs = self.filter_views(
                config,
                macro.lib,
                timing_corner,
            )
            if not len(libs):
                warn(
                    f"No libs found for macro {module} at corner {timing_corner}. The module will be black-boxed."
                )
                continue
            debug(f"Adding {libs} to timing info…")
            result += libs

        return (timing_corner, [str(path) for path in result])

    def render_png(
        self,
        config: GenericImmutableDict[str, Any],
        state_in: GenericImmutableDict[str, Any],
    ) -> Optional[bytes]:  # pragma: no cover
        try:
            from ..steps import KLayout, StepError
            from ..config import Config, InvalidConfig
            from ..state import State

            # I'm too damn tired to figure out a way to forward-declare those two,
            # have fun if you want to
            if not isinstance(config, Config):
                raise TypeError("parameter config must be of type Config")

            if not isinstance(state_in, State):
                raise TypeError("parameter state_in must be of type State")

            with tempfile.TemporaryDirectory() as d:
                render_step = KLayout.Render(config, state_in, _config_quiet=True)
                render_step.start(self, d)
                return open(os.path.join(d, "out.png"), "rb").read()
        except InvalidConfig:
            warn("PDK is incompatible with KLayout. Unable to generate preview.")
            return None
        except StepError as e:
            warn(f"Failed to generate preview: {e}.")
            return None

    def remove_cells_from_lib(
        self,
        input_lib_files: FrozenSet[str],
        excluded_cells: FrozenSet[str],
        as_cell_lists: bool = False,
    ) -> List[str]:
        """
        Creates a new lib file with some cells removed.

        This function is memoized, i.e., results are cached for a specific set
        of inputs.

        :param input_lib_files: A `frozenset` of input lib files.
        :param excluded_cells: A `frozenset` of either cells to be removed or
            lists of cells to be removed if `as_cell_lists` is set to `True`.
        :param as_cell_lists: If set to true, `excluded_cells` is treated as a
            list of files that are themselves lists of cells. Otherwise, it is
            treated as a list of cells.
        :returns: A path to the lib file with the removed cells.
        """
        if as_cell_lists:  # Paths to files
            excluded_cells_str = ""
            for file in excluded_cells:
                excluded_cells_str += open(file, encoding="utf8").read()
                excluded_cells_str += "\n"
            excluded_cells = frozenset(
                [
                    cell.strip()
                    for cell in excluded_cells_str.strip().split("\n")
                    if cell.strip() != ""
                ]
            )

        class State(IntEnum):
            initial = 0
            cell = 10
            excluded_cell = 11

        cell_start_rx = re.compile(r"(\s*)cell\s*\(\"?(.*?)\"?\)\s*\{")
        out_paths = []

        for file in input_lib_files:
            input_lib_stream = open(file)
            out_filename = f"{uuid.uuid4().hex}.lib"
            out_path = os.path.join(self.tmp_dir, out_filename)

            state = State.initial
            brace_count = 0
            output_file_handle = open(out_path, "w")
            write = lambda x: print(x, file=output_file_handle, end="")
            for line in input_lib_stream:
                if state == State.initial:
                    cell_m = cell_start_rx.search(line)
                    if cell_m is not None:
                        whitespace = cell_m[1]
                        cell_name = cell_m[2]
                        if cell_name in excluded_cells:
                            state = State.excluded_cell
                            write(f"{whitespace}/* removed {cell_name} */\n")
                        else:
                            state = State.cell
                            write(line)
                        brace_count = 1
                    else:
                        write(line)
                elif state in [State.cell, State.excluded_cell]:
                    if "{" in line:
                        brace_count += 1
                    if "}" in line:
                        brace_count -= 1
                    if state == State.cell:
                        write(line)
                    if brace_count == 0:
                        state = State.initial

            output_file_handle.close()

            out_paths.append(out_path)

        return out_paths

    def create_blackbox_model(
        self,
        input_models: FrozenSet[str],
        defines: FrozenSet[str],
    ) -> str:
        class State(IntEnum):
            output = 0
            dont = 1

        out_path = os.path.join(self.tmp_dir, f"{uuid.uuid4().hex}.bb.v")
        bad_yosys_line = re.compile(r"^\s+(\w+|(\\\S+?))\s*\(.*\).*;")
        final_files = []

        with open(out_path, "w", encoding="utf8") as out:
            for model in input_models:
                patched_path = os.path.join(
                    self.tmp_dir, f"{uuid.uuid4().hex}.patched.v"
                )
                patched = open(patched_path, "w", encoding="utf8")
                state = State.output
                for line in open(model, "r", encoding="utf8"):
                    if state == State.output:
                        if line.strip().startswith("specify"):
                            state = State.dont
                        elif bad_yosys_line.search(line) is None:
                            print(line.strip("\n"), file=patched)
                            print(line.strip("\n"), file=out)
                    elif state == State.dont:
                        if line.strip().startswith("endspecify"):
                            print("/* removed specify */", file=out)
                            state = State.output
                patched.close()
                print("", file=out)
                final_files.append(patched_path)

        yosys = shutil.which("yosys") or shutil.which("yowasp-yosys")

        if yosys is None:
            warn(
                "yosys and yowasp-yosys not found in PATH. This may trigger issues with blackboxing."
            )
            return out_path

        commands = ""
        for define in list(defines) + ["NO_PRIMITIVES"]:
            commands += f"verilog_defines -D{define};\n"
        for file in final_files:
            commands += f"read_verilog -sv -lib {file};\n"

        output_log_path = os.path.join(self.tmp_dir, f"{out_path}_yosys.log")
        output_log = open(output_log_path, "wb")
        try:
            subprocess.check_call(
                [
                    yosys,
                    "-p",
                    f"""
                    {commands}
                    blackbox;
                    write_verilog -noattr -noexpr -nohex -nodec -defparam -blackboxes {out_path};
                    """,
                ],
                stdout=output_log,
                stderr=subprocess.STDOUT,
            )
        except subprocess.CalledProcessError as e:
            output_log.close()
            err(f"Failed to pre-process input models for linting with Yosys: {e}")
            err(open(output_log_path, "r", encoding="utf8").read())
            err("Will attempt to load models into linter as-is.")

        return out_path

    def get_lib_voltage(
        self,
        input_lib: str,
    ) -> Optional[Decimal]:
        """
        Extract the voltage from the default operating conditions of a liberty file.

        Returns ``None`` if and only if the ``default_operating_conditions`` key
        does not exist and the number of operating conditions enumerated is not
        exactly 1 (one).

        :param input_lib: The lib file in question
        :returns: The voltage in question
        """
        parser = libparse.LibertyParser(open(input_lib, encoding="utf8"))
        ast = parser.ast

        default_operating_conditions_id = None
        operating_conditions_raw = {}
        for child in ast.children:
            if child.id == "default_operating_conditions":
                default_operating_conditions_id = child.value
            if child.id == "operating_conditions":
                operating_conditions_raw[child.args[0]] = child

        if default_operating_conditions_id is None:
            if len(operating_conditions_raw) > 1:
                warn(
                    f"No default operating condition defined in lib file '{input_lib}', and the lib file has multiple operating conditions."
                )
                return None

            elif len(operating_conditions_raw) < 1:
                warn(f"Lib file '{input_lib}' has no operating conditions set.")
                return None
            default_operating_conditions_id = list(operating_conditions_raw.keys())[0]

        operating_conditions = operating_conditions_raw[default_operating_conditions_id]
        operating_condition_dict = {}
        for child in operating_conditions.children:
            operating_condition_dict[child.id] = child.value
        return Decimal(operating_condition_dict["voltage"])
