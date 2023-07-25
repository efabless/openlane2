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
import pytest
from decimal import Decimal
from typing import Dict, List, Literal, Optional, Tuple, Union
from pyfakefs.fake_filesystem_unittest import Patcher


from .variable import Variable


@pytest.fixture()
def _mock_fs():
    with Patcher() as patcher:
        patcher.fs.create_dir("/cwd")
        os.chdir("/cwd")
        patcher.fs.create_file("/cwd/a")
        patcher.fs.create_file("/cwd/b")
        yield


def test_macro_validation():
    from . import Macro

    with pytest.raises(ValueError, match="at least one GDSII file"):
        Macro(gds=[], lef=["test"])

    with pytest.raises(ValueError, match="at least one LEF file"):
        Macro(gds=["test"], lef=[])


def test_is_optional():
    from .variable import is_optional

    assert is_optional(int) is False, "is_optional false positive"
    assert is_optional(Optional[int]) is True, "is_optional false negative"
    assert (
        is_optional(Optional[Union[int, dict]]) is True
    ), "is_optional composite false negative"
    assert (
        is_optional(Union[None, int, dict]) is True
    ), "is_optional flattened union false negative"


def test_some_of():
    from .variable import some_of

    assert some_of(int) == int, "some_of changed the type of a non-option type"
    assert (
        some_of(List[str]) == List[str]
    ), "some_of changed the type of a non-option type"
    assert (
        some_of(Optional[int]) == int
    ), "some_of failed to extract type from option type"
    assert (
        some_of(Optional[Union[Dict, List]]) == Union[Dict, List]
    ), "some of failed to properly handle optional union"

    assert (
        some_of(Union[Dict, List, None]) == Union[Dict, List]
    ), "some of failed to properly handle flattened optional union"


def test_variable_general():
    from . import Variable

    variable = Variable(
        "EXAMPLE",
        Optional[int],
        description="My Description",
        deprecated_names=["OLD_EXAMPLE"],
    )

    assert variable.optional, ".optional property incorrectly set"
    assert variable.some == int, ".some property incorrectly set"

    variable_b = Variable(
        "EXAMPLE",
        Optional[int],
        description="My Other Description",
    )

    assert (
        variable == variable_b
    ), "Variable with different description or deprecated_name didn't match"

    variable_union = Variable(
        "UNION_VAR",
        Union[int, str],
        description="x",
    )
    assert variable_union.type == Union[int, str], "Union magically switched types"


@pytest.fixture()
def variable():
    from .variable import Path, Variable

    return Variable(
        "EXAMPLE",
        Optional[List[Path]],
        description="x",
        deprecated_names=["OLD_EXAMPLE"],
    )


@pytest.mark.usefixtures("_mock_fs")
def test_compile(variable: Variable):
    from ..common import GenericDict

    valid_input = GenericDict({"EXAMPLE": ["/cwd/a", "/cwd/b"]})
    warning_list = []
    used_name, paths = variable.compile(
        valid_input,
        warning_list,
        {},
    )
    assert used_name == "EXAMPLE", "valid input returned incorrect used name"
    assert paths == [
        "/cwd/a",
        "/cwd/b",
    ], "valid input resolved paths incorrectly"
    assert len(warning_list) == 0, "valid input generated warning"


@pytest.mark.usefixtures("_mock_fs")
def test_compile_deprecated(variable: Variable):
    from ..common import GenericDict

    deprecated_valid_input = GenericDict(
        {
            "OLD_EXAMPLE": [
                "/cwd/a",
                "/cwd/b",
            ]
        }
    )
    warning_list = []
    used_name, paths = variable.compile(
        deprecated_valid_input,
        warning_list,
        {},
    )
    assert (
        used_name == "OLD_EXAMPLE"
    ), "deprecated valid input returned incorrect used name"
    assert paths == [
        "/cwd/a",
        "/cwd/b",
    ], "deprecated valid input returned paths resolved incorrectly"
    assert len(warning_list) == 1, "use of deprecated names did not produce a warning"


@pytest.fixture()
def variable_set(variable):
    from ..common import StringEnum

    return [
        variable,
        Variable(
            "LIST_VAR",
            List[int],
            description="x",
        ),
        Variable(
            "TUPLE_2_VAR",
            Tuple[int, int],
            description="x",
        ),
        Variable(
            "TUPLE_3_VAR",
            Tuple[int, int, int],
            description="x",
        ),
        Variable(
            "DICT_VAR",
            Dict[str, str],
            description="x",
        ),
        Variable(
            "OTHER_DICT_VAR",
            Dict[str, str],
            description="x",
        ),
        Variable(
            "UNION_VAR",
            Union[int, str],
            description="x",
        ),
        Variable(
            "LITERAL_VAR",
            Literal["yes"],
            description="x",
        ),
        Variable(
            "BOOL_VAR",
            bool,
            description="x",
        ),
        Variable(
            "LITERAL_VAR",
            Literal["yes"],
            description="x",
        ),
        Variable(
            "ENUM_VAR",
            StringEnum("x", ["AValue", "AnotherValue"]),
            description="x",
        ),
        Variable(
            "NUMBER_VAR",
            Decimal,
            description="x",
        ),
    ]


@pytest.mark.usefixtures("_mock_fs")
def test_compile_invalid(variable_set: List[Variable]):
    from ..common import GenericDict

    invalid_input = GenericDict(
        {
            "EXAMPLE": [
                "/cwd/a",
                "/cwd/c",
            ],
            "LIST_VAR": {},
            "TUPLE_2_VAR": [1, {}],
            "TUPLE_3_VAR": [1, 4],
            "DICT_VAR": [],
            "OTHER_DICT_VAR": "invalid tcl dictionary",
            "UNION_VAR": [],
            "LITERAL_VAR": "no",
            "BOOL_VAR": "No",
            "ENUM_VAR": "NotAValue",
            "NUMBER_VAR": "v",
        }
    )
    warning_list = []

    for variable in variable_set:
        print(f"* Testing {variable.name} ({variable.type})…")
        with pytest.raises(ValueError):  # noqa: PT011
            variable.compile(
                invalid_input,
                warning_list,
                {},
            )
