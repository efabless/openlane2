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
from decimal import Decimal
from typing import List, Sequence, Tuple, Optional, Callable, Union, Dict

from .resolve import resolve, Keys
from .pdk import (
    all_variables as pdk_variables,
    removed_variables as pdk_removed_variables,
    migrate_old_config,
)
from .flow import removed_variables
from .tcleval import env_from_tcl
from .config import Config, Meta
from .variable import Variable
from ..common import internal, log, warn


class InvalidConfig(ValueError):
    """
    An error raised when a configuration under resolution is invalid.

    :param config: A human-readable name for the particular configuration file
        causing this exception, i.e. whether it's a PDK configuration file or a
        user configuration file.
    :param warnings: A list of warnings generated during the loading of this
        configuration file.
    :param errors: A list of errors generated during the loading of this
        configuration file.
    :param args: Further arguments to be passed onto the constructor of
        :class:`ValueError`.
    :param kwargs: Further keyword arguments to be passed onto the constructor of
        :class:`ValueError`.
    """

    def __init__(
        self,
        config: str,
        warnings: List[str],
        errors: List[str],
        *args,
        **kwargs,
    ) -> None:
        self.config = config
        self.warnings = warnings
        self.errors = errors
        super().__init__(*args, **kwargs)


class DecimalDecoder(json.JSONDecoder):
    def default(self, o):
        if isinstance(o, float) or isinstance(o, int):
            return Decimal(o)
        return super(DecimalDecoder, self).default(o)


