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


@pytest.fixture()
def test_step_run():
    def run(self, state_in: State, **kwargs) -> Tuple[ViewsUpdate, MetricsUpdate]:
        views: ViewsUpdate = {}
        metrics: MetricsUpdate = {}
        return views, metrics

    return run


def test_step_init_empty(test_step_run):
    with pytest.raises(TypeError, match="Can't instantiate abstract class Step"):
        Step()


def test_step_init_missing_id(test_step_run):
    class TestStep(Step):
        inputs = []
        outputs = []
        run = test_step_run

    with pytest.raises(
        NotImplementedError,
        match="All subclasses of Step must override the value of id",
    ):
        TestStep()


def test_step_init_missing_config(test_step_run):
    class TestStep(Step):
        inputs = []
        outputs = []
        run = test_step_run
        id = "id"

    with pytest.raises(TypeError, match="Missing required argument 'config'"):
        TestStep()


def test_step_inputs_not_implemented(test_step_run):
    with pytest.raises(
        NotImplementedError, match="must implement class attribute 'inputs'"
    ):

        class TestStep(Step):
            run = test_step_run


def test_step_outputs_not_implemented(test_step_run):
    with pytest.raises(
        NotImplementedError, match="must implement class attribute 'outputs'"
    ):

        class TestStep(Step):
            inputs = []
            run = test_step_run
