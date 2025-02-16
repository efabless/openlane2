# Copyright 2023-2025 Efabless Corporation
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
import io
from decimal import Decimal
import pytest

MAGIC_EXAMPLE = """RAM8
----------------------------------------
P-diff distance to N-tap must be < 15.0um (LU.3)
----------------------------------------
17.990um 21.995um 18.265um 22.995um
20.905um 22.935um 21.575um 22.995um
18.535um 21.995um 18.795um 22.635um
"""

FEEDBACK_EXAMPLE = """
box 222756 88994 223076 89176
feedback add "Illegal overlap between obsm4 and metal4 (types do not connect)" medium
box 222756 88758 222798 88994
feedback add "Illegal overlap between obsm4 and metal4 (types do not connect)" medium
box 222798 88758 223034 88994
feedback add "Illegal overlap between obsm4 and via4 (types do not connect)" medium
box 223034 88758 223076 88994
feedback add "Illegal overlap between obsm4 and metal4 (types do not connect)" medium
box 222756 88674 223076 88758
feedback add "Illegal overlap between obsm4 and metal4 (types do not connect)" medium
box 222756 88438 222798 88674
feedback add "Illegal overlap between obsm4 and metal4 (types do not connect)" medium
box 222798 88438 223034 88674
feedback add "Illegal overlap between obsm4 and via4 (types do not connect)" medium
box 223034 88438 223076 88674
feedback add "Illegal overlap between obsm4 and metal4 (types do not connect)" medium
box 222756 88354 223076 88438
feedback add "Illegal overlap between obsm4 and metal4 (types do not connect)" medium
box 222756 88256 222798 88354
feedback add "Illegal overlap between obsm4 and metal4 (types do not connect)" medium
box 222798 88256 223034 88354
feedback add "Illegal overlap between obsm4 and via4 (types do not connect)" medium
box 223034 88256 223076 88354
feedback add "Illegal overlap between obsm4 and metal4 (types do not connect)" medium
box 164643 161603 164761 161713
feedback add "device missing 1 terminal;
 connecting remainder to node VGND" pale
box 164643 161263 164761 161437
feedback add "device missing 1 terminal;
 connecting remainder to node VPWR" pale
box 164091 161603 164485 161713
feedback add "device missing 1 terminal;
 connecting remainder to node VGND" pale
box 164091 161263 164485 161437
feedback add "device missing 1 terminal;
 connecting remainder to node VPWR" pale
box 163723 160719 164301 160829
feedback add "device missing 1 terminal;
 connecting remainder to node VGND" pale
box 163723 160995 164301 161169
feedback add "device missing 1 terminal;
 connecting remainder to node VPWR" pale
box 162987 161603 163933 161713
feedback add "device missing 1 terminal;
 connecting remainder to node VGND" pale
box 162987 161263 163933 161437
feedback add "device missing 1 terminal;
 connecting remainder to node VPWR" pale
box 7875 160515 8085 160625
feedback add "device missing 1 terminal;
 connecting remainder to node VGND" pale
box 7875 160175 8085 160349
feedback add "device missing 1 terminal;
 connecting remainder to node VPWR" pale
"""

OPENROAD_EXAMPLE = """
violation type: Short
	srcs: net:_03401_ net:net870
	bbox = (330.4400, 346.8900) - (330.5800, 347.0300) on Layer met1
violation type: Short
	srcs: net:_03401_ net:_03430_
	bbox = (330.4400, 346.2200) - (330.5800, 346.3600) on Layer met1
violation type: Short
	srcs: net:_01612_ net:_01616_
	bbox = (427.9150, 139.5000) - (428.0550, 139.6400) on Layer met1
violation type: Short
	srcs: net:_03401_ net:net870
	bbox = (330.8250, 346.8900) - (331.1150, 347.0300) on Layer met1
violation type: Short
	srcs: net:_03401_ net:net870
	bbox = (330.4400, 346.9000) - (331.1150, 347.0300) on Layer met1
violation type: Metal Spacing
	srcs: net:net1599
	bbox = (312.4250, 357.6400) - (312.7150, 357.7350) on Layer met1\
"""


def test_magic_drc():
    from openlane.common import DRC, Violation, BoundingBox

    drc_object, count = DRC.from_magic(io.StringIO(MAGIC_EXAMPLE))
    violations = {
        "LU.3": Violation(
            rules=[("LU", "3")],
            description="P-diff distance to N-tap must be < 15.0um (LU.3)",
            bounding_boxes=[
                BoundingBox(
                    Decimal("17.990"),
                    Decimal("21.995"),
                    Decimal("18.265"),
                    Decimal("22.995"),
                ),
                BoundingBox(
                    Decimal("20.905"),
                    Decimal("22.935"),
                    Decimal("21.575"),
                    Decimal("22.995"),
                ),
                BoundingBox(
                    Decimal("18.535"),
                    Decimal("21.995"),
                    Decimal("18.795"),
                    Decimal("22.635"),
                ),
            ],
        )
    }

    assert drc_object.module == "RAM8", "Failed to extract module object"
    assert count == 3, "Incorrect module count"
    assert violations == drc_object.violations, "Violation mismatch"


