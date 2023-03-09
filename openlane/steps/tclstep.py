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
from __future__ import annotations

import os
import re
import glob
import shutil
import textwrap
import subprocess
from enum import Enum
from decimal import Decimal
from collections import deque
from typing import List, Dict, Sequence, Union
from os.path import join, dirname, isdir, relpath

from .step import Step
from ..state import State
from ..config import Path
from ..logging import info, warn
from ..common import mkdirp, get_script_dir, get_openlane_root


def create_reproducible(
    step_dir: str,
    cmd: Sequence[Union[str, os.PathLike]],
    env_in: Dict[str, str],
    tcl_script: str,
    verbose: bool = False,
) -> str:
    step_dir = os.path.abspath(step_dir)
    run_path = os.path.dirname(step_dir)
    run_path_rel = os.path.relpath(run_path)
    pdk_root = env_in["PDK_ROOT"]

    info(
        textwrap.dedent(
            """\
            OpenLane TCLStep Issue Packager

            EFABLESS CORPORATION AND ALL AUTHORS OF THE OPENLANE PROJECT SHALL NOT BE HELD
            LIABLE FOR ANY LEAKS THAT MAY OCCUR TO ANY PROPRIETARY DATA AS A RESULT OF USING
            THIS SCRIPT. THIS SCRIPT IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OR
            CONDITIONS OF ANY KIND.

            BY USING THIS SCRIPT, YOU ACKNOWLEDGE THAT YOU FULLY UNDERSTAND THIS DISCLAIMER
            AND ALL IT ENTAILS.
            """
        )
    )

    # Phase 1: Set up destination folder
    destination_folder = os.path.join(step_dir, "tcl_reproducible")
    info(f"Setting up '{destination_folder}'…")

    try:
        shutil.rmtree(destination_folder)
    except FileNotFoundError:
        pass

    mkdirp(destination_folder)

    # Phase 2: Process TCL Scripts To Find Full List Of Files
    tcl_script_abspath = os.path.abspath(tcl_script)

    script_counter = 0

    def get_script_key():
        nonlocal script_counter
        value = f"PACKAGED_SCRIPT_{script_counter}"
        script_counter += 1
        return value

    tcls_to_process = deque([(tcl_script, get_script_key())])

    new_cmd = []
    for element in cmd:
        element = str(element)
        element_basename = os.path.basename(element)
        element_abspath = os.path.abspath(element)
        if os.path.exists(element):
            if element_abspath == tcl_script_abspath:
                new_cmd.append("$PACKAGED_SCRIPT_0")
            elif element_abspath.endswith(".tcl") or element_abspath.endswith(
                ".magicrc"
            ):
                env_key = get_script_key()
                tcls_to_process.append((element_abspath, env_key))
                new_cmd.append(f"${env_key}")
            else:
                new_cmd.append(element)
        elif element.startswith(run_path_rel) or element_abspath.startswith(run_path):
            new_cmd.append(element_basename)
        else:
            new_cmd.append(element)

    def shift(deque):
        try:
            return deque.popleft()
        except Exception:
            return None

    env_keys_used = set(["PDK_ROOT"])
    tcls = set()
    env = env_in.copy()
    current = shift(tcls_to_process)
    loop_guard = 1024
    while current is not None:
        env_key = None
        if isinstance(current, tuple):
            current, env_key = current

        loop_guard -= 1
        if loop_guard == 0:
            raise Exception("An infinite loop has been detected. Please file an issue.")

        if env_key is None:
            env_key = get_script_key()

        env_keys_used.add(env_key)
        env[env_key] = current

        warnings = []

        try:
            script = open(current).read()
            if verbose:
                info(f"Processing {current}…")

            for key, value in env.items():
                value = str(value)

                key_accessor = re.compile(
                    rf"((\$(?:\:\:)?env\({re.escape(key)}\))([/\-\w\.]*)|(\${re.escape(key)}))"
                )
                for use in key_accessor.findall(script):
                    full = use[0]
                    accessor = use[1] or use[3]
                    env_keys_used.add(key)
                    if verbose:
                        info(f"Found {accessor}…")
                    value_substituted = full.replace(accessor, value)

                    if value_substituted.endswith(".tcl") or value_substituted.endswith(
                        ".sdc"
                    ):
                        if value_substituted not in tcls:
                            tcls.add(value_substituted)
                            tcls_to_process.append(value_substituted)
        except FileNotFoundError:
            warnings.append(f"{current} was not found, might be a product. Skipping…")

        current = shift(tcls_to_process)

    # Phase 4: Copy The Files
    final_env = {}

    def copy(frm, to):
        parents = dirname(to)
        mkdirp(parents)

        def do_copy():
            if isdir(frm):
                shutil.copytree(frm, to)
            else:
                shutil.copyfile(frm, to)

        try:
            incomplete_matches = glob.glob(frm + "*")

            if len(incomplete_matches) == 0:
                raise FileNotFoundError()
            elif len(incomplete_matches) != 1 or incomplete_matches[0] != frm:
                # Prefix For Other Files
                for match in incomplete_matches:
                    if match == frm:
                        # If it's both a file AND a prefix for other files
                        do_copy()
                    else:
                        new_frm = match
                        new_to = to + new_frm[len(frm) :]
                        copy(new_frm, new_to)
            else:
                do_copy()
        except FileNotFoundError:
            warnings.append(f"{frm} was not found, might be a product. Skipping…")
        except Exception as e:
            warnings.append(f"Couldn't copy {frm}: {e}. Skipped.")

    if verbose:
        info("\nProcessing environment variables…\n---")

    ol_root = get_openlane_root()
    loop_guard = 1024
    for key in env_keys_used:
        loop_guard -= 1
        if loop_guard == 0:
            raise Exception("An infinite loop has been detected. Please file an issue.")
        full_value = env[key]
        final_env[key] = ""
        if verbose:
            info(f"Processing {key}: {full_value}")
        for potential_file in full_value.split():
            potential_file_abspath = os.path.abspath(potential_file)
            if potential_file_abspath.startswith(run_path):
                final_env[key] = ""
                relative = relpath(potential_file, run_path)
                final_value = join(".", relative)
                final_path = join(destination_folder, final_value)
                from_path = potential_file
                if potential_file_abspath != step_dir:  # Otherwise, infinite recursion
                    copy(from_path, final_path)
                final_env[key] += f"{final_value} "
            elif potential_file_abspath.startswith(pdk_root):
                if potential_file_abspath == pdk_root:  # Too many files to copy
                    continue
                relative = relpath(potential_file, pdk_root)
                final_value = join("pdk", relative)
                final_path = join(destination_folder, final_value)
                copy(potential_file, final_path)
                final_env[key] += f"{final_value} "
            elif potential_file_abspath.startswith(ol_root):
                relative = relpath(potential_file, ol_root)
                final_value = join("openlane", relative)
                final_path = join(destination_folder, final_value)

                from_path = potential_file
                if potential_file_abspath != os.path.abspath(
                    get_script_dir()
                ):  # Too many files to copy otherwise
                    copy(from_path, final_path)
                final_env[key] += f"{final_value} "
            elif os.path.exists(potential_file) and not potential_file.startswith(
                "/dev"
            ):  # /dev/null, /dev/stdout, /dev/stderr, etc should still work
                final_path = join(destination_folder, potential_file)
                final_value = os.path.relpath(final_path, destination_folder)
                print(potential_file_abspath, final_path)
                copy(potential_file, final_path)
                final_env[key] += f"{final_value} "
            else:
                final_env[key] += f"{potential_file} "
        final_env[key] = final_env[key].rstrip()
    if verbose:
        info("---\n")

    for warning in warnings:
        warn(warning)

    # Phase 5: Create Environment Set/Run Files
    def env_list(
        format_string: str = "{key}={value}",
        env: Dict[str, str] = final_env,
        indent: int = 0,
    ) -> str:
        array = []
        for key, value in sorted(env.items()):
            array.append(format_string.format(key=key, value=value))
        value = f"\n{'    ' * indent}".join(array)
        return value

    run_shell = join(destination_folder, "run.sh")
    with open(run_shell, "w") as f:
        f.write(
            textwrap.dedent(
                f"""\
                #!/bin/sh
                dir=$(cd -P -- "$(dirname -- "$0")" && pwd -P)
                cd $dir;
                {env_list("export {key}='{value}';", indent=4)}
                {' '.join(new_cmd)}
                """
            )
        )
    os.chmod(run_shell, 0o755)

    gdb_env = join(destination_folder, "env.gdb")
    with open(gdb_env, "w") as f:
        f.write(env_list("set env {key} {value}"))

    lldb_env = join(destination_folder, "env.lldb")
    with open(lldb_env, "w") as f:
        f.write(env_list("env {key}={value}"))

    return destination_folder


