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
import pathlib
import rich.console

console = rich.console.Console()

log = console.log

rule = console.rule

print = console.print


def success(printable, *args, **kwargs):
    if kwargs.get("_stack_offset") is None:
        kwargs["_stack_offset"] = 2
    log(f"⭕ [green][bold] {printable}", *args, **kwargs)


def warn(printable, *args, **kwargs):
    if kwargs.get("_stack_offset") is None:
        kwargs["_stack_offset"] = 2
    log(f"⚠️ [gold][bold] {printable}", *args, **kwargs)


def err(printable, *args, **kwargs):
    if kwargs.get("_stack_offset") is None:
        kwargs["_stack_offset"] = 2
    log(f"❌ [red][bold] {printable}", *args, **kwargs)


def mkdirp(path):
    return pathlib.Path(path).mkdir(parents=True, exist_ok=True)


openlane_root = os.path.dirname(os.path.abspath(__file__))


def get_openlane_root():
    return openlane_root


def get_script_dir():
    """
    Gets the OpenLane tool `scripts` directory.
    """
    return os.path.join(
        openlane_root,
        "scripts",
    )
