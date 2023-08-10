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
from decimal import Decimal

import pytest

from openlane.config import config
from openlane.common import Path


mock_variables = pytest.mock_variables
DiodeOnPortsEnum = pytest.DiodeOnPortsEnum


@pytest.mark.usefixtures("_mock_conf_fs")
@mock_variables()
def test_dict_config():
    from openlane.config import Meta, Config

    cfg, _ = Config.load(
        {"DESIGN_NAME": "whatever", "VERILOG_FILES": "dir::src/*.v"},
        config.flow_common_variables,
        design_dir="/cwd",
        pdk="dummy",
        scl="dummy_scl",
        pdk_root="/pdk",
    )

    assert_cfg = Config(
        {
            "DESIGN_DIR": "/cwd",
            "DESIGN_NAME": "whatever",
            "PDK": "dummy",
            "STD_CELL_LIBRARY": "dummy_scl",
            "VERILOG_FILES": ["/cwd/src/a.v", "/cwd/src/b.v"],
            "EXAMPLE_PDK_VAR": Decimal("10"),
            "GRT_REPAIR_ANTENNAS": True,
            "RUN_HEURISTIC_DIODE_INSERTION": False,
            "DIODE_ON_PORTS": DiodeOnPortsEnum.none,
            "MACROS": None,
            "TECH_LEFS": {
                "nom_*": Path(
                    "/pdk/dummy/libs.ref/techlef/dummy_scl/dummy_tech_lef.tlef"
                )
            },
            "DEFAULT_CORNER": "nom_tt_025C_1v80",
        },
        meta=Meta(version=2, flow=None),
    )
    assert cfg == assert_cfg, "Generated configuration does not match expected value"


