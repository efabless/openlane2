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
from typing import Callable, Optional, Type
from unittest import mock

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem

from ..config import Variable
from ..config.test_config import (  # noqa: F401
    MOCK_FLOW_VARS,
    mock_variables,
    _mock_fs,
)
from . import flow


@pytest.fixture()
def variable():
    return Variable("DUMMY_VARIABLE", type=str, description="x")


@pytest.fixture()
def MockStepTuple(variable: Variable):
    from ..common import Path
    from ..steps import Step
    from ..state import DesignFormat, State

    class StepA(Step):
        id = "Test.StepA"
        inputs = [DesignFormat.JSON_HEADER]
        outputs = [DesignFormat.JSON_HEADER]

        config_vars = [variable]

        def run(self, state_in: State, **kwargs):
            import json

            out_file = os.path.join(self.step_dir, "whatever.json")
            json.dump(
                {
                    "not_really_a_valid_header": True,
                    "cfg_var_value": self.config["DUMMY_VARIABLE"],
                },
                open(out_file, "w", encoding="utf8"),
            )
            return {
                DesignFormat.JSON_HEADER: Path(out_file),
            }, {"whatever": 0}

    class StepB(Step):
        id = "Test.StepB"
        inputs = []
        outputs = [DesignFormat.JSON_HEADER]

        def run(self, state_in: State, **kwargs):
            import json

            out_file = os.path.join(self.step_dir, "whatever.json")
            json.dump(
                {
                    "probably_a_valid_header": False,
                    "previous_invalid_header": state_in[DesignFormat.JSON_HEADER],
                },
                open(out_file, "w", encoding="utf8"),
            )
            return {
                DesignFormat.JSON_HEADER: Path(out_file),
            }, {"whatever": 0}

    class StepC(Step):
        id = "Test.StepC"
        inputs = [DesignFormat.JSON_HEADER]
        outputs = [DesignFormat.JSON_HEADER]

        config_vars = [Variable("DUMMY_VARIABLE", type=int, description="x")]

        def run(self, state_in: State, **kwargs):
            import json

            out_file = os.path.join(self.step_dir, "whatever.json")
            json.dump(
                {
                    "not_really_a_valid_header": True,
                    "cfg_var_value": self.config["DUMMY_VARIABLE"],
                },
                open(out_file, "w", encoding="utf8"),
            )
            return {
                DesignFormat.JSON_HEADER: Path(out_file),
            }, {"whatever": 0}

    return (StepA, StepB, StepC)


@pytest.fixture()
def DummyFlow(MockStepTuple):
    from .flow import Flow

    StepA, StepB, StepC = MockStepTuple

    class Dummy(Flow):
        Steps = [
            StepA,
            StepB,
        ]

        def __init__(
            self,
            *args,
            run_override: Optional[Callable] = None,
            **kwargs,
        ):
            self.run_override = run_override
            super().__init__(*args, **kwargs)

        def run(self, initial_state, **kwargs):
            if self.run_override is not None:
                return self.run_override(self, initial_state, **kwargs)
            return initial_state.copy(), []

    return Dummy


class MockProgress(object):
    def __init__(self, *args, **kwargs):
        self.add_task_called_count = 0
        self.start_called_count = 0
        self.stop_called_count = 0
        self.update_called_count = 0
        self.total = 100
        self.completed = 0
        self.description = "Progress"

    def add_task(self, *args):
        self.add_task_called_count += 1

    def start(self):
        self.start_called_count += 1

    def stop(self):
        self.stop_called_count += 1

    def update(
        self,
        _,
        description: Optional[str] = None,
        total: Optional[int] = None,
        completed: Optional[float] = None,
    ):
        if total_stages := total:
            self.total = total_stages

        if completed_stages := completed:
            self.completed = completed_stages

        if current_task_description := description:
            self.description = current_task_description

        self.update_called_count += 1


# ---


def test_flow_abc_init():
    from . import Flow

    with pytest.raises(TypeError, match="Can't instantiate abstract class") as e:
        Flow()

    assert e is not None, "Flow ABC instantiated successfully"


