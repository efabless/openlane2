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
import sys
import shutil
import marshal
import tempfile
import traceback
import subprocess
from textwrap import dedent
from functools import partial
from typing import Tuple, Type, Optional, List, Union

from click import Parameter, pass_context
from cloup import (
    option,
    option_group,
    command,
    Context,
)
from cloup.constraints import (
    mutually_exclusive,
)


from .__version__ import __version__
from .state import State
from .logging import (
    debug,
    err,
    warn,
    info,
)
from . import common
from .container import run_in_container
from .plugins import discovered_plugins
from .config import Config, InvalidConfig
from .common.cli import formatter_settings
from .flows import Flow, SequentialFlow, FlowException, FlowError, cloup_flow_opts


def run(
    ctx: Context,
    flow_name: Optional[str],
    pdk_root: Optional[str],
    pdk: str,
    scl: Optional[str],
    config_files: List[str],
    tag: Optional[str],
    last_run: bool,
    frm: Optional[str],
    to: Optional[str],
    skip: Tuple[str, ...],
    reproducible: Optional[str],
    with_initial_state: Optional[State],
    config_override_strings: List[str],
    _force_run_dir: Optional[str],
    _force_design_dir: Optional[str],
    _debug: bool,
) -> int:

    config_file = config_files[0]

    # Enforce Mutual Exclusion

    flow_description: Union[str, List[str]] = flow_name or "Classic"

    if meta := Config.get_meta(config_file, flow_override=flow_name):
        if flow_ids := meta.flow:
            flow_description = flow_ids

    TargetFlow: Type[Flow]

    if not isinstance(flow_description, str):
        TargetFlow = SequentialFlow.make(flow_description)
    else:
        if FlowClass := Flow.factory.get(flow_description):
            TargetFlow = FlowClass
        else:
            err(
                f"Unknown flow '{flow_description}' specified in configuration file's 'meta' object."
            )
            return -1

    try:
        flow = TargetFlow(
            config_file,
            pdk_root=pdk_root,
            pdk=pdk,
            scl=scl,
            config_override_strings=config_override_strings,
            _force_design_dir=_force_design_dir,
        )
    except InvalidConfig as e:
        info(f"[green]Errors have occurred while loading the {e.config}.")
        for error in e.errors:
            err(error)

        if len(e.warnings) > 0:
            info("The following warnings have also been generated:")
            for warning in e.warnings:
                warn(warning)
        info("OpenLane will now quit. Please check your configuration.")
        return 1
    except ValueError as e:
        err(e)
        debug(traceback.format_exc())
        info("OpenLane will now quit.")
        return 1

    try:
        flow.start(
            tag=tag,
            last_run=last_run,
            frm=frm,
            to=to,
            skip=skip,
            with_initial_state=with_initial_state,
            reproducible=reproducible,
            _force_run_dir=_force_run_dir,
        )
    except FlowException as e:
        err(f"The flow has encountered an unexpected error: {e}")
        traceback.print_exc()
        err("OpenLane will now quit.")
        return 1
    except FlowError as e:
        if "deferred" not in str(e):
            err(f"The following error was encountered while running the flow: {e}")
        err("OpenLane will now quit.")
        return 2

    return 0


def print_version(ctx: Context, param: Parameter, value: bool):
    if not value:
        return

    message = dedent(
        f"""
        OpenLane v{__version__}

        Copyright ©2020-2023 Efabless Corporation and other contributors.

        Available under the Apache License, version 2. Included with the source code,
        but you can also get a copy at https://www.apache.org/licenses/LICENSE-2.0

        Included tools and utilities may be distributed under stricter licenses.
        """
    ).strip()

    print(message)

    if len(discovered_plugins) > 0:
        print("Discovered plugins:")
        for name, module in discovered_plugins.items():
            print(f"{name} -> {module.__version__}")

    ctx.exit(0)


def print_bare_version(
    ctx: Context,
    param: Parameter,
    value: bool,
):
    if not value:
        return
    print(__version__, end="")
    ctx.exit(0)


