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
import yaml
import dataclasses
from glob import glob
from decimal import Decimal
from textwrap import dedent
from functools import lru_cache
from dataclasses import dataclass
from typing import (
    Any,
    ClassVar,
    Literal,
    Mapping,
    Tuple,
    Union,
    List,
    Optional,
    Sequence,
    Callable,
    Dict,
    Set,
)

from immutabledict import immutabledict

from .variable import Variable
from .removals import removed_variables
from .flow import pdk_variables, scl_variables, flow_common_variables
from .pdk_compat import migrate_old_config
from .preprocessor import preprocess_dict, Keys as SpecialKeys
from ..logging import info, warn
from ..__version__ import __version__
from ..common import GenericDict, GenericImmutableDict, TclUtils, Path


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
    :param message: An optional override for the Exception message.
    :param kwargs: Further keyword arguments to be passed onto the constructor of
        :class:`ValueError`.
    """

    def __init__(
        self,
        config: str,
        warnings: List[str],
        errors: List[str],
        message: Optional[str] = None,
        *args,
        **kwargs,
    ) -> None:
        self.config = config
        self.warnings = warnings
        self.errors = errors
        if message is None:
            message = "The following errors were encountered: \n"
            for error in self.errors:
                message += f"\t* {error}"
        super().__init__(message, *args, **kwargs)


@dataclass
class Meta:
    """
    Constitutes metadata for a configuration object.
    """

    version: int = 1
    flow: Union[None, str, List[str]] = None
    step: Union[None, str] = None
    openlane_version: Union[None, str] = __version__

    def copy(self) -> "Meta":
        return dataclasses.replace(self)


class Config(GenericImmutableDict[str, Any]):
    """
    A map from OpenLane configuration variable keys to their values.

    It is recommended that you use :meth:`load` to create new, validated
    configurations from dictionaries or files.

    :param meta: The :class:`Meta` object for this configuration. If ``None`` is
        passed, the default Meta object will be assigned.
    :param final: Whether the configuration is final (i.e. has been
        pre-assembled for an entire flow) or may be incremented per-step.

        Final configurations may not be adjusted or incremented.

    """

    current_interactive: ClassVar[Optional["Config"]] = None
    meta: Meta

    def __init__(
        self,
        *args,
        meta: Optional[Meta] = None,
        **kwargs,
    ):
        if meta is None:
            meta = Meta(version=1)

        self.meta = meta

        super().__init__(*args, **kwargs)

    def copy(self, **overrides) -> "Config":
        """
        Produces a *shallow* copy of the configuration object.

        :param overrides: A series of configuration overrides as key-value pairs.
            These values are NOT validated and you should not be overriding these
            haphazardly.
        """
        return Config(self, meta=self.meta, overrides=overrides)

    def to_raw_dict(self, include_meta: bool = True) -> Dict[str, Any]:
        """
        :param include_meta: Whether to include the "meta" object or not
        :returns: A raw dictionary representation including the ``meta`` object.
        """
        final = super().to_raw_dict()
        if include_meta:
            final["meta"] = self.meta
        return final

    def dumps(self, include_meta: bool = True, **kwargs) -> str:
        """
        :param include_meta: Whether to include the ``meta`` object in the
            serialized string.
        :param kwargs: Passed to ``json.dumps``.
        :returns: A JSON string representing the the GenericDict object.
        """
        if "indent" not in kwargs:
            kwargs["indent"] = 4
        return json.dumps(
            self.to_raw_dict(include_meta), cls=self.get_encoder(), **kwargs
        )

    def copy_filtered(
        self,
        config_vars: Sequence[Variable],
        include_flow_variables: bool = True,
    ) -> "Config":
        """
        Creates a new copy of the configuration object, but only with the
        configuration variables defined by the parameter.

        :param config_vars: A list of configuration variables to include in
            the filtered copy.
        :param include_flow_variables: Whether to include the common flow
            variables in the copy or not.

            This parameter is deprecated as of OpenLane 2.0.0b5 and should be
            set to ``False`` by callers.
        :returns: The new copy
        """
        variables: Set[str] = set([variable.name for variable in config_vars])
        if include_flow_variables:
            variables = variables.union(
                set([variable.name for variable in flow_common_variables])
            )

        return Config(
            {variable: self[variable] for variable in variables},
            meta=dataclasses.replace(self.meta),
        )

    def with_increment(
        self,
        config_vars: Sequence[Variable],
        other_inputs: Mapping[str, Any],
        config_quiet: bool = False,
    ) -> "Config":
        """
        Creates a new ``Config`` object by copying all values
        from the original in addition to any new variables (and removing
        any variables not in `config_vars`).

        Furthermore, inputs can be provided incrementally by passing the object
        ``other_inputs``, which will also use these as overrides to the
        values in the base ``Config`` object.

        All values, including those in the base ``Config`` object and in
        ``other_inputs``, will be re-validated.

        :param config_vars: A list of configuration variables to include and
            validate.
        :param other_inputs: A mapping of other inputs.
        :returns: The new ``Config`` object
        """
        incremental_pdk_vars = [variable for variable in config_vars if variable.pdk]

        mutable, _, _ = self.__get_pdk_config(
            self["PDK"],
            self["STD_CELL_LIBRARY"],
            self["PDK_ROOT"],
            incremental_pdk_vars,
        )

        mutable.update(self)
        mutable.update(other_inputs)

        processed, design_warnings, design_errors = Config.__process_variable_list(
            mutable,
            [],
            config_vars,
            removed_variables,
            on_unknown_key=None,
        )

        if len(design_errors) != 0:
            raise InvalidConfig(
                "incremental configuration", design_warnings, design_errors
            )

        if not config_quiet:
            if len(design_warnings) > 0:
                info(
                    "Loading the incremental configuration has generated the following warnings:"
                )
            for warning in design_warnings:
                warn(warning)

        return Config(
            processed,
            meta=self.meta.copy(),
        )

    @classmethod
    def get_meta(
        Self,
        json_config_in: Union[str, os.PathLike],
        flow_override: Optional[str] = None,
    ) -> Optional[Meta]:
        """
        Returns the Meta object of a JSON configuration file

        :param config_in: A configuration file.
        :returns: Either a Meta object, or if the file is not a JSON file, None.
        """
        try:
            obj = json.load(open(json_config_in, encoding="utf8"))
        except (json.JSONDecodeError, IsADirectoryError):
            return None

        meta = Meta()
        if meta_raw := obj.get("meta"):
            meta = Meta(**meta_raw)

        if flow_override is not None:
            meta.flow = flow_override

        return meta

    @classmethod
    def interactive(
        Self,
        DESIGN_NAME: str,
        PDK: str,
        STD_CELL_LIBRARY: Optional[str] = None,
        PDK_ROOT: Optional[str] = None,
        **kwargs,
    ) -> "Config":
        """
        This constructs a partial configuration object that may be incrementally
        adjusted per-step, and activates OpenLane's **interactive mode**.

        The interactive mode is overall less rigid than the pure mode, adding various
        references to global objects to make the REPL or Notebook experience more
        pleasant, however, it is not as resilient as the pure mode and should not
        be used in production code.

        :param DESIGN_NAME: The name of the design to be used.
        :param PDK: The name of the PDK.
        :param STD_CELL_LIBRARY: The name of the standard cell library.

            If not specified, the PDK's default SCL will be used.
        :param PDK_ROOT: Required if Volare is not installed.

            If Volare is installed, this value can be used to optionally override
            Volare's default.

        :param kwargs: Any overrides to PDK values and/or common flow default variables
            can be passed as keyword arguments to this function.

            Useful examples are CLOCK_PORT, CLOCK_PERIOD, et cetera, which while
            not bound to a specific :class:`Step`, affects most Steps' behavior.
        """
        PDK_ROOT = Self.__resolve_pdk_root(PDK_ROOT)

        raw, _, _ = Self.__get_pdk_config(
            PDK,
            STD_CELL_LIBRARY,
            PDK_ROOT,
            pdk_variables + scl_variables,
        )

        kwargs["DESIGN_NAME"] = DESIGN_NAME
        kwargs["DESIGN_DIR"] = kwargs.get("DESIGN_DIR", ".")

        raw.update(kwargs)

        processed, design_warnings, design_errors = Config.__process_variable_list(
            raw,
            [],
            flow_common_variables,
            removed_variables,
            on_unknown_key="error",
        )

        if len(design_errors) != 0:
            raise InvalidConfig("default configuration", design_warnings, design_errors)

        if len(design_warnings) > 0:
            info(
                "Loading the default configuration has generated the following warnings:"
            )
        for warning in design_warnings:
            warn(warning)

        Config.current_interactive = Config(processed)

        return Config.current_interactive

    @classmethod
    def load(
        Self,
        config_in: Union[str, os.PathLike, Mapping[str, Any]],
        flow_config_vars: Sequence[Variable],
        *,
        config_override_strings: Optional[Sequence[str]] = None,
        pdk: Optional[str] = None,
        pdk_root: Optional[str] = None,
        scl: Optional[str] = None,
        design_dir: Optional[str] = None,
        _load_pdk_configs: bool = True,
    ) -> Tuple["Config", str]:
        """
        Creates a new Config object based on a Tcl file, a JSON file, or a
        dictionary.

        The returned config object is locked and cannot be modified.

        :param config_in: Either a file path to a JSON file or a Python
            Mapping object (such as ``dict``) representing an unprocessed
            OpenLane configuration object.

            Tcl files are also supported, but are deprecated and will be removed
            in the future.

        :param config_override_strings: A list of "overrides" in the form of
            NAME=VALUE strings. These are primarily for running OpenLane from
            the command-line and strictly speaking should not be used in the API.

        :param design_dir: The design directory for said configuration.
            Supported and required *if and only if* config_in is a dictionary.

        :param pdk: A process design kit to use. Required unless specified via the
            "PDK" key in a configuration object.

        :param pdk_root: Required if Volare is not installed.

            If Volare is installed, this value can be used to optionally override
            Volare's default.

        :param scl: A standard cell library to use. If not specified, the PDK's
            default standard cell library will be used instead.

        :returns: A tuple containing a Config object and the design directory.
        """
        loader: Callable = Self.__loads
        raw: Union[str, Mapping] = ""
        default_meta_version = 1
        if not isinstance(config_in, Mapping):
            if design_dir is not None:
                raise TypeError(
                    "The argument design_dir is not supported when config_in is not a dictionary."
                )
            config_in = os.path.abspath(config_in)

            design_dir = str(os.path.dirname(config_in))
            config_in = str(config_in)
            if config_in.endswith(".json"):
                raw = open(config_in, encoding="utf8").read()
            elif config_in.endswith(".tcl"):
                raw = open(config_in, encoding="utf8").read()
                loader = Self.__loads_tcl
            else:
                if os.path.isdir(config_in):
                    raise ValueError(
                        "Passing design folders as arguments is unsupported in OpenLane 2 or higher: please pass the JSON configuration file directly."
                    )
                _, ext = os.path.splitext(config_in)
                raise ValueError(
                    f"Unsupported configuration file extension '{ext}' for '{config_in}'."
                )
        else:
            default_meta_version = 2
            if design_dir is None:
                raise TypeError(
                    "The argument design_dir is required when using attempting to load a Config with a dictionary."
                )
            raw = config_in
            loader = Self.__load_dict

        loaded = loader(
            raw,
            design_dir,
            flow_config_vars=flow_config_vars,
            pdk_root=pdk_root,
            pdk=pdk,
            scl=scl,
            config_override_strings=(config_override_strings or []),
            default_meta_version=default_meta_version,
            _load_pdk_configs=_load_pdk_configs,
        )

        return (loaded, design_dir)

    ## For Jupyter
    def _repr_markdown_(self) -> str:  # pragma: no cover
        title = (
            "Interactive Configuration"
            if self == Config.current_interactive
            else "Configuration"
        )
        values_title = (
            "Initial Values" if self == Config.current_interactive else "Values"
        )
        return (
            dedent(
                f"""
                ### {title}
                #### {values_title}

                <br />

                ```yml
                %s
                ```
                """
            )
            % yaml.safe_dump(json.loads(self.dumps()))
        )

    ## Private Methods
    @classmethod
    def __loads(
        Self,
        json_str: str,
        *args,
        **kwargs,
    ):
        raw = json.loads(json_str, parse_float=Decimal)
        return Self.__load_dict(
            raw,
            *args,
            **kwargs,
        )

    @classmethod
    def __load_dict(
        Self,
        mapping_in: Mapping[str, Any],
        design_dir: str,
        flow_config_vars: Sequence[Variable],
        *,
        config_override_strings: Sequence[str],  # Unused, kept for API consistency
        pdk_root: Optional[str] = None,
        pdk: Optional[str] = None,
        scl: Optional[str] = None,
        full_pdk_warnings: bool = False,
        default_meta_version: int = 1,
        _load_pdk_configs: bool = True,
    ) -> "Config":
        raw = dict(mapping_in)

        meta: Optional[Meta] = None
        if raw.get("meta") is not None:
            meta_raw = raw["meta"]
            del raw["meta"]
            try:
                meta = Meta(**meta_raw)
            except TypeError as e:
                raise InvalidConfig(
                    "design configuration file", [], [f"'meta' object is invalid: {e}"]
                )

        flow_option_vars = []
        flow_pdk_vars = []
        for variable in flow_config_vars:
            if variable.pdk:
                flow_pdk_vars.append(variable)
            else:
                flow_option_vars.append(variable)

        if meta is None:
            meta = Meta(version=default_meta_version)

        override_keys = set()
        for string in config_override_strings:
            key, value = string.split("=", 1)
            raw[key] = value
            override_keys.add(key)

        mutable = GenericDict(
            preprocess_dict(
                raw,
                only_extract_process_info=True,
                design_dir=design_dir,
            )
        )

        pdk = mutable.get(SpecialKeys.pdk) or pdk
        scl = mutable.get(SpecialKeys.scl) or scl
        pdkpath = ""

        mutable["PDK_ROOT"] = pdk_root

        if _load_pdk_configs:
            pdk_root = Self.__resolve_pdk_root(pdk_root)
            if pdk is None:
                raise ValueError(
                    "The pdk argument is required as the configuration object lacks a 'PDK' key."
                )

            mutable, pdkpath, scl = Self.__get_pdk_config(
                pdk=pdk,
                scl=scl,
                pdk_root=pdk_root,
                full_pdk_warnings=full_pdk_warnings,
                flow_pdk_vars=flow_pdk_vars,
            )

        readable_paths = [
            os.path.abspath(design_dir),
        ]
        if pdkpath != "":
            readable_paths.append(os.path.abspath(pdkpath))

        mutable.update(
            preprocess_dict(
                raw,
                pdk=pdk,
                pdkpath=pdkpath,
                scl=mutable[SpecialKeys.scl],
                design_dir=design_dir,
                readable_paths=readable_paths,
            )
        )

        permissive_variables = list(flow_config_vars)
        strict_variables = []
        on_unknown_key: Union[Literal["error", "warn"], None] = "warn"
        if meta.version >= 2:
            permissive_variables = []
            for variable in flow_config_vars:
                if variable.name in override_keys:
                    permissive_variables.append(variable)
                    continue
                strict_variables.append(variable)
            on_unknown_key = "error"

        processed, design_warnings, design_errors = Config.__process_variable_list(
            mutable,
            permissive_variables,
            strict_variables,
            removed_variables,
            on_unknown_key=on_unknown_key,
        )

        if len(design_errors) != 0:
            raise InvalidConfig(
                "design configuration file", design_warnings, design_errors
            )

        if len(design_warnings) > 0:
            info(
                "Loading the design configuration file has generated the following warnings:"
            )
        for warning in design_warnings:
            warn(warning)

        return Config(processed, meta=meta)

    @classmethod
    def __loads_tcl(
        Self,
        config: str,
        design_dir: str,
        flow_config_vars: Sequence[Variable],
        *,
        config_override_strings: Sequence[str],
        pdk_root: Optional[str] = None,
        pdk: Optional[str] = None,
        scl: Optional[str] = None,
        full_pdk_warnings: bool = False,
        default_meta_version: int = 1,  # Unused, kept for API consistency
        _load_pdk_configs: bool = True,  # Unused, kept for API consistency
    ) -> "Config":
        warn(
            "Support for .tcl configuration files is deprecated. Please migrate to a .json file at your earliest convenience."
        )

        flow_option_vars = []
        flow_pdk_vars = []
        for variable in flow_config_vars:
            if variable.pdk:
                flow_pdk_vars.append(variable)
            else:
                flow_option_vars.append(variable)

        pdk_root = Self.__resolve_pdk_root(pdk_root)

        tcl_vars_in = GenericDict(
            {
                SpecialKeys.pdk_root: pdk_root,
                SpecialKeys.pdk: pdk,
            }
        )
        tcl_vars_in[SpecialKeys.scl] = ""
        tcl_vars_in[SpecialKeys.design_dir] = design_dir
        tcl_config = GenericDict(TclUtils._eval_env(tcl_vars_in, config))

        process_info = preprocess_dict(
            tcl_config,
            only_extract_process_info=True,
            design_dir=design_dir,
        )

        pdk = process_info.get(SpecialKeys.pdk) or pdk

        if pdk is None:
            raise ValueError(
                "The pdk argument is required as the configuration object lacks a 'PDK' key."
            )

        mutable, _, scl = Self.__get_pdk_config(
            pdk=pdk,
            scl=scl,
            pdk_root=pdk_root,
            full_pdk_warnings=full_pdk_warnings,
            flow_pdk_vars=flow_pdk_vars,
        )

        tcl_vars_in[SpecialKeys.pdk] = pdk
        tcl_vars_in[SpecialKeys.scl] = scl
        tcl_vars_in[SpecialKeys.design_dir] = design_dir

        mutable.update(GenericDict(TclUtils._eval_env(tcl_vars_in, config)))
        for string in config_override_strings:
            key, value = string.split("=", 1)
            mutable[key] = value

        processed, design_warnings, design_errors = Config.__process_variable_list(
            mutable,
            list(flow_config_vars),
            [],
            removed_variables,
            on_unknown_key="warn",
        )

        if len(design_errors) != 0:
            raise InvalidConfig(
                "design configuration file", design_warnings, design_errors
            )

        if len(design_warnings) > 0:
            info(
                "Loading the design configuration file has generated the following warnings:"
            )
        for warning in design_warnings:
            warn(warning)

        return Config(processed)

    @classmethod
    def __resolve_pdk_root(Self, pdk_root: Optional[str]) -> str:
        try:
            import volare

            pdk_root = volare.get_volare_home(pdk_root)
        except ImportError:
            if pdk_root is None:
                raise ValueError(
                    "The pdk_root argument is required as Volare is not installed."
                )
        return os.path.abspath(pdk_root)

    @staticmethod
    @lru_cache(1, True)
    def __get_pdk_raw(
        pdk_root: str, pdk: str, scl: Optional[str]
    ) -> Tuple[immutabledict[str, Any], str, str]:
        pdk_config: GenericDict[str, Any] = GenericDict(
            {
                SpecialKeys.pdk_root: pdk_root,
                SpecialKeys.pdk: pdk,
            }
        )

        if scl is not None:
            pdk_config[SpecialKeys.scl] = scl

        pdkpath = os.path.join(pdk_root, pdk)
        if not os.path.exists(pdkpath):
            matches = glob(f"{pdkpath}*")
            errors = [f"The PDK {pdk} was not found."]
            warnings = []
            for match in matches:
                basename = os.path.basename(match)
                warnings.append(f"A similarly-named PDK was found: {basename}")
            raise InvalidConfig("PDK configuration", warnings, errors)

        pdk_config_path = os.path.join(pdkpath, "libs.tech", "openlane", "config.tcl")

        pdk_env = TclUtils._eval_env(
            pdk_config,
            open(pdk_config_path, encoding="utf8").read(),
        )

        scl = pdk_env["STD_CELL_LIBRARY"]
        assert (
            scl is not None
        ), "Fatal error: STD_CELL_LIBRARY default value not set by PDK."

        scl_config_path = os.path.join(
            pdkpath, "libs.tech", "openlane", scl, "config.tcl"
        )

        scl_env = migrate_old_config(
            TclUtils._eval_env(
                pdk_env,
                open(scl_config_path, encoding="utf8").read(),
            )
        )

        return immutabledict(scl_env), pdkpath, scl

    @staticmethod
    def __get_pdk_config(
        pdk: str,
        scl: Optional[str],
        pdk_root: str,
        flow_pdk_vars: Optional[List[Variable]] = None,
        full_pdk_warnings: Optional[bool] = False,
    ) -> Tuple[GenericDict[str, Any], str, str]:
        """
        :returns: A tuple of the PDK configuration, the PDK path and the SCL.
        """

        frozen, pdkpath, scl = Config.__get_pdk_raw(pdk_root, pdk, scl)
        if flow_pdk_vars is None or len(flow_pdk_vars) == 0:
            return (GenericDict(), pdkpath, scl)

        raw: GenericDict[str, Any] = GenericDict(frozen)  # microwave
        processed, pdk_warnings, pdk_errors = Config.__process_variable_list(
            raw,
            flow_pdk_vars,
            [],
            on_unknown_key=None,
        )

        if len(pdk_errors) != 0:
            raise InvalidConfig("PDK configuration files", pdk_warnings, pdk_errors)

        if len(pdk_warnings) > 0:
            if full_pdk_warnings:
                info(
                    "Loading the PDK configuration files has generated the following warnings:"
                )
                for warning in pdk_warnings:
                    warn(warning)

        processed["PDK_ROOT"] = pdk_root
        processed["PDK"] = pdk

        return (processed, pdkpath, scl)

    def __process_variable_list(
        mutable: GenericDict[str, Any],
        variables: Sequence["Variable"],
        strict_variables: Sequence["Variable"],
        removed: Optional[Mapping[str, str]] = None,
        *,
        on_unknown_key: Union[Literal["error", "warn"], None] = "warn",
    ) -> Tuple[GenericDict[str, Any], List[str], List[str]]:
        """
        Verifies a configuration object against a list of variables, returning
        an object with the variables normalized according to their types.

        :param config: The input, raw configuration object.
        :param variables: A sequence or some other iterable of variables.
        :param removed: A dictionary of variables that may have existed at a point in
            time, but then have gotten removed. Useful to give feedback to the user.
        :returns: A tuple of:
            [0] A final, processed configuration.
            [1] A list of warnings.
            [2] A list of errors.

            If the third element is non-empty, the first object is invalid.
        """
        if removed is None:
            removed = {}
        warnings: List[str] = []
        errors = []
        final: GenericDict[str, Any] = GenericDict()

        # Special Deprecation Behaviors
        if (
            mutable.get("DIODE_INSERTION_STRATEGY") is not None
        ):  # Can't use := because 0 is a valid value
            dis = mutable["DIODE_INSERTION_STRATEGY"]
            del mutable["DIODE_INSERTION_STRATEGY"]
            try:
                dis = int(dis)
            except ValueError:
                pass
            if not isinstance(dis, int) or dis in [1, 2, 5] or dis > 6:
                errors.append(
                    f"DIODE_INSERTION_STRATEGY '{dis}' is not available in OpenLane 2 or higher. See 'Migrating DIODE_INSERTION_STRATEGY' in the docs for more info."
                )
            else:
                warnings.append(
                    "The DIODE_INSERTION_STRATEGY variable has been deprecated. See 'Migrating DIODE_INSERTION_STRATEGY' in the docs for more info."
                )

                mutable["GRT_REPAIR_ANTENNAS"] = False
                mutable["RUN_HEURISTIC_DIODE_INSERTION"] = False
                mutable["DIODE_ON_PORTS"] = "none"
                if dis in [3, 6]:
                    mutable["GRT_REPAIR_ANTENNAS"] = True
                if dis in [4, 6]:
                    mutable["RUN_HEURISTIC_DIODE_INSERTION"] = True
                    mutable["DIODE_ON_PORTS"] = "in"

        # Macros
        if mutable.get("EXTRA_SPEFS") is not None and mutable.get("MACROS") is None:
            mutable["MACROS"] = {}

            extra_spef_list = mutable["EXTRA_SPEFS"]
            del mutable["EXTRA_SPEFS"]
            if isinstance(extra_spef_list, str):
                extra_spef_list = extra_spef_list.split(" ")

            if not isinstance(extra_spef_list, list):
                errors.append(
                    f"Invalid type for 'EXTRA_SPEFS': {type(extra_spef_list)}. It is recommended that you update your configuration to use the Macro object."
                )
            elif len(extra_spef_list) % 4 != 0:
                errors.append(
                    "Invalid value for 'EXTRA_SPEFS': Element count not divisible by four. It is recommended that you update your configuration to use the Macro object."
                )
            else:
                warnings.append(
                    "The configuration variable 'EXTRA_SPEFS' is deprecated. Check the docs on how to use the new 'MACROS' configuration variable."
                )
                for i in range(len(extra_spef_list) // 4):
                    start = i * 4
                    module, min, nom, max = (
                        extra_spef_list[start],
                        extra_spef_list[start + 1],
                        extra_spef_list[start + 2],
                        extra_spef_list[start + 3],
                    )
                    macro_dict: Dict[str, Any] = {
                        "gds": [Path._dummy_path],
                        "lef": [Path._dummy_path],
                    }
                    macro_dict["spef"] = {
                        "min_*": [min],
                        "nom_*": [nom],
                        "max_*": [max],
                    }
                    mutable["MACROS"][module] = macro_dict
        elif (
            mutable.get("EXTRA_SPEFS") is not None and mutable.get("MACROS") is not None
        ):
            errors.append(
                "EXTRA_SPEFS cannot be defined simultaneously with its successor variable, MACROS"
            )

        for variable in variables:
            try:
                key, value_processed = variable.compile(
                    mutable_config=mutable,
                    warning_list_ref=warnings,
                    values_so_far=final,
                    permissive_typing=True,
                )
                if key is not None:
                    del mutable[key]
                final[variable.name] = value_processed
            except ValueError as e:
                errors.append(str(e))
            if variable.name in mutable:
                del mutable[variable.name]

        for variable in strict_variables:
            try:
                key, value_processed = variable.compile(
                    mutable_config=mutable,
                    warning_list_ref=warnings,
                    values_so_far=final,
                    permissive_typing=False,
                )
                if key is not None:
                    del mutable[key]
                final[variable.name] = value_processed
            except ValueError as e:
                errors.append(str(e))
            if variable.name in mutable:
                del mutable[variable.name]

        for key in sorted(mutable.keys()):
            assert isinstance(key, str)

            if key in vars(SpecialKeys).values():
                continue
            if key in removed:
                warnings.append(f"'{key}' has been removed: {removed[key]}")
            elif (
                "_OPT" not in key
                and not key.startswith("//")
                and not key.startswith("#")
            ):
                if on_unknown_key == "error":
                    if key in Variable.known_variable_names:
                        warnings.append(
                            f"Key '{key}' provided is unused by the current flow."
                        )
                    else:
                        errors.append(f"Unknown key '{key}' provided.")
                elif on_unknown_key == "warn":
                    if key in Variable.known_variable_names:
                        warnings.append(
                            f"Key '{key}' provided is unused by the current flow."
                        )
                    else:
                        warnings.append(f"An unknown key '{key}' was provided.")

        return (final, warnings, errors)