@pytest.mark.usefixtures("_mock_conf_fs")
@mock_variables()
def test_json_config():
    from openlane.config import Meta, Config

    with open("/cwd/config.json", "w") as f:
        f.write(
            """
            {
                "meta": {
                    "version": 2,
                    "flow": "Whatever"
                },
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
            "DESIGN_DIR": "/cwd",
            "DESIGN_NAME": "whatever",
            "PDK": "dummy",
            "STD_CELL_LIBRARY": "dummy_scl",
            "VERILOG_FILES": ["/cwd/src/a.v", "/cwd/src/b.v"],
            "EXAMPLE_PDK_VAR": Decimal("10"),
            "GRT_REPAIR_ANTENNAS": True,
            "RUN_HEURISTIC_DIODE_INSERTION": False,
            "DIODE_ON_PORTS": DiodeOnPortsEnum.none,
            "MACROS": None,
            "TECH_LEFS": {
                "nom_*": Path(
                    "/pdk/dummy/libs.ref/techlef/dummy_scl/dummy_tech_lef.tlef"
                )
            },
            "DEFAULT_CORNER": "nom_tt_025C_1v80",
        },
        meta=Meta(version=2, flow="Whatever"),
    ), "Generated configuration does not match expected value"

    assert Config.get_meta("/cwd/config.json", flow_override="OtherWhatever") == Meta(
        version=2, flow="OtherWhatever"
    ), "get_meta test failed"


@pytest.mark.usefixtures("_mock_conf_fs")
@mock_variables()
def test_tcl_config():
    from openlane.config import Meta, Config

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
            "DESIGN_DIR": "/cwd",
            "DESIGN_NAME": "whatever",
            "PDK": "dummy",
            "STD_CELL_LIBRARY": "dummy_scl",
            "VERILOG_FILES": ["/cwd/src/a.v", "/cwd/src/b.v"],
            "EXAMPLE_PDK_VAR": Decimal("10"),
            "GRT_REPAIR_ANTENNAS": True,
            "RUN_HEURISTIC_DIODE_INSERTION": False,
            "DIODE_ON_PORTS": DiodeOnPortsEnum.none,
            "MACROS": None,
            "TECH_LEFS": {
                "nom_*": Path(
                    "/pdk/dummy/libs.ref/techlef/dummy_scl/dummy_tech_lef.tlef"
                )
            },
            "DEFAULT_CORNER": "nom_tt_025C_1v80",
        },
        meta=Meta(version=1, flow=None),
    ), "Generated configuration does not match expected value"


@pytest.mark.usefixtures("_mock_conf_fs")
@mock_variables()
def test_copy_filtered():
    from openlane.config import Config, Variable

    step1_variables = [
        Variable(
            "STEP1_VAR",
            int,
            description="x",
        )
    ]
    step2_variables = [
        Variable(
            "STEP2_VAR",
            int,
            description="x",
        )
    ]

    cfg, _ = Config.load(
        {
            "DESIGN_NAME": "whatever",
            "VERILOG_FILES": "dir::src/*.v",
            "STEP1_VAR": 3,
            "STEP2_VAR": 4,
        },
        config.flow_common_variables + step1_variables + step2_variables,
        design_dir="/cwd",
        pdk="dummy",
        scl="dummy_scl",
        pdk_root="/pdk",
    )

    step1_cfg = cfg.copy_filtered(step1_variables, include_pdk_variables=False)

    assert step1_cfg == {
        "DESIGN_DIR": "/cwd",
        "DESIGN_NAME": "whatever",
        "STEP1_VAR": 3,
        "VERILOG_FILES": ["/cwd/src/a.v", "/cwd/src/b.v"],
        "meta": cfg.meta,
        "GRT_REPAIR_ANTENNAS": True,
        "RUN_HEURISTIC_DIODE_INSERTION": False,
        "DIODE_ON_PORTS": DiodeOnPortsEnum.none,
        "MACROS": None,
    }, "copy_filtered for step 1 did not work properly"

    step2_cfg = cfg.copy_filtered(step2_variables, include_common_variables=False)

    assert step2_cfg == {
        "STEP2_VAR": 4,
        "PDK": "dummy",
        "STD_CELL_LIBRARY": "dummy_scl",
        "EXAMPLE_PDK_VAR": Decimal("10"),
        "meta": cfg.meta,
        "TECH_LEFS": {
            "nom_*": Path("/pdk/dummy/libs.ref/techlef/dummy_scl/dummy_tech_lef.tlef")
        },
        "DEFAULT_CORNER": "nom_tt_025C_1v80",
    }, "copy_filtered for step 2 did not work properly"


@pytest.mark.usefixtures("_mock_conf_fs")
@mock_variables()
def test_automatic_conversion():
    from openlane.config import Config

    with open("/cwd/config.json", "w") as f:
        f.write(
            """
            {
                "DESIGN_NAME": "whatever",
                "VERILOG_FILES": "/cwd/src/a.v /cwd/src/b.v"
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

    assert cfg["VERILOG_FILES"] == [
        "/cwd/src/a.v",
        "/cwd/src/b.v",
    ], "automatic conversion of tcl-style list failed for json file"

    with open("/cwd/config.json", "w") as f:
        f.write(
            """
            {
                "meta": {
                    "version": 2,
                    "flow": "Whatever"
                },
                "DESIGN_NAME": "whatever",
                "VERILOG_FILES": "/cwd/src/a.v /cwd/src/b.v"
            }
            """
        )

    with pytest.raises(
        config.InvalidConfig, match="Refusing to automatically convert"
    ) as e:
        Config.load(
            "/cwd/config.json",
            config.flow_common_variables,
            pdk="dummy",
            scl="dummy_scl",
            pdk_root="/pdk",
        )
    assert e is not None, "invalid config accepted: automatic conversion for meta >= 2"


@pytest.mark.usefixtures("_mock_conf_fs")
@mock_variables()
def test_pdk():
    from openlane.config import InvalidConfig, Config

    cfg1, _ = Config.load(
        {
            "DESIGN_NAME": "whatever",
            "VERILOG_FILES": "dir::src/*.v",
        },
        config.flow_common_variables,
        pdk="dummy",
        design_dir="/cwd",
        pdk_root="/pdk",
    )
    assert cfg1["PDK"] == "dummy", "PDK in argument failed to load"

    cfg1, _ = Config.load(
        {
            "PDK": "dummy2",
            "DESIGN_NAME": "whatever",
            "VERILOG_FILES": "dir::src/*.v",
        },
        config.flow_common_variables,
        design_dir="/cwd",
        pdk_root="/pdk",
    )
    assert cfg1["PDK"] == "dummy2", "PDK in dictionary failed to load"

    cfg2, _ = Config.load(
        {
            "PDK": "dummy2",
            "DESIGN_NAME": "whatever",
            "VERILOG_FILES": "dir::src/*.v",
        },
        config.flow_common_variables,
        design_dir="/cwd",
        pdk_root="/pdk",
        pdk="dummy",
    )
    assert cfg2["PDK"] == "dummy2", "PDK in dictionary does not take priority"

    with pytest.raises(ValueError, match="pdk argument is required") as e:
        Config.load(
            {
                "DESIGN_NAME": "whatever",
                "VERILOG_FILES": "dir::src/*.v",
            },
            config.flow_common_variables,
            design_dir="/cwd",
            pdk_root="/pdk",
        )

    assert e is not None, "configuration loaded without PDK set"

    with pytest.raises(InvalidConfig, match="was not found") as e:
        Config.load(
            {
                "DESIGN_NAME": "whatever",
                "VERILOG_FILES": "dir::src/*.v",
            },
            config.flow_common_variables,
            design_dir="/cwd",
            pdk_root="/pdk",
            pdk="notreal",
        )

    assert e is not None, "configuration loaded without invalid PDK exception"

    with pytest.raises(InvalidConfig, match="not found") as e:
        Config.load(
            {
                "DESIGN_NAME": "whatever",
                "VERILOG_FILES": "dir::src/*.v",
            },
            config.flow_common_variables,
            design_dir="/cwd",
            pdk_root="/pdk",
            pdk="dumm",
        )

    assert True in [
        "similarly-named" in warning for warning in e.value.warnings
    ], "invalid PDK did not return suggestions in warnings"


@pytest.mark.usefixtures("_mock_conf_fs")
@mock_variables()
def test_invalid_keys(caplog: pytest.LogCaptureFixture):
    from openlane.config import InvalidConfig, Config

    with open("/cwd/config.json", "w") as f:
        f.write(
            """
            {
                "DESIGN_NAME": "whatever",
                "VERILOG_FILES": "dir::src/*.v",
                "INVALID_VARIABLE": "potato"
            }
            """
        )

    try:
        Config.load(
            "/cwd/config.json",
            config.flow_common_variables,
            pdk="dummy",
            scl="dummy_scl",
            pdk_root="/pdk",
        )
    except InvalidConfig as e:
        assert (  # noqa: PT017
            e is None
        ), "unknown variable triggered an error when loading from a meta.version: 1 JSON file"

    assert (
        "Unknown key" in caplog.text
    ), "unknown variable did not trigger a warning when loading from a meta.version: 1 JSON file"
    caplog.clear()

    with pytest.raises(InvalidConfig, match="Unknown key") as e:
        Config.load(
            {
                "DESIGN_NAME": "whatever",
                "VERILOG_FILES": "dir::src/*.v",
                "INVALID_VARIABLE": "potato",
            },
            config.flow_common_variables,
            design_dir="/cwd",
            pdk="dummy",
            scl="dummy_scl",
            pdk_root="/pdk",
        )

    assert (
        e is not None
    ), "unknown variable did not trigger an error when loading from dict"

    Config.load(
        {
            "DESIGN_NAME": "whatever",
            "VERILOG_FILES": "dir::src/*.v",
            "REMOVED_VARIABLE": "potato",
        },
        config.flow_common_variables,
        design_dir="/cwd",
        pdk="dummy",
        scl="dummy_scl",
        pdk_root="/pdk",
    )

    assert (
        "has been removed" in caplog.text
    ), "removed variable did not trigger a warning when loading from a meta.version: 1 JSON file"
    caplog.clear()


@pytest.mark.usefixtures("_mock_conf_fs")
@mock_variables()
def test_dis_migration(caplog: pytest.LogCaptureFixture):
    from openlane.config import Config, InvalidConfig

    def set_dis(dis: int):
        with open("/cwd/config.json", "w") as f:
            f.write(
                f"""
                {{
                    "DESIGN_NAME": "whatever",
                    "VERILOG_FILES": "dir::src/*.v",
                    "DIODE_INSERTION_STRATEGY": {dis}
                }}
                """
            )

    for dis in [1, 2, 5, 7, '"cat"']:
        set_dis(dis)
        with pytest.raises(InvalidConfig, match="not available in OpenLane") as e:
            Config.load(
                "/cwd/config.json",
                config.flow_common_variables,
                pdk="dummy",
                scl="dummy_scl",
                pdk_root="/pdk",
            )
        assert e is not None, f"configuration with invalid dis {dis} has been loaded"

    set_dis(0)
    cfg, _ = Config.load(
        "/cwd/config.json",
        config.flow_common_variables,
        pdk="dummy",
        scl="dummy_scl",
        pdk_root="/pdk",
    )

    assert not cfg["GRT_REPAIR_ANTENNAS"], "failed to migrate dis 0 properly"
    assert not cfg["RUN_HEURISTIC_DIODE_INSERTION"], "failed to migrate dis 0 properly"
    assert (
        cfg["DIODE_ON_PORTS"] == DiodeOnPortsEnum.none
    ), "failed to migrate dis 0 properly"

    set_dis(3)
    cfg, _ = Config.load(
        "/cwd/config.json",
        config.flow_common_variables,
        pdk="dummy",
        scl="dummy_scl",
        pdk_root="/pdk",
    )
    assert cfg["GRT_REPAIR_ANTENNAS"], "failed to migrate dis 3 properly"
    assert not cfg["RUN_HEURISTIC_DIODE_INSERTION"], "failed to migrate dis 3 properly"
    assert (
        cfg["DIODE_ON_PORTS"] == DiodeOnPortsEnum.none
    ), "failed to migrate dis 3 properly"

    set_dis(4)
    cfg, _ = Config.load(
        "/cwd/config.json",
        config.flow_common_variables,
        pdk="dummy",
        scl="dummy_scl",
        pdk_root="/pdk",
    )
    assert not cfg["GRT_REPAIR_ANTENNAS"], "failed to migrate dis 4 properly"
    assert cfg["RUN_HEURISTIC_DIODE_INSERTION"], "failed to migrate dis 4 properly"
    assert (
        cfg["DIODE_ON_PORTS"] == DiodeOnPortsEnum["in"]
    ), "failed to migrate dis 4 properly"

    set_dis(6)
    cfg, _ = Config.load(
        "/cwd/config.json",
        config.flow_common_variables,
        pdk="dummy",
        scl="dummy_scl",
        pdk_root="/pdk",
    )
    assert cfg["GRT_REPAIR_ANTENNAS"], "failed to migrate dis 6 properly"
    assert cfg["RUN_HEURISTIC_DIODE_INSERTION"], "failed to migrate dis 6 properly"
    assert (
        cfg["DIODE_ON_PORTS"] == DiodeOnPortsEnum["in"]
    ), "failed to migrate dis 6 properly"

    assert (
        "See 'Migrating DIODE_INSERTION_STRATEGY'" in caplog.text
    ), "diode insertion strategy did not trigger a warning"
    caplog.clear()


@pytest.mark.usefixtures("_mock_conf_fs")
@mock_variables()
def test_macro_migration(
    caplog: pytest.LogCaptureFixture,
):
    from openlane.config import Config, Macro, InvalidConfig

    cfg, _ = Config.load(
        {
            "DESIGN_NAME": "whatever",
            "VERILOG_FILES": "dir::src/*.v",
            "EXTRA_SPEFS": "b /cwd/spef/b.spef /cwd/spef/b.spef /cwd/spef/b.spef",
        },
        config.flow_common_variables,
        design_dir="/cwd",
        pdk="dummy",
        scl="dummy_scl",
        pdk_root="/pdk",
    )

    assert cfg["MACROS"] == {
        "b": Macro(
            gds=[""],
            lef=[""],
            instances={},
            nl=[],
            spef={
                "min_*": ["/cwd/spef/b.spef"],
                "nom_*": ["/cwd/spef/b.spef"],
                "max_*": ["/cwd/spef/b.spef"],
            },
            lib={},
            spice=[],
            sdf={},
            json_h=None,
        )
    }, "Macro migration yielded unexpected result"

    assert (
        "deprecated" in caplog.text
    ), "configuration variable 'EXTRA_SPEFS' is deprecated"
    caplog.clear()

    with pytest.raises(InvalidConfig, match="not divisible by four") as e:
        Config.load(
            {
                "DESIGN_NAME": "whatever",
                "VERILOG_FILES": "dir::src/*.v",
                "EXTRA_SPEFS": "b /cwd/spef/b.spef /cwd/spef/b.spef",
            },
            config.flow_common_variables,
            design_dir="/cwd",
            pdk="dummy",
            scl="dummy_scl",
            pdk_root="/pdk",
        )

    assert e is not None, "invalid EXTRA_SPEFS count accepted"

    with pytest.raises(InvalidConfig, match="Invalid type for 'EXTRA_SPEFS'") as e:
        Config.load(
            {
                "DESIGN_NAME": "whatever",
                "VERILOG_FILES": "dir::src/*.v",
                "EXTRA_SPEFS": 2,
            },
            config.flow_common_variables,
            design_dir="/cwd",
            pdk="dummy",
            scl="dummy_scl",
            pdk_root="/pdk",
        )

    assert e is not None, "invalid EXTRA_SPEFS type accepted"