class TclStep(Step):
    """
    A subclass of :class:`Step` that primarily deals with running Tcl-based utilities,
    such as Yosys, OpenROAD and Magic.

    A TclStep Step corresponds to running one Tcl script with such a utility.
    """

    def get_script_path(self):
        """
        :returns: A Tcl script to be run by this step.
        """
        return os.path.join(get_script_dir(), "tclsh", "hello.tcl")

    def get_command(self) -> List[str]:
        """
        :returns: The command used to run the script.
        """
        return ["tclsh", self.get_script_path()]

    def run(
        self,
        **kwargs,
    ) -> State:
        """
        This overriden :meth:`run` function prepares configuration variables and
        inputs for use with Tcl: specifically, it converts them all to
        environment variables so they may be used by the Tcl scripts being called.

        Additionally, it logs the output to a ``.log`` file named after the script.

        When overriding in a subclass, you may find it useful to use this pattern:

            kwargs, env = self.extract_env(kwargs)
            env["CUSTOM_ENV_VARIABLE"] = "1"
            return super().run(env=env, **kwargs)

        This will allow you to add further custom environment variables to a call
        while still respecting an `env` argument further up the call-stack.


        :param **kwargs: Passed on to subprocess execution: useful if you want to
            redirect stdin, stdout, etc.
        """
        state = super().run()
        command = self.get_command()

        kwargs, env = self.extract_env(kwargs)

        env["SCRIPTS_DIR"] = get_script_dir()
        env["STEP_DIR"] = os.path.abspath(self.step_dir)

        for element in self.config.keys():
            value = self.config[element]
            if value is None:
                continue

            if isinstance(value, list):
                value = " ".join(list(map(lambda x: str(x), value)))
            elif isinstance(value, Enum):
                value = value._name_
            elif isinstance(value, bool):
                value = "1" if value else "0"
            elif isinstance(value, Decimal) or isinstance(value, int):
                value = str(value)

            env[element] = value

        for input in self.inputs:
            if input is None:
                continue
            env[f"CURRENT_{input.name}"] = str(state[input])

        for output in self.outputs:
            filename = f"{self.config['DESIGN_NAME']}.{output.value[1]}"
            env[f"SAVE_{output.name}"] = os.path.join(self.step_dir, filename)

        try:
            self.run_subprocess(
                command,
                env=env,
                **kwargs,
            )
        except subprocess.CalledProcessError:
            reproducible_folder = create_reproducible(
                self.step_dir,
                command,
                env,
                self.get_script_path(),
            )
            info(
                f"Reproducible created: please tarball and upload '{os.path.relpath(reproducible_folder)}' if you're going to file an issue."
            )
            raise

        for output in self.outputs:
            path = Path(env[f"SAVE_{output.name}"])
            if not path.exists():
                continue
            state[output] = path

        return state
