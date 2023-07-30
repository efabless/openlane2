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
# import os

import pytest

# from pyfakefs.fake_filesystem_unittest import Patcher


# @pytest.fixture(autouse=True)
# def _mock_fs():
#     with Patcher() as patcher:
#         patcher.fs.create_dir("/cwd")
#         os.chdir("/cwd")
#         yield


@pytest.mark.parametrize(
    ("corner", "expected"),
    [
        (None, ["file1.spef", "typical.whatever"]),
        ("nom_ss_n40C_1V8", ["file1.spef", "ss.a", "🥶"]),
        ("min_ff_025C_5V0", []),
    ],
)
def test_toolbox(corner, expected):
    from . import Toolbox
    from ..common import Path
    from ..config import Config

    toolbox = Toolbox(".")

    config = Config({"DEFAULT_CORNER": "nom_tt_025C_1v80"})

    views_by_corner = {
        k: Path(v)
        for k, v in {
            "nom_*": "file1.spef",
            "*_tt_*": "typical.whatever",
            "*_ss_*": "ss.a",
            "nom_": "no globs?",
            "*_100C_*": "🔥",
            "*_n40C_*": "🥶",
        }.items()
    }

    assert toolbox.filter_views(config, views_by_corner, corner) == expected, []


def test_get_macro_views():
    pass
