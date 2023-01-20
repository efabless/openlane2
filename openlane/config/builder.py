import os
import json
from decimal import Decimal
from typing import List, Tuple, Optional

import volare

from .resolve import resolve, Keys
from .tcleval import env_from_tcl
from .config import Config
from .pdk import validate_pdk_config
from .flow import validate_user_config
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
    def load(Self, file_path: str, *args, **kwargs) -> Tuple["Config", str]:
        design_dir = os.path.dirname(file_path)
        return (
            Self.loads(
                open(file_path, encoding="utf8").read(),
                design_dir,
                *args,
                **kwargs,
            ),
            design_dir,
        )

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

        print(pdk_root, pdk)
        pdkpath = os.path.join(pdk_root, pdk)
        pdk_config_path = os.path.join(pdkpath, "libs.tech", "openlane", "config.tcl")
        config_in = env_from_tcl(config_in, pdk_config_path)

        scl = config_in["STD_CELL_LIBRARY"]
        sclpath = os.path.join(pdkpath, "libs.ref", scl)
        scl_config_path = os.path.join(
            pdkpath, "libs.tech", "openlane", scl, "config.tcl"
        )
        config_in = env_from_tcl(config_in, scl_config_path)

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

        return config_in