def run_smoke_test(
    ctx: Context,
    param: Parameter,
    value: bool,
):
    if not value:
        return

    status = 0
    d = tempfile.mkdtemp("openlane2")
    final_path = os.path.join(d, "smoke_test_design")
    try:
        # 1. Copy the files
        shutil.copytree(
            os.path.join(common.get_openlane_root(), "smoke_test_design"),
            final_path,
            symlinks=False,
        )

        # 2. Make files writable
        if os.name == "posix":
            subprocess.check_call(["chmod", "-R", "777", final_path])

        pdk_root = ctx.params.get("pdk_root")
        if ctx.obj["use_volare"]:
            import volare

            pdk_root = volare.get_volare_home(ctx.params.get("pdk_root"))
            common.mkdirp(pdk_root)
            volare.enable(pdk_root, "sky130", common.get_opdks_rev())

        config_file = os.path.join(final_path, "config.json")

        # 3. Run
        status = run(
            ctx,
            flow_name=None,
            pdk_root=pdk_root,
            pdk="sky130A",
            scl=None,
            config_files=[config_file],
            tag=None,
            last_run=False,
            frm=None,
            to=None,
            reproducible=None,
            skip=(),
            with_initial_state=None,
            config_override_strings=[],
            _force_run_dir=None,
            _force_design_dir=None,
            _debug=False,
        )
        if status == 0:
            info("Smoke test passed.")
        else:
            err("Smoke test failed.")
    except KeyboardInterrupt:
        info("Smoke test aborted.")
        status = -1
    finally:
        try:
            shutil.rmtree(final_path)
        except FileNotFoundError:
            pass

    ctx.exit(status)


def cli_in_container(
    ctx: Context,
    param: Parameter,
    value: bool,
):
    if not value:
        return

    status = 0
    docker_mounts = list(ctx.params.get("docker_mounts") or ())
    docker_tty: bool = ctx.params.get("docker_tty", True)
    pdk_root = ctx.params.get("pdk_root")
    argv = sys.argv[sys.argv.index("--dockerized") + 1 :]

    interactive = True
    final_argv = ["zsh"]
    if len(argv) != 0:
        final_argv = ["openlane"] + argv
        interactive = False

    docker_image = os.getenv(
        "OPENLANE_IMAGE_OVERRIDE", f"ghcr.io/efabless/openlane2:{__version__}"
    )

    try:
        status = run_in_container(
            docker_image,
            final_argv,
            pdk_root=pdk_root,
            other_mounts=docker_mounts,
            interactive=interactive,
            tty=docker_tty,
        )
    except ValueError as e:
        print(e)
        status = -1
    except Exception:
        traceback.print_exc()
        status = -1
    finally:
        ctx.exit(status)


o = partial(option, show_default=True)


@command(
    no_args_is_help=True,
    formatter_settings=formatter_settings,
)
@option_group(
    "Containerization options",
    o(
        "--docker-mount",
        "-m",
        "docker_mounts",
        multiple=True,
        is_eager=True,  # docker options should be processed before anything else
        default=(),
        help="Used to mount more directories in dockerized mode. If a valid directory is specified, it will be mounted in the same path in the container. Otherwise, the value of the option will be passed to the Docker-compatible container engine verbatim. Must be passed before --dockerized, has no effect if --dockerized is not set.",
    ),
    o(
        "--docker-tty/--docker-no-tty",
        is_eager=True,  # docker options should be processed before anything else
        default=True,
        help="Controls the allocation of a virtual terminal by passing -t to the Docker-compatible container engine invocation. Must be passed before --dockerized, has no effect if --dockerized is not set.",
    ),
    o(
        "--dockerized",
        default=False,
        is_flag=True,
        is_eager=True,  # ddocker options should be processed before anything else
        help="Run the remaining flags using a Docker container. Some caveats apply. Must precede all options except --docker-mount, --docker-tty/--docker-no-tty.",
        callback=cli_in_container,
    ),
)
@option_group(
    "Subcommands",
    o(
        "--version",
        is_flag=True,
        is_eager=True,
        help="Prints version information and exits",
        callback=print_version,
    ),
    o(
        "--bare-version",
        is_flag=True,
        is_eager=True,
        callback=print_bare_version,
        hidden=True,
    ),
    o(
        "--smoke-test",
        is_flag=True,  # Cannot be eager- PDK options need to be processed
        help="Runs a basic OpenLane smoke test.",
        callback=run_smoke_test,
    ),
    constraint=mutually_exclusive,
)
@cloup_flow_opts(_enable_debug_flags=True, sequential_flow_reproducible=True)
@pass_context
def cli(ctx, /, **kwargs):
    """
    Runs an OpenLane flow via the commandline using a design configuration
    object.

    Try 'python3 -m openlane.steps --help' for step-specific options, including
    reproducibles and running a step standalone.
    """
    args = kwargs["config_files"]
    run_kwargs = kwargs.copy()

    if len(args) == 1 and args[0].endswith(".marshalled"):
        run_kwargs = marshal.load(open(args[0], "rb"))
        run_kwargs.update(**{k: kwargs[k] for k in ["pdk_root", "pdk", "scl"]})

    for subcommand_flag in [
        "docker_tty",
        "docker_mounts",
        "dockerized",
        "version",
        "bare_version",
        "smoke_test",
    ]:
        if subcommand_flag in run_kwargs:
            del run_kwargs[subcommand_flag]

    ctx.exit(run(ctx, **run_kwargs))


if __name__ == "__main__":
    cli()
