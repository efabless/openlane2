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
import shutil
import sys
import glob
import tempfile
import subprocess
from textwrap import dedent
from typing import Tuple, Type, Optional, List, Union

import click

from .steps import State
from .__version__ import __version__
from .common import err, warn, log, get_opdks_rev, get_openlane_root
from .container import run_in_container
from .flows import Flow, SequentialFlow, FlowException, FlowError
from .config import Config, InvalidConfig


def run(
    flow_name: Optional[str],
    use_volare: bool,
    pdk_root: Optional[str],
    pdk: str,
    scl: Optional[str],
    config_files: str,
    run_tag: Optional[str],
    last_run: bool,
    frm: Optional[str],
    to: Optional[str],
    initial_state_json: Optional[str],
    config_override_strings: List[str],
):
    if len(config_files) != 1:
        print(f"Invalid argument count for config_files: ({len(config_files)}/1).")
        exit(-1)

    if use_volare:
        import volare

        pdk_root = volare.get_volare_home(pdk_root)

        volare.enable(pdk_root, pdk[:-1], get_opdks_rev())

    config_file = config_files[0]

    # Enforce Mutual Exclusion
    if run_tag is not None and last_run:
        err("--run-tag and --last-run are mutually exclusive.")
        exit(1)
        
    flow_description: Union[str, List[str]] = flow_name or "Classic"

    if meta := Config.get_meta(config_file, flow_override=flow_name):
        if flow_ids := meta.flow:
            flow_description = flow_ids

    TargetFlow: Type[Flow]
    
    if not isinstance(flow_description, str):
        TargetFlow = SequentialFlow.make(flow_description)
    else:
        if FlowClass := Flow.get(flow_description):
            TargetFlow = FlowClass
        else:
            err(
                f"Unknown flow '{flow_description}' specified in configuration file's 'meta' object."
            )
            exit(1)

    try:
        flow = TargetFlow.init_with_config(
            config_in=config_file,
            pdk_root=pdk_root,
            pdk=pdk,
            scl=scl,
            config_override_strings=config_override_strings,
        )
    except InvalidConfig as e:
        log(f"[green]Errors have occurred while loading the {e.config}:")
        for error in e.errors:
            err(error)
        if len(e.warnings) > 0:
            log("The following warnings have also been generated:")
            for warning in e.warnings:
                warn(warning)
        log("OpenLane will now quit. Please check your configuration.")
        exit(1)
    except ValueError as e:
        err(e)
        log("OpenLane will now quit.")
        exit(1)

    initial_state: Optional[State] = None
    if initial_state_json is not None:
        initial_state = State.loads(open(initial_state_json).read())

    if last_run:
        runs = glob.glob(os.path.join(flow.design_dir, "runs", "*"))

        latest_time: float = 0
        latest_run: Optional[str] = None
        for run in runs:
            time = os.path.getmtime(run)
            if time > latest_time:
                latest_time = time
                latest_run = run

        if latest_run is None:
            err("--last-run specified, but no runs found.")
            exit(1)

        run_tag = os.path.basename(latest_run)

    try:
        flow.start(
            tag=run_tag,
            frm=frm,
            to=to,
            with_initial_state=initial_state,
        )
    except FlowException as e:
        err(f"The flow has encountered an unexpected error: {e}")
        err("OpenLane will now quit.")
        exit(1)
    except FlowError as e:
        err(f"The following error was encountered while running the flow: {e}")
        err("OpenLane will now quit.")
        exit(2)


def print_bare_version(
    ctx: click.Context,
    param: click.Parameter,
    value: bool,
):
    if not value:
        return
    print(__version__, end="")
    ctx.exit(0)


