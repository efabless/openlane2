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
from dataclasses import asdict
import os
import re
import sys
import uuid
import fnmatch
import tempfile
import subprocess
from enum import IntEnum
from shutil import which
from typing import Dict, FrozenSet, Optional, Tuple, List, Union

from .memoize import memoize
from ..state import DesignFormat
from ..logging import warn
from ..config import Config, Path, Macro
from ..common import mkdirp, get_script_dir


class Toolbox(object):
    def __init__(self, tmp_dir: Optional[str] = None) -> None:
        if tmp_dir is None:
            tmp_dir = "./openlane_tmp"  # Temporary
        self.tmp_dir = os.path.abspath(tmp_dir)

    def filter_views(
        self,
        config: Config,
        views_by_corner: Dict[str, Union[Path, List[Path]]],
        timing_corner: Optional[str] = None,
    ) -> List[Path]:
        timing_corner = timing_corner or config["DEFAULT_CORNER"]
        result: List[Path] = []

        for key, value in views_by_corner.items():
            if not fnmatch.fnmatch(timing_corner, key):
                continue
            if isinstance(value, list):
                result += value
            else:
                result += [value]

        return result

    def get_macro_views(
        self,
        config: Config,
        view: DesignFormat,
        timing_corner: Optional[str] = None,
        _unless_exist: Optional[DesignFormat] = None
    ) -> List[Path]:
        timing_corner = timing_corner or config["DEFAULT_CORNER"]
        macros = config["MACROS"]
        result: List[Path] = []

        if macros is None:
            return result

        id = view.value.id
        superseding_id = "NONEXISTENT"
        if _unless_exist is not None:
            superseding_id = _unless_exist.value.id
        for macro in macros.values():
            assert isinstance(macro, Macro)
            views = None
            try:
                views = getattr(macro, id)
            except AttributeError:
                pass
            superseding_views = None
            print(superseding_id)
            try:
                superseding_views = getattr(macro, superseding_id)
            except AttributeError:
                pass
            print(views, superseding_views)
            if views is None and superseding_view is None:
                warn(f"No {view.value.name} view found for macro '{macro.module}'.")
                continue
            if superseding_views is not None:
                continue

            views_filtered = self.filter_views(config, views, timing_corner)
            result += views_filtered
        return result

    def get_libs(
        self,
        config: Config,
        timing_corner: Optional[str] = None,
        prioritize_spef: bool = False,
    ) -> Tuple[str, List[Path]]:
        """
        Returns the lib files for a given configuration and timing corner.

        :param config: A configuration object.
        :param timing_corner: A fully qualified IPVT corner to get libs for.

            If not specified, the value for `DEFAULT_CORNER` from the SCL will
            be used.
        :param prioritize_spef: Do not return lib files for macros that have
            SPEF views.
        """
        timing_corner = timing_corner or config["DEFAULT_CORNER"]

        lib_list = []
        lib_list += self.filter_views(config, config["LIBS"], timing_corner)

        if len(lib_list) == 0:
            warn(f"No SCL lib files found for {timing_corner}.")

        prioritized = None
        if prioritize_spef:
            prioritized = DesignFormat.SPEF
        lib_list += self.get_macro_views(config, DesignFormat.LIB, timing_corner, _unless_exist=prioritized)
        
        extra_libs = config["EXTRA_LIBS"] or []
        lib_list += extra_libs

        return (timing_corner, lib_list)

    def _render_common(self, config: Config) -> Optional[Tuple[str, str, str]]:
        klayout_bin = which("klayout")
        if klayout_bin is None:
            warn("This PDK does not support KLayout; previews cannot be rendered.")
            return None

        lyp = config["KLAYOUT_PROPERTIES"]
        lyt = config["KLAYOUT_TECH"]
        lym = config["KLAYOUT_DEF_LAYER_MAP"]
        if None in [lyp, lyt, lym]:
            warn("This PDK does not support KLayout; previews cannot be rendered.")
            return None
        return (str(lyp), str(lyt), str(lym))

    def render_png(self, config: Config, input: str) -> Optional[bytes]:
        files = self._render_common(config)
        if files is None:
            return None
        lyp, lyt, lym = files

        tech_lefs = self.filter_views(config, config["TECH_LEFS"])
        if len(tech_lefs) != 1:
            raise ValueError(
                "Misconfigured SCL: 'TECH_LEFS' must return exactly one Tech LEF for its default timing corner."
            )

        lef_arguments = ["-l", str(tech_lefs[0])]
        for file in config["CELL_LEFS"]:
            lef_arguments += ["-l", str(file)]
        if extra := config["EXTRA_LEFS"]:
            for file in extra:
                lef_arguments += ["-l", str(file)]

        result = None
        with tempfile.NamedTemporaryFile() as f:
            try:
                cmd = [
                    sys.executable,
                    os.path.join(get_script_dir(), "klayout", "render.py"),
                    input,
                    "--output",
                    f.name,
                    "--lyp",
                    lyp,
                    "--lyt",
                    lyt,
                    "--lym",
                    lym,
                ] + lef_arguments
                subprocess.check_output(
                    cmd,
                    stderr=subprocess.STDOUT,
                    encoding="utf8",
                )
                result = f.read()
            except subprocess.CalledProcessError as e:
                warn(f"Failed to render preview: {e.stdout}")
        return result

    @memoize
    def remove_cells_from_lib(
        self,
        input_lib_files: FrozenSet[str],
        excluded_cells: FrozenSet[str],
        as_cell_lists: bool = False,
    ) -> List[str]:
        """
        Returns a path to a new lib file without specific cells.

        This function is memoized, i.e., results are cached for a specific set
        of inputs.

        :param input_lib_files: A `frozenset` of input lib files.
        :param excluded_cells: A `frozenset` of either cells to be removed or
            lists of cells to be removed if `as_cell_lists` is set to `True`.
        :param as_cell_lists: If set to true, `excluded_cells` is treated as a
            list of files that are themselves lists of cells. Otherwise, it is
            treated as a list of cells.
        :returns: A path to a lib file with the removed cells.
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

        mkdirp(self.tmp_dir)

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
                            write(f"{whitespace}/* removed {cell_name} */")
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
