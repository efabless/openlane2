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

from typing import Tuple
from .step import Step, ViewsUpdate, MetricsUpdate
from ..state import State
from ..config import Config
from ..config.test_config import _mock_fs, mock_variables  # noqa: F401


@pytest.fixture()
def step_run():
    def run(self, state_in: State, **kwargs) -> Tuple[ViewsUpdate, MetricsUpdate]:
        views_update: ViewsUpdate = {}
        metrics: MetricsUpdate = {}
        return views_update, metrics

    return run


def test_step_init_empty():
    with pytest.raises(TypeError, match="Can't instantiate abstract class Step"):
        Step()


def test_step_init_missing_id(step_run):
    class TestStep(Step):
        inputs = []
        outputs = []
        run = step_run

    with pytest.raises(
        NotImplementedError,
        match="All subclasses of Step must override the value of id",
    ):
        TestStep()


def test_step_inputs_not_implemented(step_run):
    with pytest.raises(
        NotImplementedError, match="must implement class attribute 'inputs'"
    ):

        class TestStep(Step):
            run = step_run


def test_step_outputs_not_implemented(step_run):
    with pytest.raises(
        NotImplementedError, match="must implement class attribute 'outputs'"
    ):

        class TestStep(Step):
            inputs = []
            run = step_run


def test_step_missing_config(step_run):
    class TestStep(Step):
        inputs = []
        outputs = []
        run = step_run
        id = "TestStep"

    with pytest.raises(TypeError, match="Missing required argument 'config'"):
        TestStep()


def test_step_missing_state_in(step_run):
    class TestStep(Step):
        inputs = []
        outputs = []
        run = step_run
        id = "TestStep"

    with pytest.raises(TypeError, match="Missing required argument 'state_in'"):

        TestStep(config=Config({"abc": "abc"}))


@pytest.fixture()
@mock_variables()
def mock_config():
    from ..config import config

    mock_config, _ = Config.load(
        {
            "DESIGN_NAME": "whatever",
            "VERILOG_FILES": "dir::src/*.v",
        },
        config.flow_common_variables,
        design_dir="/cwd",
        pdk="dummy",
        scl="dummy_scl",
        pdk_root="/pdk",
    )
    return mock_config


@pytest.mark.usefixtures("_mock_fs")
@mock_variables()
def test_step_create(step_run, mock_config):
    from ..state.design_format import DesignFormat

    class TestStep(Step):
        inputs = []
        outputs = []
        run = step_run
        id = "TestStep"

    step = TestStep(
        id="TestStep",
        long_name="longname",
        config=mock_config,
        state_in=State({DesignFormat.NETLIST: "abc"}),
    )
    assert step.id == "TestStep", "Wrong step id"
    assert step.long_name == "longname", "Wrong step longname"
    assert step.config == mock_config, "Wrong step config"


@pytest.mark.usefixtures("_mock_fs")
@mock_variables()
def test_step_run(step_run, mock_config):
    from ..state.design_format import DesignFormat

    class TestStep(Step):
        inputs = []
        outputs = []
        run = step_run
        id = "TestStep"

    state_in = State({DesignFormat.NETLIST: "abc"})
    step = TestStep(
        id="TestStep",
        long_name="longname",
        config=mock_config,
        state_in=state_in,
    )
    views_update, metrics_update = step.run(state_in)
    assert step.id == "TestStep", "Wrong step id"
    assert (
        step.long_name == "longname"
    ), "Wrong step long_name, declared via constructor"
    assert step.config == mock_config, "Wrong step config"
    assert views_update == {}, "Wrong step run -- tainted views_update"
    assert metrics_update == {}, "Wrong step run -- tainted metrics_update"


@pytest.mark.usefixtures("_mock_fs")
@mock_variables()
def test_step_start_missing_toolbox(step_run, mock_config):
    from ..state.design_format import DesignFormat

    class TestStep(Step):
        inputs = []
        outputs = []
        run = step_run
        id = "TestStep"

    state_in = State({DesignFormat.NETLIST: "abc"})
    step = TestStep(
        id="TestStep",
        long_name="longname",
        config=mock_config,
        state_in=state_in,
    )
    with pytest.raises(TypeError, match="Missing argument 'toolbox' required"):
        step.start()