def run_smoke_test(
    ctx: click.Context,
    param: click.Parameter,
    value: bool,
):
    if not value:
        return
    dockerized = ctx.params["dockerized"]

    with tempfile.TemporaryDirectory("_ol2design") as d:
        final_path = os.path.join(d, "spm")
        shutil.copytree(
            os.path.join(get_openlane_root(), "smoke_test_design"),
            final_path,
        )

        cmd = (
            [
                (sys.executable if not dockerized else "python3"),
                "-m",
                "openlane",
            ]
            + (["--dockerized", "--docker-mount", d] if dockerized else [])
            + [os.path.join(final_path, "config.json")]
        )

        subprocess.check_call(cmd)

    ctx.exit(0)


@click.command()
@click.version_option(
    __version__,
    prog_name="OpenLane",
    message=dedent(
        """
        %(prog)s v%(version)s

        Copyright ©2020-2023 Efabless Corporation and other contributors.

        Available under the Apache License, version 2. Included with the source code,
        but you can also get a copy at https://www.apache.org/licenses/LICENSE-2.0

        Included tools and utilities may be distributed under stricter licenses.
        """
    ).strip(),
)
@click.option(
    "--bare-version",
    is_flag=True,
    is_eager=True,
    expose_value=False,
    callback=print_bare_version,
    hidden=True,
)
@click.option(
    "--dockerized/--native",
    is_eager=True,
    default=False,
    help="Run OpenLane primarily using a Docker container. Some caveats apply.",
)
@click.option("--docker-mount", "docker_mounts", multiple=True, default=[], help="")
@click.option(
    "-p",
    "--pdk",
    type=str,
    default="sky130A",
    help="The process design kit to use. [default: sky130A]",
)
@click.option(
    "-s",
    "--scl",
    type=str,
    default=None,
    help="The standard cell library to use. [default: varies by PDK]",
)
@click.option(
    "-f",
    "--flow",
    "flow_name",
    type=click.Choice(Flow.factory.list(), case_sensitive=False),
    default=None,
    help="The built-in OpenLane flow to use",
)
@click.option(
    "--pdk-root",
    default=None,
    help="Override volare PDK root folder. Required if Volare is not installed.",
)
@click.option(
    "--volare-auto/--manual",
    "use_volare",
    default=True,
    help="Automatically use Volare for PDK version installation and enablement. Set --manual if you want to use a custom PDK version.",
)
@click.option(
    "--run-tag",
    default=None,
    type=str,
    help="An optional name to use for this particular run of an OpenLane-based flow. Mutually exclusive with --last-run.",
)
@click.option(
    "--last-run",
    is_flag=True,
    default=False,
    help="Attempt to resume the last run. Supported by sequential flows. Mutually exclusive with --run-tag.",
)
@click.option(
    "-F",
    "--from",
    "frm",
    type=str,
    default=None,
    help="Start from a step with this id. Supported by sequential flows.",
)
@click.option(
    "-T",
    "--to",
    type=str,
    default=None,
    help="Stop at a step with this id. Supported by sequential flows.",
)
@click.option(
    "-I",
    "--with-initial-state",
    "initial_state_json",
    type=str,
    default=None,
    help="Use this JSON file as an initial state. If this is not specified, the latest `state_out.json` of the run directory will be used if available.",
)
@click.option(
    "-c",
    "--override-config",
    "config_override_strings",
    type=str,
    multiple=True,
    help="For this run only- override a configuration variable with a certain value. In the format KEY=VALUE. Can be specified multiple times. Values must be valid JSON values.",
)
@click.option(
    "--smoke-test",
    is_flag=True,
    help="Runs a basic OpenLane smoke test.",
    expose_value=False,
    callback=run_smoke_test,
)
@click.argument("config_files", nargs=-1)
def cli(dockerized: bool, docker_mounts: Tuple[str], **kwargs):
    if dockerized:
        argv = sys.argv.copy()[1:]
        argv.remove("--dockerized")

        try:
            run_in_container(
                f"docker.io/donnio/openlane:{__version__}",
                ["openlane"] + argv,
                docker_mounts,
            )
        except subprocess.CalledProcessError as e:
            exit(e.returncode)

    else:
        run(**kwargs)


if __name__ == "__main__":
    cli()
