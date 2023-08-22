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
import json
import shlex
import datetime
from functools import partial
from typing import Any, Dict, Optional, Sequence, Union

from click import pass_context, Context
from cloup import (
    group,
    option,
    command,
    Path,
)

from .step import Step, StepError, StepException
from ..common import mkdirp, Toolbox
from ..logging import info, err, warn
from ..__version__ import __version__
from ..common.cli import formatter_settings


def extract_step_id(ctx: Context, json_in_path: str) -> Optional[str]:
    try:
        cfg = json.load(open(json_in_path, encoding="utf8"))
        meta = cfg.get("meta") or {}
        return meta.get("step")
    except json.JSONDecodeError:
        err("Invalid JSON provided for configuration object.")
        ctx.exit(-1)


def load_step_from_inputs(
    ctx: Context,
    id: Optional[str],
    config: str,
    state_in: str,
) -> Step:
    if id is None:
        id = extract_step_id(ctx, config)
        if id is None:
            err(
                "Step ID not provided either in the Configuration object's .meta.step value or over the command-line."
            )
            ctx.exit(-1)
    Target = Step.factory.get(id)
    if Target is None:
        err(
            f"No step registered with id '{id}'. Ensure all relevant plugins are installed."
        )
        ctx.exit(-1)

    return Target.load(
        config_path=config,
        state_in_path=state_in,
    )


o = partial(option, show_default=True)


@command(formatter_settings=formatter_settings)
@o(
    "-o",
    "--output",
    type=Path(
        exists=False,
        file_okay=False,
        dir_okay=True,
    ),
    help="The directory to store artifacts from step execution in",
    default=os.path.join(
        os.getcwd(),
        datetime.datetime.now().astimezone().strftime("STEP_RUN_%Y-%m-%d_%H-%M-%S"),
    ),
)
@o(
    "--id",
    type=str,
    required=False,
    help="The ID for the step. Can be omitted if the configuration object has the ID in the key-path .meta.step.",
)
@o(
    "-c",
    "--config",
    type=Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
    ),
    required=True,
    help="A step-specific config.json file",
)
@o(
    "-i",
    "--state-in",
    type=Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
    ),
    required=False,
)
@pass_context
def run(ctx, output, state_in, config, id):
    """
    Runs a step using a step-specific configuration object and an input state.

    Useful for re-running a step that has already run, or running
    filesystem-independent reproducibles.
    """

    step = load_step_from_inputs(ctx, id, config, state_in)

    if step.config.meta.openlane_version != __version__:
        warn(
            "OpenLane version being used is different from the version this step was originally run with. Procceed with caution."
        )

    mkdirp(output)
    toolbox_dir = os.path.join(output, "toolbox_tmp")
    try:
        step.start(
            toolbox=Toolbox(toolbox_dir),
            step_dir=output,
        )
    except StepException as e:
        err("An unexpected error occurred while executing your step:")
        err(e)
        ctx.exit(-1)
    except StepError as e:
        err("An error occurred while executing your step:")
        err(e)
        ctx.exit(-1)