def test_magic_drc_badrule():
    from openlane.common import DRC

    description = "P-diff distance to N-tap must be < 15.0um (egg salad)"
    magic_bad_rule_example = f"""RAM8
    ----------------------------------------
    {description}
    ----------------------------------------
    17.990um 21.995um 18.265um 22.995um
    20.905um 22.935um 21.575um 22.995um
    18.535um 21.995um 18.795um 22.635um
    """

    drc_object, _ = DRC.from_magic(io.StringIO(magic_bad_rule_example))
    assert (
        drc_object.violations["UNKNOWN.UNKNOWN0"].description == description
    ), "bad rule name improperly handled"


def test_magic_drc_exceptions():
    from openlane.common import DRC

    BAD_MAGIC_EXAMPLE = """
    ----------------------------------------
    P-diff distance to N-tap must be < 15.0um (LU.3)
    ----------------------------------------
    invalid example bounding box
    """

    with pytest.raises(ValueError, match="number is invalid"):
        DRC.from_magic(io.StringIO(BAD_MAGIC_EXAMPLE))

    BAD_MAGIC_EXAMPLE_2 = """
    ----------------------------------------
    P-diff distance to N-tap must be < 15.0um (LU.3)
    ----------------------------------------
    18.535um 21.995um 18.795um 22.635um 22.635um
    """

    with pytest.raises(ValueError, match="bounding box has 5/4 elements"):
        DRC.from_magic(io.StringIO(BAD_MAGIC_EXAMPLE_2))


def test_magic_feedback():
    from openlane.common import DRC, Violation, BoundingBox

    expected_violations = {
        "obsm4-metal4.ILLEGAL_OVERLAP": Violation(
            rules=[("obsm4-metal4", "ILLEGAL_OVERLAP")],
            description="Illegal overlap between obsm4 and metal4 (types do not connect)",
            bounding_boxes=[
                BoundingBox(
                    Decimal("11137.80"),
                    Decimal("4449.70"),
                    Decimal("11153.80"),
                    Decimal("4458.80"),
                ),
                BoundingBox(
                    Decimal("11137.80"),
                    Decimal("4437.90"),
                    Decimal("11139.90"),
                    Decimal("4449.70"),
                ),
                BoundingBox(
                    Decimal("11151.70"),
                    Decimal("4437.90"),
                    Decimal("11153.80"),
                    Decimal("4449.70"),
                ),
                BoundingBox(
                    Decimal("11137.80"),
                    Decimal("4433.70"),
                    Decimal("11153.80"),
                    Decimal("4437.90"),
                ),
                BoundingBox(
                    Decimal("11137.80"),
                    Decimal("4421.90"),
                    Decimal("11139.90"),
                    Decimal("4433.70"),
                ),
                BoundingBox(
                    Decimal("11151.70"),
                    Decimal("4421.90"),
                    Decimal("11153.80"),
                    Decimal("4433.70"),
                ),
                BoundingBox(
                    Decimal("11137.80"),
                    Decimal("4417.70"),
                    Decimal("11153.80"),
                    Decimal("4421.90"),
                ),
                BoundingBox(
                    Decimal("11137.80"),
                    Decimal("4412.80"),
                    Decimal("11139.90"),
                    Decimal("4417.70"),
                ),
                BoundingBox(
                    Decimal("11151.70"),
                    Decimal("4412.80"),
                    Decimal("11153.80"),
                    Decimal("4417.70"),
                ),
            ],
        ),
        "obsm4-via4.ILLEGAL_OVERLAP": Violation(
            rules=[("obsm4-via4", "ILLEGAL_OVERLAP")],
            description="Illegal overlap between obsm4 and via4 (types do not connect)",
            bounding_boxes=[
                BoundingBox(
                    Decimal("11139.90"),
                    Decimal("4437.90"),
                    Decimal("11151.70"),
                    Decimal("4449.70"),
                ),
                BoundingBox(
                    Decimal("11139.90"),
                    Decimal("4421.90"),
                    Decimal("11151.70"),
                    Decimal("4433.70"),
                ),
                BoundingBox(
                    Decimal("11139.90"),
                    Decimal("4412.80"),
                    Decimal("11151.70"),
                    Decimal("4417.70"),
                ),
            ],
        ),
        "UNKNOWN.UNKNOWN2": Violation(
            rules=[("UNKNOWN", "UNKNOWN2")],
            description="device missing 1 terminal;\n connecting remainder to node VGND",
            bounding_boxes=[
                BoundingBox(
                    Decimal("8232.15"),
                    Decimal("8080.15"),
                    Decimal("8238.05"),
                    Decimal("8085.65"),
                ),
                BoundingBox(
                    Decimal("8204.55"),
                    Decimal("8080.15"),
                    Decimal("8224.25"),
                    Decimal("8085.65"),
                ),
                BoundingBox(
                    Decimal("8186.15"),
                    Decimal("8035.95"),
                    Decimal("8215.05"),
                    Decimal("8041.45"),
                ),
                BoundingBox(
                    Decimal("8149.35"),
                    Decimal("8080.15"),
                    Decimal("8196.65"),
                    Decimal("8085.65"),
                ),
                BoundingBox(
                    Decimal("393.75"),
                    Decimal("8025.75"),
                    Decimal("404.25"),
                    Decimal("8031.25"),
                ),
            ],
        ),
        "UNKNOWN.UNKNOWN3": Violation(
            rules=[("UNKNOWN", "UNKNOWN3")],
            description="device missing 1 terminal;\n connecting remainder to node VPWR",
            bounding_boxes=[
                BoundingBox(
                    Decimal("8232.15"),
                    Decimal("8063.15"),
                    Decimal("8238.05"),
                    Decimal("8071.85"),
                ),
                BoundingBox(
                    Decimal("8204.55"),
                    Decimal("8063.15"),
                    Decimal("8224.25"),
                    Decimal("8071.85"),
                ),
                BoundingBox(
                    Decimal("8186.15"),
                    Decimal("8049.75"),
                    Decimal("8215.05"),
                    Decimal("8058.45"),
                ),
                BoundingBox(
                    Decimal("8149.35"),
                    Decimal("8063.15"),
                    Decimal("8196.65"),
                    Decimal("8071.85"),
                ),
                BoundingBox(
                    Decimal("393.75"),
                    Decimal("8008.75"),
                    Decimal("404.25"),
                    Decimal("8017.45"),
                ),
            ],
        ),
    }
    drc_object, count = DRC.from_magic_feedback(
        io.StringIO(FEEDBACK_EXAMPLE), Decimal("0.05"), "EXAMPLE"
    )
    assert count == 22, "Incorrect number of violations extracted"
    assert (
        drc_object.violations == expected_violations
    ), "Violations extracted have one or more critical data mismatches"


