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
import re
import glob

import pytest


def collect_step_tests():
    result = []
    test_rx = re.compile(r"\d+\-[A-Za-z\d_]+")
    for p in sorted(
        glob.glob(
            os.path.join(pytest.step_test_dir, "**"),
            recursive=True,
        )
    ):
        basename = os.path.basename(p)
        if test_rx.match(basename) is None:
            continue
        test_id = os.path.relpath(p, pytest.step_test_dir)
        result.append(test_id)

    return result


def pytest_configure():
    __dir__ = os.path.dirname(os.path.abspath(__file__))

    pytest.step_test_dir = os.path.join(__dir__, "all", "by_id")
    pytest.step_common_dir = os.path.join(__dir__, "all", "common")
    pytest.tests = collect_step_tests()
