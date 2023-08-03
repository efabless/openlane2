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
import textwrap

import pytest
from pyfakefs.fake_filesystem_unittest import Patcher

from openlane.state import DesignFormat


@pytest.fixture()
def mock_macros_config():
    from openlane.config import Config, Macro, Instance

    return Config(
        {
            "DEFAULT_CORNER": "nom_tt_025C_1v80",
            "LIB": {
                "*": "/pdk/my.lib",
            },
            "MACROS": {
                "a": Macro(
                    gds=[""],
                    lef=[""],
                    instances={"instance_a": Instance((0, 10), "N")},
                    nl=[],
                    spef={},
                    lib={
                        "nom_tt_025C_1v80": ["/cwd/a/lib/tt.lib"],
                        "nom_ss_n40C_1v80": ["/cwd/a/lib/ss.lib"],
                        "min_ff_025C_5v00": ["/cwd/a/lib/ff.lib"],
                    },
                    spice=[],
                    sdf={},
                    json_h=None,
                ),
                "b": Macro(
                    gds=[""],
                    lef=[""],
                    instances={"instance_b": Instance((0, 10), "FS")},
                    nl=[
                        "/cwd/b/spef/nl1.v",
                        "/cwd/b/spef/nl2.v",
                    ],
                    spef={
                        "min_*": ["/cwd/b/spef/min.spef"],
                        "nom_*": ["/cwd/b/spef/nom.spef"],
                        "max_*": ["/cwd/b/spef/max.spef"],
                    },
                    lib={
                        "nom_tt_025C_1v80": ["/cwd/b/lib/tt.lib"],
                        "nom_ss_n40C_1v80": ["/cwd/b/lib/ss.lib"],
                        "min_ff_025C_5v00": ["/cwd/b/lib/ff.lib"],
                    },
                    spice=[],
                    sdf={},
                    json_h=None,
                ),
            },
        }
    )


@pytest.mark.parametrize(
    ("corner", "expected"),
    [
        (None, ["file1.spef", "typical.whatever"]),
        ("nom_ss_n40C_1v80", ["file1.spef", "ss.a", "🥶"]),
        ("min_ff_025C_5v00", []),
    ],
)
def test_filter_views(corner, expected, mock_macros_config):
    from openlane.common import Path
    from openlane.utils import Toolbox

    toolbox = Toolbox(".")
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

    assert (
        toolbox.filter_views(mock_macros_config, views_by_corner, corner) == expected
    ), []


def gmv_parameters(f):
    f = pytest.mark.parametrize(
        ("view", "corner", "unless_exist", "expected"),
        [
            (DesignFormat.LIB, None, None, ["/cwd/a/lib/tt.lib", "/cwd/b/lib/tt.lib"]),
            (DesignFormat.LIB, None, DesignFormat.SPEF, ["/cwd/a/lib/tt.lib"]),
            (DesignFormat.SPEF, "min_ff_025C_5V0", None, ["/cwd/b/spef/min.spef"]),
            (DesignFormat.SPEF, "not_a_real_corner", None, []),
            (
                DesignFormat.NETLIST,
                "nom_ss_n40C_1v80",
                None,
                [
                    "/cwd/b/spef/nl1.v",
                    "/cwd/b/spef/nl2.v",
                ],
            ),
            (
                DesignFormat.LIB,
                "nom_ss_n40C_1v80",
                DesignFormat.NETLIST,
                ["/cwd/a/lib/ss.lib"],
            ),
            (
                DesignFormat.SDC,
                "nom_ss_n40C_1v80",
                None,
                [],
            ),
        ],
    )(f)
    return f


@gmv_parameters
def test_get_macro_views_without_macros(
    view,
    corner,
    unless_exist,
    expected,
):
    from openlane.config import Config
    from openlane.utils import Toolbox

    toolbox = Toolbox(".")

    assert (
        toolbox.get_macro_views(
            Config({"DEFAULT_CORNER": "nom_ss_n40C_1v80", "MACROS": None}),
            view,
            corner,
            unless_exist,
        )
        == []
    ), "get_macro_views with empty macro object returned a non-empty list"


@gmv_parameters
def test_get_macro_views_with_macros(
    view,
    corner,
    unless_exist,
    expected,
    mock_macros_config,
):
    from openlane.utils import Toolbox

    toolbox = Toolbox(".")

    assert (
        toolbox.get_macro_views(mock_macros_config, view, corner, unless_exist)
        == expected
    ), "get_macro_views returned unexpected result"


@pytest.mark.parametrize(
    (
        "timing_corner",
        "prioritize_nl",
        "expected",
    ),
    [
        (
            None,
            False,
            (
                "nom_tt_025C_1v80",
                ["/pdk/my.lib", "/cwd/a/lib/tt.lib", "/cwd/b/lib/tt.lib"],
            ),
        ),
        (
            None,
            True,
            (
                "nom_tt_025C_1v80",
                [
                    "/pdk/my.lib",
                    "/cwd/a/lib/tt.lib",
                    "/cwd/b/spef/nl1.v",
                    "/cwd/b/spef/nl2.v",
                    "instance_b@/cwd/b/spef/nom.spef",
                ],
            ),
        ),
        (
            "min_ff_025C_5v00",
            True,
            (
                "min_ff_025C_5v00",
                [
                    "/pdk/my.lib",
                    "/cwd/a/lib/ff.lib",
                    "/cwd/b/spef/nl1.v",
                    "/cwd/b/spef/nl2.v",
                    "instance_b@/cwd/b/spef/min.spef",
                ],
            ),
        ),
    ],
)
def test_get_timing_files(timing_corner, prioritize_nl, expected, mock_macros_config):
    from openlane.utils import Toolbox

    toolbox = Toolbox(".")

    assert (
        toolbox.get_timing_files(
            mock_macros_config,
            timing_corner,
            prioritize_nl,
        )
        == expected
    ), "get_timing_files returned unexpected result"