def test_openroad_drc():
    from openlane.common import DRC, Violation, BoundingBox

    drc_object, count = DRC.from_openroad(io.StringIO(OPENROAD_EXAMPLE), "EXAMPLE")

    assert count == 6, "Incorrect number of violations extracted"
    assert drc_object.violations == {
        "Metal Spacing": Violation(
            rules=[("met1", "Metal Spacing")],
            description="Metal Spacing",
            bounding_boxes=[
                BoundingBox(
                    llx=Decimal("312.4250"),
                    lly=Decimal("357.6400"),
                    urx=Decimal("312.7150"),
                    ury=Decimal("357.7350"),
                    info="net:net1599 to " "None",
                )
            ],
        ),
        "Short": Violation(
            rules=[("met1", "Short")],
            description="Short",
            bounding_boxes=[
                BoundingBox(
                    llx=Decimal("330.4400"),
                    lly=Decimal("346.8900"),
                    urx=Decimal("330.5800"),
                    ury=Decimal("347.0300"),
                    info="net:_03401_ to " "net:net870",
                ),
                BoundingBox(
                    llx=Decimal("330.4400"),
                    lly=Decimal("346.2200"),
                    urx=Decimal("330.5800"),
                    ury=Decimal("346.3600"),
                    info="net:_03401_ to " "net:_03430_",
                ),
                BoundingBox(
                    llx=Decimal("427.9150"),
                    lly=Decimal("139.5000"),
                    urx=Decimal("428.0550"),
                    ury=Decimal("139.6400"),
                    info="net:_01612_ to " "net:_01616_",
                ),
                BoundingBox(
                    llx=Decimal("330.8250"),
                    lly=Decimal("346.8900"),
                    urx=Decimal("331.1150"),
                    ury=Decimal("347.0300"),
                    info="net:_03401_ to " "net:net870",
                ),
                BoundingBox(
                    llx=Decimal("330.4400"),
                    lly=Decimal("346.9000"),
                    urx=Decimal("331.1150"),
                    ury=Decimal("347.0300"),
                    info="net:_03401_ to " "net:net870",
                ),
            ],
        ),
    }, "Violations extracted have one or more critical data mismatches"


def test_klayout_xml():
    from openlane.common import DRC
    from xml.etree import ElementTree as ET

    drc_object, _ = DRC.from_magic(io.StringIO(MAGIC_EXAMPLE))

    bio = io.BytesIO()
    drc_object.to_klayout_xml(bio)

    try:
        parsed = ET.fromstring(bio.getvalue().decode("utf8"))
    except Exception as e:
        pytest.fail(f"Unexpected error while attempting to parse generated XML: {e}")

    assert parsed.find(".//categories/category[1]/name").text == "LU.3"