@command(formatter_settings=formatter_settings)
@o(
    "-o",
    "--output",
    type=Path(
        exists=False,
        file_okay=True,
        dir_okay=False,
    ),
    help="Ejected run script",
    default="run.sh",
)
@o(
    "--id",
    type=str,
    required=False,
    help="The ID for the step. Can be omitted if the configuration object has the ID in the key-path .meta.step.",
)
@o(
    "-c",
    "--config",
    type=Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
    ),
    required=True,
    help="A step-specific config.json file",
)
@o(
    "-i",
    "--state-in",
    type=Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
    ),
    required=False,
)
@pass_context
def eject(ctx, output, state_in, config, id):
    """
    For steps that rely on underlying utilities using a subprocess, this scripts
    "ejects" OpenLane and just returns a shell script that runs this subprocess.

    This is useful for:

    * OpenLane developers and maintainers reporting issues to original tool
      developers
    * Advanced users who are sure that the issue is not OpenLane-specific and
      would like to skip reporting an issue with OpenLane first
    """

    step = load_step_from_inputs(ctx, id, config, state_in)

    if step.config.meta.openlane_version != __version__:
        warn(
            "OpenLane version being used is different from the version this step was originally run with. Procceed with caution."
        )

    toolbox_dir = os.path.join(output, "toolbox_tmp")

    found_cmd: Optional[Sequence[Union[str, os.PathLike]]] = None
    found_env: Optional[Dict[str, Any]] = None

    class Stop(Exception):
        pass

    def run_subprocess_subsitute(
        cmd: Sequence[Union[str, os.PathLike]],
        env: Optional[Dict[str, Any]] = None,
        *args,
        **kwargs,
    ):
        nonlocal found_env, found_cmd
        found_cmd = cmd
        found_env = env
        raise Stop()

    step.run_subprocess = run_subprocess_subsitute

    try:
        step.start(
            toolbox=Toolbox(toolbox_dir),
            step_dir=".",
        )
    except Stop:
        pass
    except Exception as e:
        info("An error occurred while attempting to execute the step:")
        err(e)
        info("This may affect the ejection process.")

    if found_cmd is None:
        err(
            "Could not eject: The step did not successfully invoke a subprocess using run_subprocess."
        )
        exit(-1)

    current_env = os.environ
    filtered_env = {}
    if found_env is not None:
        for key, value in found_env.items():
            if value != current_env.get(key) and value not in [
                "STEP_DIR",
                "SCRIPTS_DIR",
            ]:
                filtered_env[key] = value

    with open(output, "w", encoding="utf8") as f:
        f.write("#!/bin/sh\n")
        for key, value in filtered_env.items():
            f.write(f"export {key}={shlex.quote(str(value))}\n")
        f.write("\n")
        f.write(shlex.join([str(e) for e in found_cmd]))
        f.write("\n")

    if hasattr(os, "chmod"):
        os.chmod(output, 0o755)

    info("Ejected successfully.")


@command(formatter_settings=formatter_settings)
@o(
    "-o",
    "--output",
    type=Path(
        exists=False,
        file_okay=False,
        dir_okay=True,
    ),
    help="The output directory for the reproducible.",
    default="reproducible",
)
@o(
    "-d",
    "--step-dir",
    type=Path(
        exists=False,
        file_okay=False,
        dir_okay=True,
    ),
    help="The step directory from which to create the reproducible. If provided, --config and the input state can be omitted, and vice versa.",
    default=None,
)
@o(
    "--id",
    type=str,
    required=False,
    help="The ID for the step. Can be omitted if the configuration object has the ID in the key-path .meta.step.",
)
@o(
    "-c",
    "--config",
    type=Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
    ),
    required=False,
    help="A step-specific config.json file",
)
@o(
    "-i",
    "--state-in",
    type=Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
    ),
    required=False,
)
@pass_context
def create_reproducible(ctx, output, step_dir, id, config, state_in):
    """
    Creates a filesystem-independent step reproducible.

    The input can be either:

    * Both a configuration object (--config) and an input state (--state-in)

    * A step directory (--step-dir) generated from a previous run

    These reproducibles are filesystem-independent, i.e. they can be run
    on any computer that has the appropriate version of OpenLane 2 installed
    (as well as the underlying utility for that specific step.)

    The reproducible will report an error if OpenLane is not installed and will
    emit a warning if the installed version of OpenLane mismatches the one
    declared in the config file.
    """
    if step_dir is None:
        if config is None or state_in is None:
            err("Either --step-dir or both --config and --state-in must be provided.")
            ctx.exit(-1)
        elif None in [config, state_in]:
            err(
                "Both --config and --state-in must be provided if the --step-dir is not provided."
            )
            ctx.exit(-1)
    else:
        if config is None:
            config = os.path.join(step_dir, "config.json")
        if state_in is None:
            state_in = os.path.join(step_dir, "state_in.json")

    step = load_step_from_inputs(ctx, id, config, state_in)
    step.create_reproducible(output)


@group(formatter_settings=formatter_settings)
def cli():
    """
    Try 'python3 -m openlane.steps COMMAND --help' for help with a specific
    command.
    """
    pass


cli.add_command(run)
cli.add_command(eject)
cli.add_command(create_reproducible)

if __name__ == "__main__":
    cli()
