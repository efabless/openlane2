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
import glob
import shutil
import marshal
import tempfile
import traceback
import subprocess
from textwrap import dedent
from functools import partial
from typing import Tuple, Type, Optional, List, Union

import click
from cloup import (
    option,
    option_group,
    command,
    version_option,
    HelpFormatter,
    HelpTheme,
    Style,
)
from cloup.constraints import (
    If,
    IsSet,
    accept_none,
    require_one,
    mutually_exclusive,
)


from .__version__ import __version__
from .state import State
from .logging import (
    LogLevelsDict,
    set_log_level,
    err,
    warn,
    info,
)
from .common import (
    get_opdks_rev,
    get_openlane_root,
)
from .container import run_in_container
from .plugins import discovered_plugins
from .config import Config, InvalidConfig
from .flows import Flow, SequentialFlow, FlowException, FlowError


def run(
    ctx: click.Context,
    flow_name: Optional[str],
    use_volare: bool,
    pdk_root: Optional[str],
    pdk: str,
    scl: Optional[str],
    config_files: List[str],
    run_tag: Optional[str],
    last_run: bool,
    frm: Optional[str],
    to: Optional[str],
    only: Optional[str],
    skip: Tuple[str, ...],
    initial_state_json: Optional[str],
    config_override_strings: List[str],
    log_level: Union[str, int],
) -> int:
    try:
        set_log_level(log_level)
    except ValueError:
        err(f"Invalid logging level: {log_level}.")
        click.echo(ctx.get_help())
        return -1

    if only is not None:
        frm = to = only

    if use_volare:
        import volare

        pdk_root = volare.get_volare_home(pdk_root)

        volare.enable(pdk_root, pdk[:-1], get_opdks_rev())

    config_file = config_files[0]

    # Enforce Mutual Exclusion
    if run_tag is not None and last_run:
        err("--run-tag and --last-run are mutually exclusive.")
        return -1

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
            return -1

    try:
        flow = TargetFlow(
            config_file,
            pdk_root=pdk_root,
            pdk=pdk,
            scl=scl,
            config_override_strings=config_override_strings,
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
        info("OpenLane will now quit.")
        return 1

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
            return 1

        run_tag = os.path.basename(latest_run)

    try:
        flow.start(
            tag=run_tag,
            frm=frm,
            to=to,
            skip=list(skip),
            with_initial_state=initial_state,
        )
    except FlowException as e:
        err(f"The flow has encountered an unexpected error: {e}")
        err("OpenLane will now quit.")
        return 1
    except FlowError as e:
        if "deferred" not in str(e):
            err(f"The following error was encountered while running the flow: {e}")
        err("OpenLane will now quit.")
        return 2

    return 0


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

    status = 0
    d = tempfile.mkdtemp("openlane2")
    try:
        final_path = os.path.join(d, "smoke_test_design")

        # 1. Copy the files
        shutil.copytree(
            os.path.join(get_openlane_root(), "smoke_test_design"),
            final_path,
            symlinks=False,
        )

        # 2. Make files writable
        if os.name == "posix":
            subprocess.check_call(["chmod", "-R", "777", final_path])

        pdk_root = ctx.params.get("pdk_root")
        config_file = os.path.join(final_path, "config.json")

        # 3. Run
        status = run(
            ctx,
            flow_name=None,
            use_volare=True,
            pdk_root=pdk_root,
            pdk="sky130A",
            scl=None,
            config_files=[config_file],
            run_tag=None,
            last_run=False,
            frm=None,
            to=None,
            only=None,
            skip=(),
            initial_state_json=None,
            config_override_strings=[],
            log_level="VERBOSE",
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
            pass  # shutil.rmtree(d)
        except FileNotFoundError:
            pass

    ctx.exit(status)


def cli_in_container(
    ctx: click.Context,
    param: click.Parameter,
    value: bool,
):
    if not value:
        return

    status = 0
    docker_mounts = list(ctx.params.get("docker_mounts") or ())
    pdk_root = ctx.params.get("pdk_root")
    argv = sys.argv[sys.argv.index("--dockerized") + 1 :]

    interactive = True
    final_argv = ["zsh"]
    if len(argv) != 0:
        final_argv = ["python3", "-m", "openlane"] + argv
        interactive = False

    try:
        status = run_in_container(
            f"ghcr.io/efabless/openlane2:{__version__}",
            final_argv,
            pdk_root=pdk_root,
            other_mounts=docker_mounts,
            interactive=interactive,
        )
    except ValueError as e:
        print(e)
        status = -1
    except Exception:
        traceback.print_exc()
        status = -1
    finally:
        ctx.exit(status)


def print_plugins(
    ctx: click.Context,
    param: click.Parameter,
    value: bool,
):
    if not value:
        return
    print(f"openlane -> {__version__}")
    for name, module in discovered_plugins.items():
        print(f"{name} -> {module.__version__}")
    ctx.exit(0)


formatter_settings = HelpFormatter.settings(
    theme=HelpTheme(
        invoked_command=Style(fg="bright_yellow"),
        heading=Style(fg="bright_white", bold=True),
        constraint=Style(fg="magenta"),
        col1=Style(fg="bright_yellow"),
    )
)

o = partial(option, show_default=True)


@command(
    no_args_is_help=True,
    formatter_settings=formatter_settings,
)
@version_option(
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
@option_group(
    "Docker options",
    o(
        "--docker-mount",
        "docker_mounts",
        multiple=True,
        is_eager=True,
        default=[],
        help="Additionally mount this directory in dockerized mode. Can be supplied multiple times to mount multiple directories. **Must be passed before --docker.**",
    ),
    o(
        "--dockerized/--native",
        default=False,
        is_eager=True,
        help="Run command primarily using a Docker container. Some caveats apply.",
        callback=cli_in_container,
    ),
    constraint=If(~IsSet("dockerized"), accept_none),
)
@o(
    "--bare-version",
    is_flag=True,
    is_eager=True,
    expose_value=False,
    callback=print_bare_version,
    hidden=True,
)
@o(
    "--list-plugins",
    is_flag=True,
    is_eager=True,
    expose_value=False,
    callback=print_plugins,
    help="List all detected plugins for OpenLane.",
)
@o(
    "--smoke-test",
    is_flag=True,
    help="Runs a basic OpenLane smoke test.",
    callback=run_smoke_test,
)
@option_group(
    "PDK options",
    o(
        "--volare-pdk/--manual-pdk",
        "use_volare",
        default=True,
        help="Automatically use Volare for PDK version installation and enablement. Set --manual if you want to use a custom PDK version.",
    ),
    o(
        "--pdk-root",
        type=click.Path(
            exists=True,
            file_okay=False,
            dir_okay=True,
        ),
        is_eager=True,
        default=os.environ.pop("PDK_ROOT", None),
        help="Override volare PDK root folder. Required if Volare is not installed.",
    ),
    o(
        "-p",
        "--pdk",
        type=str,
        default=os.environ.pop("PDK", "sky130A"),
        help="The process design kit to use.",
    ),
    o(
        "-s",
        "--scl",
        type=str,
        default=os.environ.pop("STD_CELL_LIBRARY", None),
        help="The standard cell library to use. If None, the PDK's default standard cell library is used.",
    ),
)
@option_group(
    "Run options",
    o(
        "-f",
        "--flow",
        "flow_name",
        type=click.Choice(Flow.factory.list(), case_sensitive=False),
        default=None,
        help="The built-in OpenLane flow to use for this run",
    ),
    o(
        "-i",
        "--with-initial-state",
        "initial_state_json",
        type=click.Path(
            exists=True,
            file_okay=True,
            dir_okay=False,
        ),
        default=None,
        help="Use this JSON file as an initial state. If this is not specified, the latest `state_out.json` of the run directory will be used if available.",
    ),
    o(
        "-c",
        "--override-config",
        "config_override_strings",
        type=str,
        multiple=True,
        help="For this run only- override a configuration variable with a certain value. In the format KEY=VALUE. Can be specified multiple times. Values must be valid JSON values.",
    ),
)
@option_group(
    "Run options - tag",
    o(
        "--run-tag",
        default=None,
        type=str,
        help="An optional name to use for this particular run of an OpenLane-based flow.",
    ),
    o(
        "--last-run",
        is_flag=True,
        default=False,
        help="Use the last run as the run tag.",
    ),
    constraint=mutually_exclusive,
)
@option_group(
    "Run options - sequential flow control",
    o(
        "-F",
        "--from",
        "frm",
        type=str,
        default=None,
        help="Start from a step with this id. Supported by sequential flows.",
    ),
    o(
        "-T",
        "--to",
        type=str,
        default=None,
        help="Stop at a step with this id. Supported by sequential flows.",
    ),
    o(
        "--only",
        type=str,
        default=None,
        help="Shorthand to set both --from and --to to the same value.",
    ),
    o(
        "-S",
        "--skip",
        type=str,
        multiple=True,
        help="Skip these steps. Supported by sequential flows.",
    ),
    constraint=If(IsSet("only"), require_one),
)
@o(
    "--log-level",
    type=str,
    default="VERBOSE",
    help=dedent(
        """
        A logging level. Set to INFO or higher to silence subprocess logs.

        You can provide either a number or a string out of the following (higher is more silent):
        """
    )
    + ",".join([f"{name}={value}" for name, value in LogLevelsDict.items()]),
)
@click.argument(
    "config_files",
    nargs=-1,
    type=click.Path(
        exists=True,
        file_okay=True,
        dir_okay=True,
    ),
)
@click.pass_context
def cli(ctx: click.Context, **kwargs):
    run_kwargs = kwargs
    args = kwargs["config_files"]
    if len(args) == 1 and args[0].endswith(".marshalled"):
        run_kwargs = marshal.load(open(args[0], "rb"))
        run_kwargs.update(**{k: kwargs[k] for k in ["pdk_root", "pdk", "scl"]})
    if "smoke_test" in run_kwargs:
        del run_kwargs["smoke_test"]
    if "docker_mounts" in run_kwargs:
        del run_kwargs["docker_mounts"]
    if "dockerized" in run_kwargs:
        del run_kwargs["dockerized"]
    ctx.exit(run(ctx, **run_kwargs))


if __name__ == "__main__":
    cli()