@pytest.mark.usefixtures("_mock_fs")
@mock_variables()
def test_step_start_missing_step_dir(step_run, mock_config):
    from ..state.design_format import DesignFormat
    from ..utils import Toolbox

    class TestStep(Step):
        inputs = []
        outputs = []
        run = step_run
        id = "TestStep"

    state_in = State({DesignFormat.NETLIST: "abc"})
    step = TestStep(
        id="TestStep",
        long_name="longname",
        config=mock_config,
        state_in=state_in,
    )
    with pytest.raises(TypeError, match="Missing required argument 'step_dir'"):
        step.start(toolbox=Toolbox(tmp_dir="/cwd"))


@pytest.mark.usefixtures("_mock_fs")
@mock_variables()
def test_step_start_invalid_state(step_run, mock_config):
    from ..state.design_format import DesignFormat
    from ..utils import Toolbox
    from .step import StepException

    class TestStep(Step):
        inputs = []
        outputs = []
        run = step_run
        id = "TestStep"

    state_in = State({DesignFormat.NETLIST: "abc"})
    step = TestStep(
        id="TestStep",
        long_name="longname",
        config=mock_config,
        state_in=state_in,
    )
    with pytest.raises(StepException, match="generated invalid state"):
        step.start(toolbox=Toolbox(tmp_dir="/cwd"), step_dir="/cwd")


@pytest.mark.usefixtures("_mock_fs")
@mock_variables()
def test_step_start(mock_config):
    from ..common import Path
    from ..state.design_format import DesignFormat
    from ..utils import Toolbox

    test_file = "test.nl.v"
    with open(test_file, "w") as f:
        f.write("\n")

    test_file_out = "test2.nl.v"
    with open(test_file_out, "w") as f:
        f.write("\n")

    new_metric: MetricsUpdate = {"new_metric": "abc"}
    new_view: ViewsUpdate = {DesignFormat.NETLIST: Path(test_file_out)}

    class TestStep(Step):
        inputs = []
        outputs = []
        id = "TestStep"

        def run(self, state_in: State, **kwargs) -> Tuple[ViewsUpdate, MetricsUpdate]:
            return new_view, new_metric

    metrics_in = {"metric": "123"}
    state_in = State({DesignFormat.NETLIST: Path(test_file)}, metrics=metrics_in)
    step = TestStep(
        id="TestStep",
        long_name="longname",
        config=mock_config,
        state_in=state_in,
    )
    state_out = step.start(toolbox=Toolbox(tmp_dir="/cwd"), step_dir="/cwd")
    assert state_out[DesignFormat.NETLIST] == test_file_out, "Wrong step state_out"
    assert state_out.metrics == {
        **new_metric,
        **metrics_in,
    }, "Wrong step state_out metrics"


@pytest.mark.usefixtures("_mock_fs")
@mock_variables()
def test_step_longname(step_run, mock_config):
    from ..state.design_format import DesignFormat

    class TestStep(Step):
        inputs = []
        outputs = []
        run = step_run
        id = "TestStep"
        long_name = "longname2"

    step = TestStep(
        id="TestStep",
        config=mock_config,
        state_in=State({DesignFormat.NETLIST: "abc"}),
    )
    assert step.long_name == "longname2", "Wrong long_name declared via class"


@pytest.mark.usefixtures("_mock_fs")
@mock_variables()
def test_step_factory(step_run):
    @Step.factory.register()
    class TestStep(Step):
        inputs = []
        outputs = []
        run = step_run
        id = "TestStep"
        long_name = "longname2"

    assert (
        "TestStep" in Step.factory.list()
    ), "Step factory did not register step used for testing: TestStep"
    assert (
        Step.factory.get("TestStep") == TestStep
    ), "Wrong type registered by StepFactor"
