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
import inspect
from enum import Enum
from typing import get_origin, get_args
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Union, Type, List, Optional, Tuple, Any, Dict, Callable, Sequence

from .config import Config, Path
from .resolve import process_string, Keys as SpecialKeys

# Scalar = Union[Type[str], Type[Decimal], Type[Path], Type[bool]]
# VType = Union[Scalar, List[Scalar]]


def StringEnum(name: str, values: Sequence[str]):
    """
    Creates a string enumeration where the keys and values are the same.
    """
    return Enum(name, [(value, value) for value in values])


newline_rx = re.compile(r"\n")


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
        - Enums

        Supported "generics":

        - ``Union`` (incl. ``Optional``)
        - ``List``
        - ``Tuple``

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

    def is_optional(self) -> bool:
        """
        Returns whether a variable's type is an `Option type <https://en.wikipedia.org/wiki/Option_type>`_.
        """
        type_args = get_args(self.type)
        return get_origin(self.type) is Union and type(None) in type_args

    def some(self) -> Any:
        """
        Returns the type of a variable presuming it is not None.

        If a variable is not Optional, that is simply the type specified in the
        :attr:`type` field.
        """
        if not self.is_optional():
            return self.type
        else:
            type_args = get_args(self.type)
            if len(type_args) == 2:
                if type_args[0] != Type[None]:
                    return type_args[0]
                else:
                    return type_args[1]
            else:
                some_type_args = list(type_args)
                some_type_args.remove(Type[None])
                return tuple(some_type_args)

    @property
    def required(self) -> bool:
        """
        Whether this variable is required to be specified by a user configuration
        or not.

        What it boils down to is: Variables without defaults that are not optional
        are required.
        """
        return self.default is None and not self.is_optional()

    def type_repr_md(self) -> str:
        """
        Prints a pretty Markdown string representation of the Variable's type.
        """
        some = self.some()
        optional = self.is_optional()

        type_string = some.__name__
        if inspect.isclass(some) and issubclass(some, Enum):
            type_string = "	\\| ".join([repr(e.value) for e in some])
            type_string = f"`{type_string}`"

        origin, args = get_origin(some), get_args(some)
        if origin is not None:
            arg_strings = [arg.__name__ for arg in args]
            if origin == Union:
                type_string = "	\\| ".join(arg_strings)
                type_string = f"({type_string})"
            else:
                type_string = f"{type_string}[{','.join(arg_strings)}]"

        return type_string + ("?" if optional else "")

    def desc_repr_md(self) -> str:
        """
        Prints the description, but with newlines escaped for Markdown.
        """
        return newline_rx.sub("<br />", self.description)

    def _process(
        self,
        exists: bool,
        value: Any,
        validating_type: Optional[Type] = None,
        values_so_far: Optional[Dict[str, Any]] = None,
    ):
        if values_so_far is None:
            values_so_far = {}

        if validating_type is None:
            validating_type = self.type
            if self.is_optional():
                validating_type = self.some()

        assert validating_type is not None

        if not exists:
            if self.default is not None:
                return self._process(True, self.default, validating_type, values_so_far)
            elif self.is_optional():
                return None
            else:
                raise ValueError(
                    f"Required variable {self.name} did not get a specified value."
                )
        elif value is None:
            if self.is_optional():
                return value
            else:
                raise ValueError(
                    f"Required variable {self.name} received a null value."
                )

        if type(value) == str:
            value = process_string(value, values_so_far)

        if get_origin(validating_type) == list:
            return_value = list()
            subtype = get_args(validating_type)[0]
            if isinstance(value, list):
                pass
            elif isinstance(value, str):
                if "," in value:
                    value = value.split(",")
                elif ";" in value:
                    value = value.split(";")
                else:
                    value = value.split()
            else:
                raise ValueError(
                    f"Invalid List provided for variable {self.name}: {value}"
                )
            for item in value:
                return_value.append(self._process(True, item, subtype))
            return return_value
        elif validating_type == Path:
            if not os.path.exists(value):
                raise ValueError(
                    f"Path provided for variable {self.name} does not exist: '{value}'"
                )
            return Path(value)
        elif validating_type == bool:
            if value in ["1", "true", True]:
                return True
            elif value in ["0", "false", False]:
                return False
            else:
                raise ValueError(
                    f"Value provided for variable {self.name} of type {validating_type} is invalid: '{value}'"
                )
        elif issubclass(validating_type, Enum):
            try:
                return validating_type[value]
            except KeyError:
                raise ValueError(
                    f"Variable provided for variable {self.name} of enumerated type {validating_type} is invalid: 'value'"
                )
        elif issubclass(validating_type, Decimal):
            try:
                return Decimal(value)
            except InvalidOperation:
                raise ValueError(
                    f"Value provided for variable {self.name} of type {validating_type} is invalid: '{value}'"
                )
        else:
            try:
                return validating_type(value)
            except ValueError as e:
                raise ValueError(
                    f"Value provided for variable {self.name} of type {validating_type} is invalid: '{value}' {e}"
                )

    def _compile(
        self,
        mutable_config: Config,
        warning_list_ref: List[str],
        values_so_far: Config,
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

        return self._process(exists, value, values_so_far=values_so_far.data)

    def __hash__(self) -> int:
        return hash((self.name, self.description))

    def __eq__(self, rhs: object) -> bool:
        if not isinstance(rhs, Variable):
            raise NotImplementedError()
        return (
            self.name == rhs.name
            and self.description == rhs.description
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
        final = Config()
        mutable = config.copy()

        if dis := mutable.get("DIODE_INSERTION_STRATEGY"):
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

                config["GRT_REPAIR_ANTENNAS"] = False
                config["RUN_HEURISTIC_DIODE_INSERTION"] = False
                if dis in [3, 6]:
                    config["GRT_REPAIR_ANTENNAS"] = True
                if dis in [5, 6]:
                    config["RUN_HEURISTIC_DIODE_INSERTION"] = True

            del mutable["DIODE_INSERTION_STRATEGY"]

        for variable in variables:
            try:
                value_processed = variable._compile(
                    mutable_config=mutable,
                    warning_list_ref=warnings,
                    values_so_far=final,
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
                warnings.append(f"Unknown key {key} provided.")

        return (final, warnings, errors)
