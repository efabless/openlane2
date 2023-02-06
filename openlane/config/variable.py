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
from enum import Enum
from typing import get_origin, get_args
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Union, Type, List, Optional, Tuple, Any, Dict, Callable

from .config import Config, Path
from .resolve import process_string

# Scalar = Union[Type[str], Type[Decimal], Type[Path], Type[bool]]
# VType = Union[Scalar, List[Scalar]]


@dataclass
class Variable:
    name: str
    type: Any
    description: str
    default: Any = None
    deprecated_names: List[Union[str, Tuple[str, Callable]]] = field(
        default_factory=list
    )

    doc_example: Optional[str] = None
    doc_units: Optional[str] = None

    def is_optional(self) -> bool:
        type_args = get_args(self.type)
        return get_origin(self.type) is Union and type(None) in type_args

    def some(self) -> Any:
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
        return self.default is None and not self.is_optional()

    def process(
        self,
        value,
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

        if value is None:
            if not self.is_optional():
                if self.default is not None:
                    value = self.default
                else:
                    raise ValueError(f"Required variable {self.name} given null value.")
            else:
                return value

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
                return_value.append(self.process(item, subtype))
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

    @classmethod
    def validate_config(
        Self,
        config: Config,
        ignore_keys: List[str],
        variables: List["Variable"],
        processed_so_far: Optional[Config] = None,
    ) -> Tuple[Config, List[str], List[str]]:
        processed = Config()
        if processed_so_far is not None:
            processed = processed_so_far.copy()
        warnings = []
        errors = []
        mutable = config.copy()
        for variable in variables:
            exists, value = mutable.extract(variable.name)
            i = 0
            while (
                not exists
                and variable.deprecated_names is not None
                and i < len(variable.deprecated_names)
            ):
                deprecated_name = variable.deprecated_names[i]
                deprecated_callable = lambda x: x
                if not isinstance(deprecated_name, str):
                    deprecated_name, deprecated_callable = deprecated_name
                exists, value = mutable.extract(deprecated_name)
                if exists:
                    warnings.append(
                        f"The variable '{deprecated_name}' is deprecated. Please check the docs for the usage on the replacement variable '{variable.name}'."
                    )
                if value is not None:
                    value = deprecated_callable(value)
                i = i + 1
            try:
                value_processed = variable.process(value, values_so_far=processed.data)
            except ValueError as e:
                errors.append(str(e))
            processed[variable.name] = value_processed
        for key in sorted(mutable.keys()):
            if key not in ignore_keys and "_OPT" not in key:
                warnings.append(f"Unknown key {key} provided.")

        return (processed, warnings, errors)
