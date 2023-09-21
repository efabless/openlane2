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
import shutil
import inspect
import importlib
from typing import Optional

import pytest


@pytest.mark.parametrize("test", pytest.tests)
@pytest.mark.usefixtures("_chdir_tmp")
def test_step_folder(test: str):
    from openlane.steps import Step
    from openlane.common import Toolbox

    step, _ = test.split(os.path.sep, maxsplit=1)
    test_path = os.path.join(pytest.step_test_dir, test)
    shutil.copytree(test_path, ".", dirs_exist_ok=True)

    state_in = os.path.join(".", "state_in.json")
    config = os.path.join(".", "config.json")
    handler = None
    handler_sig = None
    try:
        spec = importlib.util.spec_from_file_location(
            "handler_module", os.path.join(test_path, "handler.py")
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        handler = module.handle
        handler_sig = inspect.signature(handler)
    except FileNotFoundError:
        pass

    Target = Step.factory.get(step)
    target = Target.load(config, state_in, "/home/donn/.volare")

    exception: Optional[Exception] = None
    try:
        target.start(
            toolbox=Toolbox("."),
            step_dir=".",
        )
    except Exception as e:
        exception = e

    if exception is not None:
        if handler is None:
            raise exception from None
        if len(handler_sig.parameters) != 2:
            raise exception from None

    if handler is not None:
        if len(handler_sig.parameters) == 1:
            handler(target)
        elif len(handler_sig.parameters) == 2:
            handler(target, exception)
        else:
            raise RuntimeError("Handler has less than 1 or more than 2 parameters")