def test_get_timing_files_warnings(
    caplog: pytest.LogCaptureFixture,
    mock_macros_config,
):
    from openlane.utils import Toolbox

    toolbox = Toolbox(".")

    cfg = mock_macros_config

    # 0. Missing netlists
    netlist_bk = cfg["MACROS"]["b"].nl
    cfg["MACROS"]["b"].nl = []

    assert toolbox.get_timing_files(cfg, None, True,) == (
        "nom_tt_025C_1v80",
        ["/pdk/my.lib", "/cwd/a/lib/tt.lib", "/cwd/b/lib/tt.lib"],
    ), "get_timing_files returned unexpected result"

    assert (
        "but no netlist found" in caplog.text
    ), "get_timing_files did not warn about missing netlists"

    cfg["MACROS"]["b"].nl = netlist_bk

    # 1. Missing spefs
    spefs_bk = cfg["MACROS"]["b"].spef
    cfg["MACROS"]["b"].spef = {}

    assert toolbox.get_timing_files(cfg, None, True,) == (
        "nom_tt_025C_1v80",
        ["/pdk/my.lib", "/cwd/a/lib/tt.lib", "/cwd/b/lib/tt.lib"],
    ), "get_timing_files returned unexpected result"

    assert (
        "but no parasitics extraction found" in caplog.text
    ), "get_timing_files did not warn about missing spefs"

    cfg["MACROS"]["b"].spef = spefs_bk

    # 2. No SCLs
    cfg = cfg.copy(LIB={})

    assert toolbox.get_timing_files(cfg, None, True,) == (
        "nom_tt_025C_1v80",
        [
            "/cwd/a/lib/tt.lib",
            "/cwd/b/spef/nl1.v",
            "/cwd/b/spef/nl2.v",
            "instance_b@/cwd/b/spef/nom.spef",
        ],
    ), "get_timing_files returned unexpected result"

    assert (
        "No SCL lib files" in caplog.text
    ), "get_timing_files did not warn about missing SCL liberty"


@pytest.fixture()
def _lib_mock_fs():
    with Patcher() as patcher:
        patcher.fs.create_dir("/cwd")
        os.chdir("/cwd")
        patcher.fs.create_file(
            "/cwd/example_lib.lib",
            contents=textwrap.dedent(
                """
                library ("example_lib") {
                    cell ("example_lib__cell0") {
                    }
                    cell ("example_lib__cell1") {
                        property (x) {
                            
                        }
                    }
                    cell ("example_lib__cell2") {
                    }
                }
                """
            ),
        )
        patcher.fs.create_file(
            "/cwd/example_lib2.lib",
            contents=textwrap.dedent(
                """
                library ("example_lib2") {
                    cell ("example_lib2__cell0") {
                    }
                    cell ("example_lib2__cell1") {
                    }
                    cell ("example_lib2__cell2") {
                    }
                }
                """
            ),
        )
        patcher.fs.create_file(
            "/cwd/bad_cell_list.txt",
            contents=textwrap.dedent(
                """
                example_lib__cell0
                example_lib2__cell1
                example_lib2__cell2
                """
            ),
        )
        yield


@pytest.fixture()
def lib_trim_result():
    return [
        textwrap.dedent(
            """
                library ("example_lib") {
                    /* removed example_lib__cell0 */
                    cell ("example_lib__cell1") {
                        property (x) {

                        }
                    }
                    cell ("example_lib__cell2") {
                    }
                }
                """
        ).strip(),
        textwrap.dedent(
            """
                library ("example_lib2") {
                    cell ("example_lib2__cell0") {
                    }
                    /* removed example_lib2__cell1 */
                    /* removed example_lib2__cell2 */
                }
                """
        ).strip(),
    ]


@pytest.mark.usefixtures("_lib_mock_fs")
def test_remove_cell_list_from_lib(lib_trim_result):
    from openlane.utils import Toolbox

    toolbox = Toolbox(".")

    result = toolbox.remove_cells_from_lib(
        frozenset(["/cwd/example_lib.lib", "/cwd/example_lib2.lib"]),
        excluded_cells=frozenset(["/cwd/bad_cell_list.txt"]),
        as_cell_lists=True,
    )
    for file in result:
        contents = open(file, encoding="utf8").read()
        assert (
            contents.strip() in lib_trim_result
        ), "remove_cells_from_lib produced unexpected result"


@pytest.mark.usefixtures("_lib_mock_fs")
def test_remove_cells_from_lib(lib_trim_result):
    from openlane.utils import Toolbox

    toolbox = Toolbox(".")

    excluded_cells = (
        open("/cwd/bad_cell_list.txt", encoding="utf8").read().strip().splitlines()
    )

    result = toolbox.remove_cells_from_lib(
        frozenset(["/cwd/example_lib.lib", "/cwd/example_lib2.lib"]),
        excluded_cells=frozenset(excluded_cells),
    )
    for file in result:
        contents = open(file, encoding="utf8").read()
        assert (
            contents.strip() in lib_trim_result
        ), "remove_cells_from_lib produced unexpected result"
