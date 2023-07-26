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
from typing import Callable, List
from shutil import rmtree
from unittest import mock

import pytest
from pyfakefs.fake_filesystem_unittest import Patcher


from . import config


@pytest.fixture()
def _mock_fs():
    with Patcher() as patcher:
        rmtree("/run", ignore_errors=True)
        patcher.fs.add_real_directory(os.getenv("TMPDIR"))
        patcher.fs.create_dir("/cwd/src")
        patcher.fs.create_file("/cwd/src/a.v")
        patcher.fs.create_file("/cwd/src/b.v")
        patcher.fs.create_file(
            "/pdk/dummy/libs.tech/openlane/config.tcl",
            contents="""
            if { ![info exists ::env(STD_CELL_LIBRARY)] } {
                set ::env(STD_CELL_LIBRARY) "dummy_scl"
            }
            """,
        )

        patcher.fs.create_file(
            "/pdk/dummy/libs.tech/openlane/dummy_scl/config.tcl",
            contents="",
        )

        os.chdir("/cwd")
        yield


def mock_variables(f: Callable):
    from ..common import Path
    from . import Variable

    f = mock.patch.object(
        config,
        "pdk_variables",
        [
            config.Variable(
                "STD_CELL_LIBRARY",
                str,
                description="x",
            )
        ],
    )(f)
    f = mock.patch.object(
        config,
        "flow_common_variables",
        [
            Variable(
                "DESIGN_NAME",
                str,
                description="x",
            ),
            Variable(
                "VERILOG_FILES",
                List[Path],
                description="x",
            ),
        ],
    )(f)
    return f


@pytest.mark.usefixtures("_mock_fs")
@mock_variables
def test_dict_config():
    from . import Meta, Config

    cfg, _ = Config.load(
        {"DESIGN_NAME": "whatever", "VERILOG_FILES": "dir::src/*.v"},
        config.flow_common_variables,
        design_dir="/cwd",
        pdk="dummy",
        scl="dummy_scl",
        pdk_root="/pdk",
    )

    assert cfg == Config(
        {
            "DESIGN_NAME": "whatever",
            "STD_CELL_LIBRARY": "dummy_scl",
            "VERILOG_FILES": ["/cwd/src/a.v", "/cwd/src/b.v"],
        },
        meta=Meta(version=1, flow="Classic"),
    ), "Generated configuration does not match expected value"


@pytest.mark.usefixtures("_mock_fs")
@mock_variables
def test_json_config():
    from . import Meta, Config

    with open("/cwd/config.json", "w") as f:
        f.write(
            """
            {
                "DESIGN_NAME": "whatever",
                "VERILOG_FILES": "dir::src/*.v"
            }
            """
        )

    cfg, _ = Config.load(
        "/cwd/config.json",
        config.flow_common_variables,
        pdk="dummy",
        scl="dummy_scl",
        pdk_root="/pdk",
    )

    assert cfg == Config(
        {
            "DESIGN_NAME": "whatever",
            "STD_CELL_LIBRARY": "dummy_scl",
            "VERILOG_FILES": ["/cwd/src/a.v", "/cwd/src/b.v"],
        },
        meta=Meta(version=1, flow="Classic"),
    ), "Generated configuration does not match expected value"


@pytest.mark.usefixtures("_mock_fs")
@mock_variables
def test_tcl_config():
    from . import Meta, Config

    with open("/cwd/config.tcl", "w") as f:
        f.write(
            """
            set ::env(DESIGN_NAME) "whatever"
            set ::env(VERILOG_FILES) "\\
                /cwd/src/a.v\\
                    /cwd/src/b.v\\
            "
            # cant test glob because of the mock filesystem
            """
        )

    cfg, _ = Config.load(
        "/cwd/config.tcl",
        config.flow_common_variables,
        pdk="dummy",
        scl="dummy_scl",
        pdk_root="/pdk",
    )

    assert cfg == Config(
        {
            "DESIGN_NAME": "whatever",
            "STD_CELL_LIBRARY": "dummy_scl",
            "VERILOG_FILES": ["/cwd/src/a.v", "/cwd/src/b.v"],
        },
        meta=Meta(version=1, flow="Classic"),
    ), "Generated configuration does not match expected value"