class ConfigBuilder(object):
    """
    Construct a full, validated and resolved OpenLane configuration object
    from a user configuration + the various associated default values.
    """

    @classmethod
    def load(
        Self,
        config_in: Union[str, os.PathLike, Dict],
        flow_config_vars: Sequence[Variable],
        config_override_strings: Optional[Sequence[str]] = None,
        pdk: Optional[str] = None,
        pdk_root: Optional[str] = None,
        scl: Optional[str] = None,
        design_dir: Optional[str] = None,
    ) -> Tuple["Config", str]:
        """
        :param config_in: Either a file path to a JSON file or a Python
            dictionary representing an unprocessed OpenLane configuration
            object.

            Tcl files are also supported, but are deprecated and will be removed
            in the future.

        :param config_override_strings: A list of "overrides" in the form of
            NAME=VALUE strings. These are primarily for running OpenLane from
            the commandline and strictly speaking should not be used in the API.

        :param design_dir: The design directory for said configuration.
            Supported and required *if and only if* config_in is a dictionary.

        :param pdk: A process design kit to use. Could also be specified via the
            "PDK" key in a configuration object, in which case this parameter is
            optional.

        :param pdk_root: Required if Volare is not installed.

            If Volare is installed, this value can be used to optionally override
            Volare's default.

        :param scl: A standard cell library to use. If not specified, the PDK's
            default standard cell library will be used instead.

        :returns: A tuple containing a ConfigBuilder and the design directory.
        """

        loader: Callable = Self.loads
        raw: Union[str, dict] = ""
        if not isinstance(config_in, dict):
            if design_dir is not None:
                raise TypeError(
                    "The argument design_dir is not supported when config_in is not a dictionary."
                )

            design_dir = str(os.path.dirname(config_in))
            config_in = str(config_in)
            if config_in.endswith(".json"):
                raw = open(config_in, encoding="utf8").read()
            elif config_in.endswith(".tcl"):
                raw = open(config_in, encoding="utf8").read()
                loader = Self.loads_tcl
                if config_override_strings is None:
                    raise ValueError(
                        "CLI override strings are not supported with .Tcl configuration files."
                    )
            else:
                if os.path.isdir(config_in):
                    raise ValueError(
                        "Passing design folders as arguments is unsupported in OpenLane 2.0+: please pass the JSON configuration file directly."
                    )
                _, ext = os.path.splitext(config_in)
                raise ValueError(
                    f"Unsupported configuration file extension '{ext}' for '{config_in}'."
                )
        else:
            if design_dir is None:
                raise TypeError(
                    "The argument design_dir is required when using ConfigBuilder with a dictionary."
                )
            raw = config_in
            loader = Self.load_dict

        loaded = loader(
            raw,
            design_dir,
            flow_config_vars=flow_config_vars,
            pdk=pdk,
            pdk_root=pdk_root,
            scl=scl,
            config_override_strings=(config_override_strings or []),
        )

        return (loaded, design_dir)

    @classmethod
    def loads(
        Self,
        json_str: str,
        *args,
        **kwargs,
    ):
        raw = json.loads(json_str, cls=DecimalDecoder)
        kwargs["resolve_json"] = True
        return Self.load_dict(
            raw,
            *args,
            **kwargs,
        )

    @internal
    @classmethod
    def load_dict(
        Self,
        raw: dict,
        design_dir: str,
        flow_config_vars: Sequence[Variable],
        config_override_strings: Sequence[str],
        pdk: Optional[str] = None,
        pdk_root: Optional[str] = None,
        scl: Optional[str] = None,
        full_pdk_warnings: bool = False,
        resolve_json: bool = False,
    ) -> "Config":

        meta_raw: Optional[dict] = None
        if raw.get("meta") is not None:
            meta_raw = raw["meta"]
            del raw["meta"]

        for string in config_override_strings:
            key, value = string.split("=", 1)
            raw[key] = value

        process_info = resolve(
            raw,
            only_extract_process_info=True,
            design_dir=design_dir,
        )

        try:
            import volare

            pdk_root = volare.get_volare_home(pdk_root)
        except ImportError:
            if pdk_root is None:
                raise ValueError(
                    "The pdk_root argument is required as Volare is not installed."
                )

        pdk = process_info.get(Keys.pdk) or pdk
        if pdk is None:
            raise ValueError(
                "The pdk argument is required as the configuration object lacks a 'PDK' key."
            )

        config_in = Config(
            {
                "PDK_ROOT": pdk_root,
                Keys.pdk: pdk,
            }
        )
        if scl is not None:
            config_in[Keys.scl] = scl

        pdkpath = os.path.join(pdk_root, pdk)
        pdk_config_path = os.path.join(pdkpath, "libs.tech", "openlane", "config.tcl")

        config_in = env_from_tcl(
            config_in,
            open(pdk_config_path, encoding="utf8").read(),
        )

        scl = config_in["STD_CELL_LIBRARY"]
        assert (
            scl is not None
        ), "Fatal error: STD_CELL_LIBRARY default value not set by PDK."

        scl_config_path = os.path.join(
            pdkpath, "libs.tech", "openlane", scl, "config.tcl"
        )
        config_in = migrate_old_config(
            env_from_tcl(
                config_in,
                open(scl_config_path, encoding="utf8").read(),
            )
        )

        config_in, pdk_warnings, pdk_errors = Variable.process_config(
            config_in,
            pdk_variables,
            pdk_removed_variables,
        )

        if len(pdk_errors) != 0:
            raise InvalidConfig("PDK configuration files", pdk_warnings, pdk_errors)

        if len(pdk_warnings) > 0:
            if full_pdk_warnings:
                log(
                    "Loading the PDK configuration files has generated the following warnings:"
                )
                for warning in pdk_warnings:
                    warn(warning)

        resolve_maybe = resolve if resolve_json else lambda x, *args, **kwargs: x

        resolved = resolve_maybe(
            raw,
            pdk=pdk,
            pdkpath=pdkpath,
            scl=scl,
            design_dir=design_dir,
        )

        config_in.update(**resolved)

        config_in, design_warnings, design_errors = Variable.process_config(
            config_in,
            pdk_variables + list(flow_config_vars),
            removed_variables,
        )

        if meta_raw is not None:
            try:
                config_in.meta = Meta(**meta_raw)
            except TypeError as e:
                design_errors.append(f"'meta' object is invalid: {e}")

        if len(design_errors) != 0:
            raise InvalidConfig(
                "design configuration file", design_warnings, design_errors
            )

        if len(design_warnings) > 0:
            log(
                "Loading the design configuration file has generated the following warnings:"
            )
        for warning in design_warnings:
            warn(warning)

        config_in["PDK_ROOT"] = pdk_root
        return config_in

    @internal
    @classmethod
    def loads_tcl(
        Self,
        config: str,
        design_dir: str,
        flow_config_vars: Sequence[Variable],
        config_override_strings: Sequence[str],  # Unused, kept for API consistency
        pdk: Optional[str] = None,
        pdk_root: Optional[str] = None,
        scl: Optional[str] = None,
        full_pdk_warnings: bool = False,
    ) -> "Config":
        warn(
            "Support for .tcl configuration files is deprecated. Please migrate to a .json file at your earliest convenience."
        )

        try:
            import volare

            pdk_root = volare.get_volare_home(pdk_root)
        except ImportError:
            if pdk_root is None:
                raise ValueError(
                    "The pdk_root argument is required as Volare is not installed."
                )

        config_in = Config(
            {
                "PDK_ROOT": pdk_root,
                Keys.pdk: pdk,
            }
        )

        tcl_vars_in = config_in.copy()
        tcl_vars_in[Keys.scl] = ""
        tcl_vars_in[Keys.design_dir] = design_dir
        tcl_config = env_from_tcl(tcl_vars_in, config)

        process_info = resolve(
            tcl_config.data,
            only_extract_process_info=True,
            design_dir=design_dir,
        )

        pdk = process_info.get(Keys.pdk) or pdk

        if pdk is None:
            raise ValueError(
                "The pdk argument is required as the configuration object lacks a 'PDK' key."
            )

        if scl is not None:
            config_in[Keys.scl] = scl

        pdkpath = os.path.join(pdk_root, pdk)
        pdk_config_path = os.path.join(pdkpath, "libs.tech", "openlane", "config.tcl")

        config_in = env_from_tcl(
            config_in,
            open(pdk_config_path, encoding="utf8").read(),
        )

        scl = config_in["STD_CELL_LIBRARY"]
        assert (
            scl is not None
        ), "Fatal error: STD_CELL_LIBRARY default value not set by PDK."

        scl_config_path = os.path.join(
            pdkpath, "libs.tech", "openlane", scl, "config.tcl"
        )
        config_in = env_from_tcl(
            config_in,
            open(scl_config_path, encoding="utf8").read(),
        )

        config_in = migrate_old_config(
            env_from_tcl(
                config_in,
                open(scl_config_path, encoding="utf8").read(),
            )
        )

        config_in, pdk_warnings, pdk_errors = Variable.process_config(
            config_in,
            pdk_variables,
            pdk_removed_variables,
        )

        if len(pdk_errors) != 0:
            raise InvalidConfig("PDK configuration files", pdk_warnings, pdk_errors)

        if len(pdk_warnings) > 0:
            if full_pdk_warnings:
                log(
                    "Loading the PDK configuration files has generated the following warnings:"
                )
                for warning in pdk_warnings:
                    warn(warning)

        tcl_vars_in[Keys.pdk] = pdk
        tcl_vars_in[Keys.scl] = scl
        tcl_vars_in[Keys.design_dir] = design_dir

        design_config = env_from_tcl(tcl_vars_in, config)

        config_in.update(**design_config)

        config_in, design_warnings, design_errors = Variable.process_config(
            config_in,
            pdk_variables + list(flow_config_vars),
            removed_variables,
        )

        if len(design_errors) != 0:
            raise InvalidConfig(
                "design configuration file", design_warnings, design_errors
            )

        if len(design_warnings) > 0:
            log(
                "Loading the design configuration file has generated the following warnings:"
            )
        for warning in design_warnings:
            warn(warning)

        config_in["PDK_ROOT"] = pdk_root

        return config_in
