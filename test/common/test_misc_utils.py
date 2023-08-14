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


def test_slugify():
    from openlane.common import slugify

    assert slugify("ABCD efg.xy-Z") == "abcd-efg-xy-z", "Failed slugify test"
    assert (
        slugify("Lorem ipsum   dolor sit amet") == "lorem-ipsum-dolor-sit-amet"
    ), "Failed slugify test"


def test_magic_drc():
    from openlane.common import DRC, Violation

    drc_object, count = DRC.from_magic(io.StringIO(MAGIC_EXAMPLE))
    violations = {
        "LU.3": Violation(
            rules=[("LU", "3")],
            description="P-diff distance to N-tap must be < 15.0um (LU.3)",
            bounding_boxes=[
                (
                    Decimal("17.990"),
                    Decimal("21.995"),
                    Decimal("18.265"),
                    Decimal("22.995"),
                ),
                (
                    Decimal("20.905"),
                    Decimal("22.935"),
                    Decimal("21.575"),
                    Decimal("22.995"),
                ),
                (
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
