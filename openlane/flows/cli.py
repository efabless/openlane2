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
from functools import partial
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Union


from click import Parameter, echo
from cloup import (
    option,
    argument,
    option_group,
    Context,
    Choice,
    Path,
)
from cloup.constraints import (
    mutually_exclusive,
)
from cloup.typing import Decorator

from .flow import Flow
from ..common import set_tpe, get_opdks_rev, cli
from ..logging import set_log_level, verbose, err, options, LogLevels
from ..state import State, InvalidState


def set_log_level_cb(
    ctx: Context,
    param: Parameter,
    value: Optional[str],
):
    if value is None:
        return

    level: Union[str, int] = value
    try:
        try:
            level = int(value)
        except ValueError:
            pass
        set_log_level(level)
    except ValueError as e:
        err(f"Invalid logging level {value}: {e}.")
        echo(ctx.get_help())
        ctx.exit(-1)


def set_worker_count_cb(
    ctx: Context,
    param: Parameter,
    value: Optional[int],
):
    if value is None:
        return None

    set_tpe(ThreadPoolExecutor(max_workers=value))


def initial_state_cb(
    ctx: Context,
    param: Parameter,
    value: Optional[str],
):
    if value is None:
        return None

    try:
        initial_state_str = open(value, encoding="utf8").read()
    except Exception as e:
        err(f"Failed to read initial state: {e}")
        ctx.exit(-1)
    try:
        initial_state = State.loads(initial_state_str, validate_path=True)
    except InvalidState as e:
        err(e)
        ctx.exit(-1)

    return initial_state


def only_cb(
    ctx: Context,
    param: Parameter,
    value: Optional[str],
):
    if value is not None:
        ctx.obj = ctx.obj or {}
        ctx.obj["only"] = value
    return value


def from_to_cb(
    ctx: Context,
    param: Parameter,
    value: Optional[str],
):
    if isinstance(ctx.obj, dict) and ctx.obj.get("only"):
        return ctx.obj.get("only")
    return value


def use_volare_cb(
    ctx: Context,
    param: Parameter,
    value: bool,
):
    ctx.obj = ctx.obj or {}
    ctx.obj["use_volare"] = value


def pdk_scl_cb(
    ctx: Context,
    param: Parameter,
    value: Optional[str],
):
    if param.name is None:
        return

    values = ctx.params.copy()
    values[param.name] = value
    if "pdk" in values and "scl" in values:
        pdk = values["pdk"]
        if ctx.obj and ctx.obj.get("use_volare"):
            import volare

            volare_home = volare.get_volare_home(values["pdk_root"])

            include_libraries = ["default"]
            if scl := values["scl"]:
                include_libraries.append(scl)

            pdk_family = None
            if family := volare.Family.by_name.get(pdk):
                ctx.params["pdk"] = family.default_variant
                pdk_family = family.name
                verbose(f"Resolved PDK variant {family.default_variant}.")
            else:
                for family in volare.Family.by_name.values():
                    if pdk in family.variants:
                        pdk_family = family.name
                        break

            if pdk_family is None:
                err(f"Could not resolve the PDK '{ctx.params['pdk']}'.")
                ctx.exit(1)

            version = volare.fetch(
                volare_home,
                pdk_family,
                get_opdks_rev(),
                include_libraries=include_libraries,
            )
            ctx.params["pdk_root"] = version.get_dir(volare_home)
    return value


def condensed_cb(ctx: Context, param: Parameter, value: bool):
    if value:
        options.set_condensed_mode(True)
        options.set_show_progress_bar(False)


def progressbar_cb(ctx: Context, param: Parameter, value: Optional[bool]):
    if value is not None:
        options.set_show_progress_bar(value)