def test_factory(DummyFlow: Type[flow.Flow]):
    from . import Flow

    assert Flow.factory.list() == [
        "Optimizing",
        "Classic",
        "OpenInKLayout",
        "OpenInOpenROAD",
    ], "One or more built-in flows missing from factory list"

    Flow.factory.register()(DummyFlow)

    assert "Dummy" in Flow.factory.list(), "failed to register new dummy flow"

    Flow.factory.register("AnotherName")(DummyFlow)

    assert (
        "AnotherName" in Flow.factory.list()
    ), "failed to register new dummy flow by another name"

    assert (
        Flow.factory.get("Dummy") == DummyFlow
    ), "failed to retrieve registered dummy flow"


@pytest.mark.usefixtures("_mock_fs")
@mock_variables([flow])
def test_init_and_config_vars(DummyFlow: Type[flow.Flow], variable: Variable):
    flow = DummyFlow(
        {
            "DESIGN_NAME": "WHATEVER",
            "DUMMY_VARIABLE": "PINGAS",
            "VERILOG_FILES": ["/cwd/src/a.v"],
        },
        design_dir="/cwd",
        pdk="dummy",
        scl="dummy_scl",
        pdk_root="/pdk",
    )

    assert flow.get_config_variables() == MOCK_FLOW_VARS + [
        variable
    ], "flow config variables did not match"


@pytest.mark.usefixtures("_mock_fs")
@mock_variables([flow])
def test_clashing_variables(DummyFlow: Type[flow.Flow], MockStepTuple):
    from . import FlowException

    StepA, StepB, StepC = MockStepTuple

    class DummierFlow(DummyFlow):
        Steps = [StepA, StepB, StepC]

    with pytest.raises(
        FlowException,
        match=r"Unrelated variables in \w+ and \w+ share a name",
    ) as e:
        DummierFlow(
            {
                "DESIGN_NAME": "WHATEVER",
                "DUMMY_VARIABLE": "PINGAS",
                "VERILOG_FILES": ["/cwd/src/a.v"],
            },
            design_dir="/cwd",
            pdk="dummy",
            scl="dummy_scl",
            pdk_root="/pdk",
        )

    assert e is not None, "clashing variables did not generate a FlowException"


@pytest.mark.usefixtures("_mock_fs")
@mock_variables([flow])
@mock.patch.object(flow, "Progress", MockProgress)
def test_progress_bar(DummyFlow: Type[flow.Flow]):
    def run_override(self: DummyFlow, initial_state, **kwargs):
        assert (
            self.progress_bar.started
        ), ".start() did not start the progress bar rendering"

        assert (
            self.progress_bar._FlowProgressBar__progress.start_called_count == 1
        ), "start called more than once"

        self.progress_bar.set_max_stage_count(2)
        assert (
            self.progress_bar._FlowProgressBar__progress.total == 2
        ), ".set_max_stage_count() failed to set progress bar total"

        self.progress_bar.start_stage("literally whatever")

        self.progress_bar.end_stage()

        assert (
            self.progress_bar._FlowProgressBar__progress.update_called_count == 3
        ), "unexpected progress bar update count"

        assert (
            self.progress_bar._FlowProgressBar__progress.completed == 1
        ), "task complete count out of sync"

        self.progress_bar.get_ordinal_prefix() == "2-", "incorrect ordinal returned"

        return initial_state.copy(), []

    flow = DummyFlow(
        {
            "DESIGN_NAME": "WHATEVER",
            "DUMMY_VARIABLE": "PINGAS",
            "VERILOG_FILES": ["/cwd/src/a.v"],
        },
        design_dir="/cwd",
        pdk="dummy",
        scl="dummy_scl",
        pdk_root="/pdk",
        run_override=run_override,
    )

    flow.start()


@pytest.mark.usefixtures("_mock_fs")
@mock_variables([flow])
@mock.patch.object(flow, "Progress", MockProgress)
def test_last_run(
    fs: FakeFilesystem, DummyFlow: Type[flow.Flow], caplog: pytest.LogCaptureFixture
):
    fs.create_dir("/cwd/runs/MY_TAG")
    flow = DummyFlow(
        {
            "DESIGN_NAME": "WHATEVER",
            "DUMMY_VARIABLE": "PINGAS",
            "VERILOG_FILES": ["/cwd/src/a.v"],
        },
        design_dir="/cwd",
        pdk="dummy",
        scl="dummy_scl",
        pdk_root="/pdk",
    )

    flow.start(tag="MY_TAG")
    assert (
        "Starting a new run of the" in caplog.text
    ), ".start() with an empty folder did not print a message about a new run"
