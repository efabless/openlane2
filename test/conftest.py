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
import tempfile
from shutil import rmtree
from unittest import mock
from decimal import Decimal
from typing import Any, Optional, Iterable, Callable, List, Dict

import pytest
from pyfakefs.fake_filesystem_unittest import Patcher

from openlane.config import Variable, Macro
from openlane.common import StringEnum, Path


@pytest.fixture()
def _mock_conf_fs():
    with Patcher() as patcher:
        rmtree("/run", ignore_errors=True)
        patcher.fs.create_dir("/cwd/src")
        patcher.fs.create_file("/cwd/src/a.v")
        patcher.fs.create_file("/cwd/src/b.v")
        patcher.fs.create_dir("/cwd/spef")
        patcher.fs.create_file("/cwd/spef/b.spef")
        patcher.fs.create_file(
            "/pdk/dummy/libs.tech/openlane/config.tcl",
            contents="""
            if { ![info exists ::env(STD_CELL_LIBRARY)] } {
                set ::env(STD_CELL_LIBRARY) "dummy_scl"
            }
            set ::env(TECH_LEF) "/pdk/dummy/libs.ref/techlef/dummy_scl/dummy_tech_lef.tlef"
            set ::env(LIB_SYNTH) "sky130_fd_sc_hd__tt_025C_1v80.lib"
            """,
        )
        patcher.fs.create_file(
            "/pdk/dummy2/libs.tech/openlane/config.tcl",
            contents="""
            if { ![info exists ::env(STD_CELL_LIBRARY)] } {
                set ::env(STD_CELL_LIBRARY) "dummy2_scl"
            }
            set ::env(TECH_LEF) "/pdk/dummy2/libs.ref/techlef/dummy_scl/dummy_tech_lef.tlef"
            set ::env(LIB_SYNTH) "sky130_fd_sc_hd__tt_025C_1v80.lib"
            """,
        )
        patcher.fs.create_file(
            "/pdk/dummy/libs.ref/techlef/dummy_scl/dummy_tech_lef.tlef",
        )
        patcher.fs.create_file(
            "/pdk/dummy2/libs.ref/techlef/dummy_scl/dummy_tech_lef.tlef",
        )
        patcher.fs.create_file(
            "/pdk/dummy/libs.tech/openlane/dummy_scl/config.tcl",
            contents="",
        )
        patcher.fs.create_file(
            "/pdk/dummy2/libs.tech/openlane/dummy2_scl/config.tcl",
            contents="",
        )

        os.chdir("/cwd")
        yield


class chdir(object):
    def __init__(self, path):
        self.path = path
        self.previous = None

    def __enter__(self):
        self.previous = os.getcwd()
        os.chdir(self.path)

    def __exit__(self, exc_type, exc_value, traceback):
        os.chdir(self.previous)
        if exc_type is not None:
            raise exc_value


class chdir_tmp(chdir):
    def __init__(self):
        self.__temp_dir = None
        super().__init__(None)

    def __enter__(self):
        self.__temp_dir = tempfile.TemporaryDirectory()
        self.path = self.__temp_dir.name
        super().__enter__()
        return self.path

    @property
    def temp_dir(self):
        return self.path

    def __exit__(self, exc_type, exc_value, traceback):
        super().__exit__(exc_type, exc_value, traceback)
        self.__temp_dir.cleanup()
        self.__temp_dir = None
        self.path = None


@pytest.fixture()
def _chdir_tmp():
    import tempfile

    with tempfile.TemporaryDirectory() as dir, chdir(dir):
        yield


DiodeOnPortsEnum = StringEnum("Ports", ["none", "in"])
MOCK_PDK_VARS = [
    Variable(
        "PDK",
        str,
        description="x",
    ),
    Variable(
        "STD_CELL_LIBRARY",
        str,
        description="x",
    ),
    Variable(
        "EXAMPLE_PDK_VAR",
        Decimal,
        description="x",
        default=10.0,
    ),
    Variable(
        "TECH_LEFS",
        Dict[str, Path],
        description="x",
    ),
    Variable(
        "DEFAULT_CORNER",
        str,
        description="x",
        default="nom_tt_025C_1v80",
    ),
]
MOCK_FLOW_VARS = [
    Variable(
        "DESIGN_DIR",
        Path,
        "The directory of the design. Does not need to be provided explicitly.",
    ),
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
    Variable(
        "GRT_REPAIR_ANTENNAS",
        bool,
        description="x",
        default=True,
    ),
    Variable(
        "RUN_HEURISTIC_DIODE_INSERTION",
        bool,
        description="x",
        default=False,
    ),
    Variable(
        "DIODE_ON_PORTS",
        DiodeOnPortsEnum,
        description="x",
        default="none",
    ),
    Variable(
        "MACROS",
        Optional[Dict[str, Macro]],
        description="x",
        default=None,
    ),
]


def mock_variables(patch_in_objects: Optional[Iterable[Any]] = None):
    from openlane.config import config

    if patch_in_objects is None:
        patch_in_objects = []
    patch_in_objects = patch_in_objects + [config]

    def decorator(f: Callable):
        for o in patch_in_objects:
            if hasattr(o, "pdk_variables"):
                f = mock.patch.object(
                    o,
                    "pdk_variables",
                    MOCK_PDK_VARS,
                )(f)
            if hasattr(o, "flow_common_variables"):
                f = mock.patch.object(
                    o,
                    "flow_common_variables",
                    MOCK_FLOW_VARS,
                )(f)
            if hasattr(o, "removed_variables"):
                f = mock.patch.object(
                    o,
                    "removed_variables",
                    {"REMOVED_VARIABLE": "Variable sucked"},
                )(f)
            if hasattr(o, "universal_flow_config_variables"):
                f = mock.patch.object(
                    o,
                    "universal_flow_config_variables",
                    MOCK_FLOW_VARS,
                )(f)
            if hasattr(o, "all_variables"):
                f = mock.patch.object(
                    o,
                    "all_variables",
                    MOCK_FLOW_VARS,
                )(f)

        return f

    return decorator


@pytest.fixture()
@mock_variables()
def mock_config():
    from openlane.config import Config

    mock_config, _ = Config.load(
        {
            "DESIGN_NAME": "whatever",
            "VERILOG_FILES": "dir::src/*.v",
        },
        MOCK_FLOW_VARS,
        design_dir="/cwd",
        pdk="dummy",
        scl="dummy_scl",
        pdk_root="/pdk",
    )
    return mock_config


def pytest_configure():
    pytest.MOCK_PDK_VARS = MOCK_PDK_VARS
    pytest.MOCK_FLOW_VARS = MOCK_FLOW_VARS
    pytest.mock_variables = mock_variables
    pytest.DiodeOnPortsEnum = DiodeOnPortsEnum
