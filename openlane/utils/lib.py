#!/usr/bin/python3
# Copyright 2020-2023 Efabless Corporation
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
from typing import FrozenSet

from .memoize import memoize
from ..common import mkdirp


class LibTools(object):
    def __init__(self, tmp_dir: str):
        self.tmp_dir = os.path.abspath(tmp_dir)

    @memoize
    def remove_cells(
        self,
        input_lib_files: FrozenSet[str],
        excluded_cells: FrozenSet[str],
        as_cell_lists: bool = False,
    ) -> str:
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

        out_filename = f"{uuid.uuid4().hex}.lib"
        out_path = os.path.join(self.tmp_dir, out_filename)

        mkdirp(self.tmp_dir)
        output_file_handle = open(out_path, "w")

        def write(string):
            print(string, file=output_file_handle)

        cell_start_rx = re.compile(r"(\s*)cell\s*\(\"?(.*?)\"?\)\s*\{")

        state = 0
        brace_count = 0
        for file in input_lib_files:
            input_lib_str = open(file).read()
            input_lib_lines = input_lib_str.split("\n")
            for line in input_lib_lines:
                if state == 0:
                    cell_m = cell_start_rx.search(line)
                    if cell_m is not None:
                        whitespace = cell_m[1]
                        cell_name = cell_m[2]
                        if cell_name in excluded_cells:
                            state = 2
                            write(f"{whitespace}/* removed {cell_name} */")
                        else:
                            state = 1
                            write(line)
                        brace_count = 1
                    else:
                        write(line)
                elif state in [1, 2]:
                    if "{" in line:
                        brace_count += 1
                    if "}" in line:
                        brace_count -= 1
                    if state == 1:
                        write(line)
                    if brace_count == 0:
                        state = 0

        output_file_handle.close()

        return out_path
