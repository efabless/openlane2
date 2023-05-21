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
import re
import os
import shlex
import inspect
from enum import Enum
from decimal import Decimal, InvalidOperation
from typing import Iterable, Literal, get_origin, get_args
from dataclasses import _MISSING_TYPE, MISSING, dataclass, field, fields, is_dataclass
from typing import Union, Type, List, Optional, Tuple, Any, Dict, Callable, Sequence

from .config import Config
from .resolve import process_string, Keys as SpecialKeys
from ..state import Path

# Scalar = Union[Type[str], Type[Decimal], Type[Path], Type[bool]]
# VType = Union[Scalar, List[Scalar]]


class zip_first(object):
    """
    Works like ``zip_longest`` but always stops when the first iterant stops.
    """

    def __init__(self, a: Iterable, b: Iterable, fillvalue: Any) -> None:
        self.a = a
        self.b = b
        self.fillvalue = fillvalue

    def __iter__(self):
        self.iter_a = iter(self.a)
        self.iter_b = iter(self.b)
        return self

    def __next__(self):
        a = next(self.iter_a)
        b = self.fillvalue
        try:
            b = next(self.iter_b)
        except StopIteration:
            pass
        return (a, b)


newline_rx = re.compile(r"\n")


def is_optional(t: Type[Any]) -> bool:
    type_args = get_args(t)
    return get_origin(t) is Union and type(None) in type_args


def some_of(t: Type[Any]) -> Type[Any]:
    if not is_optional(t):
        return t

    # t must be a Union with None if we're here

    type_args = get_args(t)
    if len(type_args) == 2:
        # Either (Type | None) or (None | Type)
        if type_args[0] != Type[None]:
            return type_args[0]
        else:
            return type_args[1]
    else:
        return t


def repr_type(t: Type[Any]) -> str:
    optional = is_optional(t)
    some = some_of(t)

    type_string = some.__name__
    if inspect.isclass(some) and issubclass(some, Enum):
        type_string = "｜".join([str(e.name) for e in some])
        type_string = f"`{type_string}`"
    else:
        origin, args = get_origin(some), get_args(some)
        if origin is not None:
            if origin == Union:
                arg_strings = [repr_type(arg) for arg in args]
                type_string = "｜".join(arg_strings)
                type_string = f"({type_string})"
            elif origin == Literal:
                return str(args[0])
            else:
                arg_strings = [repr_type(arg) for arg in args]
                type_string = f"{type_string}[{','.join(arg_strings)}]"

    return type_string + ("?" if optional else "")


