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
from typing import List, Tuple, Optional, Callable

import volare

from .resolve import resolve, Keys
from .tcleval import env_from_tcl
from .config import Config, Meta
from .pdk import validate_pdk_config, PDKVariablesByID
from .flow import validate_user_config, FlowVariablesByID
from ..common import log, warn


class InvalidConfig(ValueError):
    def __init__(
        self,
        config: str,
        warnings: List[str],
        errors: List[str],
        *args: object,
    ) -> None:
        self.config = config
        self.warnings = warnings
        self.errors = errors
        super().__init__(*args)


class DecimalDecoder(json.JSONDecoder):
    def default(self, o):
        if isinstance(o, float) or isinstance(o, int):
            return Decimal(o)
        return super(DecimalDecoder, self).default(o)


class ConfigBuilder(object):
    @classmethod
    def load(
        Self,
        file_path: str,
        config_override_strings: List[str],
        *args,
        **kwargs,
    ) -> Tuple["Config", str]:
        design_dir = os.path.dirname(file_path)

        loader: Callable = Self.loads
        if file_path.endswith(".json"):
            pass
        elif file_path.endswith(".tcl"):
            loader = Self.loads_tcl
        else:
            if os.path.isdir(file_path):
                raise ValueError(
                    "Passing design folders as arguments is unsupported in OpenLane 2.0+: please pass the JSON configuration file directly."
                )
            _, ext = os.path.splitext(file_path)
            raise ValueError(
                f"Unsupported configuration file extension '{ext}' for '{file_path}'."
            )

        loaded = loader(
            open(file_path, encoding="utf8").read(),
            design_dir,
            *args,
            **kwargs,
        )

        for string in config_override_strings:
            components = string.split("=", 2)
            if len(components) != 2:
                raise TypeError(
                    f"Config override string '{components}' is invalid: no = found."
                )
            name, value_raw = components
            variable = PDKVariablesByID.get(name) or FlowVariablesByID.get(name)
            if variable is None:
                warn(f"Unknown configuration override variable '{name}'.")
                continue
            value = json.loads(value_raw)
            value_verified = variable.process(value)
            loaded[name] = value_verified

        return (loaded, design_dir)

    @classmethod
    def loads(
        Self,
        json_str: str,
        design_dir: str,
        pdk: str,
        pdk_root: Optional[str] = None,
        scl: Optional[str] = None,
    ) -> "Config":
        raw = json.loads(json_str, cls=DecimalDecoder)

        meta_raw: Optional[dict] = None
        if raw.get("meta") is not None:
            meta_raw = raw["meta"]
            del raw["meta"]

        process_info = resolve(
            raw,
            only_extract_process_info=True,
            design_dir=design_dir,
        )
        pdk_root = volare.get_volare_home(pdk_root)
        pdk = process_info.get(Keys.pdk) or pdk
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

        sclpath = os.path.join(pdkpath, "libs.ref", scl)
        scl_config_path = os.path.join(
            pdkpath, "libs.tech", "openlane", scl, "config.tcl"
        )
        config_in = env_from_tcl(
            config_in,
            open(scl_config_path, encoding="utf8").read(),
        )

        config_in, pdk_warnings, pdk_errors = validate_pdk_config(
            config_in, ["PDK_ROOT", "PDK", "STD_CELL_LIBRARY"]
        )

        if len(pdk_errors) != 0:
            raise InvalidConfig("PDK configuration files", pdk_warnings, pdk_errors)

        if len(pdk_warnings) > 0:
            log(
                "Loading the PDK configuration files has generated the following warnings:"
            )
        for warning in pdk_warnings:
            warn(warning)

        design_config = Config(
            **resolve(
                raw,
                pdk=pdk,
                pdkpath=pdkpath,
                scl=scl,
                sclpath=sclpath,
                design_dir=design_dir,
            )
        )

        config_in, design_warnings, design_errors = validate_user_config(
            design_config,
            ["DESIGN_DIR", "PDK_ROOT", "PDK", "PDKPATH", "SCLPATH", "STD_CELL_LIBRARY"],
            config_in,
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

    @classmethod
    def loads_tcl(
        Self,
        config: str,
        design_dir: str,
        pdk: str,
        pdk_root: Optional[str] = None,
        scl: Optional[str] = None,
    ) -> "Config":
        warn(
            "Support for .tcl configuration files is deprecated. Please migrate to a .json file at your earliest convenience."
        )

        pdk_root = volare.get_volare_home(pdk_root)
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

        config_in, pdk_warnings, pdk_errors = validate_pdk_config(
            config_in,
            ["PDK_ROOT", "PDK", "STD_CELL_LIBRARY", "DESIGN_DIR", "DESIGN_NAME"],
        )

        if len(pdk_errors) != 0:
            raise InvalidConfig("PDK configuration files", pdk_warnings, pdk_errors)

        if len(pdk_warnings) > 0:
            log(
                "Loading the PDK configuration files has generated the following warnings:"
            )
        for warning in pdk_warnings:
            warn(warning)

        tcl_vars_in[Keys.pdk] = pdk
        tcl_vars_in[Keys.scl] = scl
        tcl_vars_in[Keys.design_dir] = design_dir

        design_config = env_from_tcl(tcl_vars_in, config)

        config_in, design_warnings, design_errors = validate_user_config(
            design_config,
            ["DESIGN_DIR", "PDK_ROOT", "PDK", "PDKPATH", "SCLPATH", "STD_CELL_LIBRARY"],
            config_in,
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
