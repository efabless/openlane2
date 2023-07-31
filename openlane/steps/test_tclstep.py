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

import pytest

from .tclstep import TclStep
from ..state import State
from ..config.test_config import _mock_fs, mock_variables  # noqa: F401
from .test_step import mock_config  # noqa: F401


def test_tclstep_missing_get_script_path():
    class TclStepTest(TclStep):
        pass

    error = "Can't instantiate abstract class TclStepTest with abstract method get_script_path"
    with pytest.raises(TypeError, match=error):
        TclStepTest()


@pytest.mark.usefixtures("_mock_fs")
@mock_variables()
def test_tclstep_init(mock_config):
    from ..state.design_format import DesignFormat

    class TclStepTest(TclStep):
        inputs = []
        outputs = []
        id = "TclStepTest"

        def get_script_path(self):
            return "/dummy_path"

    TclStepTest(config=mock_config, state_in=State({DesignFormat.NETLIST: "abc"}))


@pytest.mark.usefixtures("_mock_fs")
@mock_variables()
def test_tclstep_get_command(mock_config):
    from ..state.design_format import DesignFormat

    class TclStepTest(TclStep):
        inputs = []
        outputs = []
        id = "TclStepTest"

        def get_script_path(self):
            return "/dummy_path"

    assert TclStepTest(
        config=mock_config, state_in=State({DesignFormat.NETLIST: "abc"})
    ).get_command() == ["tclsh", "/dummy_path"], "Wrong TclStep command"


def test_tcl_step_value_to_tcl():
    from enum import Enum

    numerical_list_value = [1.0, 2.1000, 3, 4.01]
    numerical_list_value_string = "1.0 2.1 3 4.01"
    assert (
        TclStep.value_to_tcl(numerical_list_value) == numerical_list_value_string
    ), "Wrong numerical list to tcl list conversion"

    alphanumerical_list_value = [
        1.0,
        2.1000,
        3,
        "abc",
        "abc f",
        "{abc}",
        "[abc]",
        "\\abc",
    ]
    alphanumerical_list_value_string = (
        '1.0 2.1 3 abc "abc f" "{abc}" "\\[abc]" "\\\\abc"'
    )
    assert (
        TclStep.value_to_tcl(alphanumerical_list_value)
        == alphanumerical_list_value_string
    ), "Wrong alpahnumerical list to tcl list conversion"

    assert TclStep.value_to_tcl(True) == "1", "Wrong bool to tcl conversion"
    assert TclStep.value_to_tcl(1) == "1", "Wrong integer to tcl conversion"
    assert TclStep.value_to_tcl(-1) == "-1", "Wrong negative integer to tcl conversion"
    assert TclStep.value_to_tcl(-1.01) == "-1.01", "Wrong decimal to tcl conversion"
    assert TclStep.value_to_tcl("Hello") == "Hello", "Wrong string to tcl conversion"

    assert TclStep.value_to_tcl({}) == ""
    assert TclStep.value_to_tcl([]) == ""
    assert TclStep.value_to_tcl("") == ""
    assert TclStep.value_to_tcl(" ") == " "  # or should it be empty?

    class Color(Enum):
        RED = 1

    assert TclStep.value_to_tcl(Color.RED) == "RED"

    dict_value = {"abc": 1}
    dict_value_string = "abc 1"
    assert (
        TclStep.value_to_tcl(dict_value) == dict_value_string
    ), "Wrong dict to tcl conversion"
    dict_value = {
        "abc": 1,
        "cde": "123",
        "f": "[hello]",
        "h": [1, 2, 3],
        "[g]": alphanumerical_list_value,
    }
    dict_value_string = (
        'abc 1 cde 123 f "\\[hello]" h "1 2 3" "\\[g]" '
        + alphanumerical_list_value_string
    )
    assert (
        TclStep.value_to_tcl(dict_value) == dict_value_string
    ), "Wrong complex dict to tcl conversion"