@dataclass
class Variable:
    """
    An object representing a configuration variable for a PDK, a Flow or a Step.

    :param name: A string name for the Variable. Because of backwards compatility
        with OpenLane 1, the convention is ``UPPER_SNAKE_CASE``.

    :param type: A Python type object representing the variable.

        Supported scalars:

        - ``int``
        - ``decimal.Decimal``
        - ``bool``
        - ``str``
        - :class:`Path`

        Supported products:

        - ``Union`` (incl. ``Optional``)
        - ``List``
        - ``Tuple``
        - ``Dict``
        - ``Enum``

        Other:

        - ``dataclass`` types composed of the above.

    :param description: A human-readable description of the variable. Used to
        generate help strings and documentation.

    :param default: A default value for the variable.

        Optional variables have an implicit default value of ``None``.

    :param deprecated_names: A list of deprecated names for said variable.

        An element of the list can alternative be a tuple of a name and a Callable
        used to perform a translation for when a renamed variable is also slightly
        modified.

    :param units: Used only in documentation: the unit corresponding to this
        object, i.e., μm, pF, etc. Can be any string, but for consistency, SI units
        must be represented in terms of their official symbols.
    """

    name: str
    type: Any
    description: str
    default: Any = None
    deprecated_names: List[Union[str, Tuple[str, Callable]]] = field(
        default_factory=list
    )

    units: Optional[str] = None

    @property
    def optional(self) -> bool:
        """
        Returns whether a variable's type is an `Option type <https://en.wikipedia.org/wiki/Option_type>`_.
        """
        return is_optional(self.type)

    @property
    def some(self) -> Any:
        """
        Returns the type of a variable presuming it is not None.

        If a variable is not Optional, that is simply the type specified in the
        :ivar:`type` field.
        """
        return some_of(self.type)

    def type_repr_md(self) -> str:
        """
        Prints a pretty Markdown string representation of the Variable's type.
        """
        return repr_type(self.type)

    def desc_repr_md(self) -> str:
        """
        Prints the description, but with newlines escaped for Markdown.
        """
        return newline_rx.sub("<br />", self.description)

    def _process(
        self,
        key_path: str,
        value: Any,
        values_so_far: Dict[str, Any],
        validating_type: Type[Any],
        default: Any = None,
        explicitly_specified: bool = True,
    ):
        if explicitly_specified and value is None:
            # User explicitly specified "null" for this value: only error if
            # value is not optional
            if not is_optional(validating_type):
                raise ValueError(
                    f"Non-optional variable {key_path} received a null value."
                )
            else:
                return None
        elif not explicitly_specified and value is None:
            # User did not specify a value for this variable: couple outcomes
            if default is not None:
                return self._process(
                    key_path=key_path,
                    value=default,
                    validating_type=validating_type,
                    values_so_far=values_so_far,
                )
            elif not is_optional(validating_type):
                raise ValueError(
                    f"Required variable {key_path} did not get a specified value."
                )
            else:
                return None

        assert (
            explicitly_specified and value is not None
        ), "Configurator has built an inconsistent state."

        if is_optional(validating_type):
            validating_type = some_of(validating_type)

        if type(value) == str:
            value = process_string(value, values_so_far)

        type_origin = get_origin(validating_type)
        type_args = get_args(validating_type)
        if type_origin in [list, tuple]:
            return_value = list()
            raw = value
            if isinstance(raw, list):
                pass
            elif isinstance(raw, str):
                if "," in raw:
                    raw = raw.split(",")
                elif ";" in raw:
                    raw = raw.split(";")
                else:
                    raw = raw.split()
            else:
                raise ValueError(
                    f"Invalid List provided for variable {key_path}: {value}"
                )

            if type_origin == tuple:
                if len(raw) != len(type_args):
                    raise ValueError(
                        f"Invalid {validating_type} provided for variable {key_path}: ({len(raw)}/{len(type_args)}) tuple entries provided"
                    )

            for i, (item, value_type) in enumerate(
                zip_first(raw, type_args, fillvalue=type_args[0])
            ):
                return_value.append(
                    self._process(
                        key_path=f"{key_path}[{i}]",
                        value=item,
                        validating_type=value_type,
                        values_so_far=values_so_far,
                    )
                )

            if type_origin == tuple:
                return tuple(raw)

            return return_value
        elif type_origin == dict:
            raw = value
            key_type, value_type = type_args
            if isinstance(raw, dict):
                pass
            elif isinstance(raw, str):
                # Assuming Tcl format:
                components = shlex.split(value)
                if len(components) % 2 != 0:
                    raise ValueError(
                        f"Tcl-style flat dictionary provided for variable {key_path} is invalid: uneven number of components ({len(components)})"
                    )
                raw = {}
                for i in range(0, len(components) // 2):
                    key = components[2 * i]
                    val = components[2 * i + 1]
                    raw[key] = val
            else:
                raise ValueError(
                    f"Value provided for variable {key_path} of type {validating_type} is not a dictionary: '{value}'"
                )

            processed = {}
            for key, val in raw.items():
                key_validated = self._process(
                    key_path=key_path,
                    value=key,
                    validating_type=key_type,
                    values_so_far=values_so_far,
                )
                value_validated = self._process(
                    key_path=f"{key_path}.{key_validated}",
                    value=val,
                    validating_type=value_type,
                    values_so_far=values_so_far,
                )
                processed[key_validated] = value_validated

            return processed
        elif type_origin == Union:
            final_value = None
            errors = []
            for arg in type_args:
                try:
                    final_value = self._process(
                        key_path=key_path,
                        value=value,
                        validating_type=arg,
                        values_so_far=values_so_far,
                    )
                except ValueError as e:
                    errors.append(f"\t{str(e)}")
            if final_value is not None:
                return final_value
            else:
                raise ValueError(
                    "\n".join(
                        [
                            f"Value for {key_path} is invalid for union {repr_type(validating_type)}:"
                        ]
                        + errors
                    )
                )
        elif type_origin == Literal:
            arg = type_args[0]
            if value == arg:
                return value
            else:
                raise ValueError(f"Value for {key_path} is not '{arg}': '{value}'")
        elif is_dataclass(validating_type):
            raw = value
            if not isinstance(raw, dict):
                raise ValueError(
                    f"Value provided for deserializable path {validating_type} at {key_path} is not a dictionary."
                )
            kwargs_dict = {}
            for current_field in fields(validating_type):
                key = current_field.name
                subtype = current_field.type
                explicitly_specified = False
                if key in raw:
                    explicitly_specified = True
                field_value = raw.get(key)
                field_default = None
                if (
                    current_field.default is not None
                    and type(current_field.default) != _MISSING_TYPE
                ):
                    field_default = current_field.default
                if current_field.default_factory != MISSING:
                    field_default = current_field.default_factory()
                value_processed = self._process(
                    key_path=f"{key_path}.{key}",
                    value=field_value,
                    explicitly_specified=explicitly_specified,
                    default=field_default,
                    validating_type=subtype,
                    values_so_far=values_so_far,
                )
                kwargs_dict[key] = value_processed
            return validating_type(**kwargs_dict)
        elif validating_type == Path:
            if not os.path.exists(str(value)):
                raise ValueError(
                    f"Path provided for variable {key_path} does not exist: '{value}'"
                )
            return Path(value)
        elif validating_type == bool:
            if value in ["1", "true", True]:
                return True
            elif value in ["0", "false", False]:
                return False
            else:
                raise ValueError(
                    f"Value provided for variable {key_path} of type {validating_type} is invalid: '{value}'"
                )
        elif issubclass(validating_type, Enum):
            try:
                return validating_type[value]
            except KeyError:
                raise ValueError(
                    f"Variable provided for variable {key_path} of enumerated type {validating_type} is invalid: '{value}'"
                )
        elif issubclass(validating_type, Decimal):
            try:
                return Decimal(value)
            except InvalidOperation:
                raise ValueError(
                    f"Value provided for variable {key_path} of type {validating_type} is invalid: '{value}'"
                )

        else:
            try:
                return validating_type(value)
            except ValueError as e:
                raise ValueError(
                    f"Value provided for variable {key_path} of type {validating_type} is invalid: '{value}' {e}"
                )

    def _compile(
        self,
        mutable_config: Config,
        warning_list_ref: List[str],
        values_so_far: Dict[str, Any],
    ) -> Any:
        exists, value = mutable_config.extract(self.name)

        i = 0
        while (
            not exists
            and self.deprecated_names is not None
            and i < len(self.deprecated_names)
        ):
            deprecated_name = self.deprecated_names[i]
            deprecated_callable = lambda x: x
            if not isinstance(deprecated_name, str):
                deprecated_name, deprecated_callable = deprecated_name
            exists, value = mutable_config.extract(deprecated_name)
            if exists:
                warning_list_ref.append(
                    f"The configuration variable '{deprecated_name}' is deprecated. Please check the docs for the usage on the replacement variable '{self.name}'."
                )
            if value is not None:
                value = deprecated_callable(value)
            i = i + 1

        return self._process(
            key_path=self.name,
            value=value,
            default=self.default,
            validating_type=self.type,
            values_so_far=values_so_far,
            explicitly_specified=exists,
        )

    def __hash__(self) -> int:
        return hash((self.name, self.type, self.default))

    def __eq__(self, rhs: object) -> bool:
        if not isinstance(rhs, Variable):
            raise NotImplementedError()
        return (
            self.name == rhs.name
            and self.type == rhs.type
            and self.default == rhs.default
        )

    @classmethod
    def process_config(
        Self,
        config: Config,
        variables: Sequence["Variable"],
        removed: Optional[Dict[str, str]] = None,
    ) -> Tuple[Config, List[str], List[str]]:
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
        final = Config()._unlock()
        mutable = config.copy()._unlock()

        # Special Deprecation Behaviors
        if (
            mutable.get("DIODE_INSERTION_STRATEGY") is not None
        ):  # Can't use := because 0 is a valid value
            _, dis = mutable.extract("DIODE_INSERTION_STRATEGY")
            try:
                dis = int(dis)
            except ValueError:
                pass
            if not isinstance(dis, int) or dis in [1, 2, 5] or dis > 6:
                errors.append(
                    f"DIODE_INSERTION_STRATEGY '{dis}' is not available in OpenLane 2. See 'Migrating DIODE_INSERTION_STRATEGY' in the docs for more info."
                )
            else:
                warnings.append(
                    "The DIODE_INSERTION_STRATEGY variable has been deprecated. See 'Migrating DIODE_INSERTION_STRATEGY' in the docs for more info."
                )

                final["GRT_REPAIR_ANTENNAS"] = False
                final["RUN_HEURISTIC_DIODE_INSERTION"] = False
                final["DIODE_ON_PORTS"] = "none"
                if dis in [3, 6]:
                    final["GRT_REPAIR_ANTENNAS"] = True
                if dis in [5, 6]:
                    final["RUN_HEURISTIC_DIODE_INSERTION"] = True
                    final["DIODE_ON_PORTS"] = "in"

        # Macros
        translated_macros = False
        if mutable.get("EXTRA_SPEFS") is not None:
            mutable["MACROS"] = mutable.get("MACROS") or {}

            _, extra_spef_list = mutable.extract("EXTRA_SPEFS")
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
                translated_macros = True
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
                    macro_dict = {"module": module, "gds": ["/dev/null"]}
                    macro_dict["spef"] = {
                        "min_*": [min],
                        "nom_*": [nom],
                        "max_*": [max],
                    }
                    mutable["MACROS"][module] = macro_dict

        for variable in variables:
            try:
                value_processed = variable._compile(
                    mutable_config=mutable,
                    warning_list_ref=warnings,
                    values_so_far=final.data,
                )
                final[variable.name] = value_processed
            except ValueError as e:
                errors.append(str(e))

        for key in sorted(mutable.keys()):
            if key in vars(SpecialKeys).values():
                continue
            if key in removed:
                warnings.append(f"'{key}' has been removed: {removed[key]}")
            elif "_OPT" not in key:
                warnings.append(f"Unknown key '{key}' provided.")

        if translated_macros:
            for macro in final["MACROS"].values():
                if macro.gds == "/dev/null":
                    macro.gds = Path("")

        return (final._lock(), warnings, errors)