def cloup_flow_opts(
    *,
    config_options: bool = True,
    run_options: bool = True,
    sequential_flow_controls: bool = True,
    sequential_flow_reproducible: bool = False,
    pdk_options: bool = True,
    log_level: bool = True,
    jobs: bool = True,
    accept_config_files: bool = True,
    volare_by_default: bool = True,
    _enable_debug_flags: bool = False,
) -> Decorator:
    """
    Creates a wrapper that appends a number of OpenLane flow-related flags to a
    function decorated with @cloup.command (https://cloup.readthedocs.io/en/stable/autoapi/cloup/index.html#cloup.command).

    The following keyword arguments will be passed to the decorated function.
    * Those postfixed ‡ are compatible with the constructor for :class:`Flow`.
    * Those postfixed § are compatible with the :meth:`Flow.start`.

    * Flow configuration options (if parameter ``config_options`` is ``True``):
        * ``flow_name``: ``Optional[str]``: A valid flow ID to be used with :meth:`Flow.factory.get`
        * ``config_override_strings``‡: ``Optional[Iterable[str]]``
    * Sequential flow controls (if parameter ``sequential_flow_controls`` is ``True``)
        * ``frm``§: ``Optional[str]``: Start from a step with this ID. Supported by sequential flows.
        * ``to``§: ``Optional[str]``: Stop at a step with this id. Supported by sequential flows.
        * ``skip``§: ``Iterable[str]``: Skip these steps. Supported by sequential flows.
    * Sequential flow reproducible (if parameter ``sequential_flow_reproducible`` is ``True``)
        * ``reproducible``§: ``str``: Create a reproducible for a step with is ID, aborting the flow afterwards. Supported by sequential flows.
    * Flow run options (if parameter ``run_options`` is ``True``):
        * ``tag``§: ``Optional[str]``
        * ``last_run``§: ``bool``: If ``True``, ``tag`` is guaranteed to be None.
        * ``with_initial_state``§: ``Optional[State]``
    * PDK options
        * ``use_volare``: ``bool``
        * ``pdk_root``‡: ``Optional[str]``
        * ``pdk``‡: ``str``
        * ``scl``‡: ``Optional[str]``
    * ``config_files``: ``Iterable[str]``: Paths to configuration files (if
      parameter  ``accept_config_files`` is ``True``)

    :param config_options: Enables flow configuration and starting CLI flags
    :param sequential_flow_controls: Enables flow control CLI flags
    :param flow_run_options: Enables tag CLI flags
    :param pdk_options: Enables PDK CLI flags
    :param log_level: Enables ``--log-level`` CLI flag
    :param jobs: Enables ``-j/--jobs`` CLI flag
    :param accept_config_files: Accepts configuration file paths as CLI arguments
    :param volare_by_default: If ``pdk_options`` is ``True``, this changes whether
        Volare is used by default for this CLI or not.
    :returns: The wrapper
    """
    o = partial(option, show_default=True)

    def decorator(f):
        if config_options:
            f = option_group(
                "Flow configuration options",
                o(
                    "-f",
                    "--flow",
                    "flow_name",
                    type=Choice(Flow.factory.list(), case_sensitive=False),
                    default=None,
                    help="The built-in OpenLane flow to use for this run",
                ),
                o(
                    "-c",
                    "--override-config",
                    "config_override_strings",
                    type=str,
                    multiple=True,
                    help="For this run only- override a configuration variable with a certain value. In the format KEY=VALUE. Can be specified multiple times. Values must be valid JSON values, and keys must not use their deprecated names.",
                ),
            )(f)
        if run_options:
            f = o(
                "-i",
                "--with-initial-state",
                type=Path(
                    exists=True,
                    file_okay=True,
                    dir_okay=False,
                ),
                default=None,
                callback=initial_state_cb,
                help="Use this JSON file as an initial state. If this is not specified, the latest `state_out.json` of the run directory will be used if available.",
            )(f)
            f = o(
                "--design-dir",
                "design_dir",
                type=Path(
                    exists=True,
                    file_okay=False,
                    dir_okay=True,
                ),
                default=None,
                help="The top-level directory for your design that configuration objects may resolve paths relative to.",
            )(f)
            if _enable_debug_flags:
                f = option_group(
                    "Debug flags",
                    o(
                        "--force-run-dir",
                        "_force_run_dir",
                        type=Path(
                            exists=True,
                            file_okay=False,
                            dir_okay=True,
                        ),
                        hidden=True,
                        default=None,
                    ),
                )(f)
            f = option_group(
                "Run options",
                o(
                    "--run-tag",
                    "tag",
                    default=None,
                    type=str,
                    help="An optional name to use for this particular run of an OpenLane-based flow. Used to create the run directory.",
                ),
                o(
                    "--last-run",
                    is_flag=True,
                    default=False,
                    help="Use the last run as the run tag.",
                ),
                constraint=mutually_exclusive,
            )(f)
        if sequential_flow_controls:
            f = option_group(
                "Sequential flow controls",
                o(
                    "-F",
                    "--from",
                    "frm",
                    type=str,
                    default=None,
                    callback=from_to_cb,
                    help="Start from a step with this id. Supported by sequential flows.",
                ),
                o(
                    "-T",
                    "--to",
                    type=str,
                    default=None,
                    callback=from_to_cb,
                    help="Stop at a step with this id. Supported by sequential flows.",
                ),
                o(
                    "--only",
                    type=str,
                    default=None,
                    expose_value=False,
                    is_eager=True,
                    callback=only_cb,
                    help="Shorthand to set both --from and --to to the same value. Overrides the values from both.",
                ),
                o(
                    "-S",
                    "--skip",
                    type=str,
                    multiple=True,
                    help="Skip these steps. Supported by sequential flows.",
                ),
            )(f)
        if sequential_flow_reproducible:
            f = o(
                "--reproducible",
                type=str,
                help="Create a reproducible for the step matching this ID, then abort the flow. Supported by sequential flows.",
            )(f)
        if log_level:
            f = o(
                "--log-level",
                type=cli.IntEnumChoice(LogLevels),
                default=None,
                help="A logging level. Set to VERBOSE or higher to silence subprocess logs. [default: unchanged from SUBPROCESS]",
                callback=set_log_level_cb,
                expose_value=False,
                show_default=False,
            )(f)
            f = o(
                "--show-progress-bar/--hide-progress-bar",
                type=bool,
                help="Whether to show the progress bar when running Flows. [default: show]",
                default=None,
                callback=progressbar_cb,
                expose_value=False,
            )(f)
            f = o(
                "--condensed/--full",
                type=bool,
                help="In condensed mode, subprocess logs are suppressed regardless of step, --hide-progress-bar is the default, and the log messages themselves are a bit more terse. Useful for debugging.",
                default=False,
                is_eager=True,
                callback=condensed_cb,
                expose_value=False,
            )(f)
        if pdk_options:
            f = option_group(
                "PDK options",
                o(
                    "--volare-pdk/--manual-pdk",
                    "use_volare",
                    is_eager=True,
                    default=volare_by_default,
                    help="Automatically use Volare for PDK version installation and enablement. Set --manual if you want to use a custom PDK version.",
                    expose_value=False,
                    callback=use_volare_cb,
                ),
                o(
                    "--pdk-root",
                    type=Path(
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
                    callback=pdk_scl_cb,
                ),
                o(
                    "-s",
                    "--scl",
                    type=str,
                    default=os.environ.pop("STD_CELL_LIBRARY", None),
                    help="The standard cell library to use. If None, the PDK's default standard cell library is used.",
                    callback=pdk_scl_cb,
                ),
            )(f)
        if jobs:
            f = o(
                "-j",
                "--jobs",
                type=int,
                default=os.cpu_count(),
                help="The maximum number of threads or processes that can be used by OpenLane.",
                callback=set_worker_count_cb,
                expose_value=False,
            )(f)
        if accept_config_files:
            f = argument(
                "config_files",
                nargs=-1,
                type=Path(
                    exists=True,
                    file_okay=True,
                    dir_okay=True,
                ),
            )(f)
        return f

    return decorator
