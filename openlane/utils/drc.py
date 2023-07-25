# Copyright 2020-2023 Efabless Corporation
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
import re
import json
from enum import IntEnum
from decimal import Decimal, InvalidOperation
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Tuple, Dict

BoundingBox = Tuple[Decimal, Decimal, Decimal, Decimal]  # microns


@dataclass
class Violation:
    rules: List[Tuple[str, str]]
    description: str
    bounding_boxes: List[BoundingBox] = field(default_factory=list)

    @property
    def layer(self) -> str:
        return self.rules[0][0]

    @property
    def rule(self) -> str:
        return self.rules[0][1]

    @property
    def category_name(self) -> str:
        return f"{self.layer}.{self.rule}"


@dataclass
class DRC:
    module: str
    violations: Dict[str, Violation]

    @classmethod
    def from_magic(
        Self,
        report: io.TextIOWrapper,
        db_file: Optional[str] = None,
    ) -> Tuple["DRC", int]:
        class State(IntEnum):
            drc = 0
            data = 1
            header = 10

        MAGIC_SPLIT_LINE = "-" * 40
        MAGIC_RULE_LINE_PARSER = re.compile(r"^(.+?)(?:\s*\((.+)\))?$")
        MAGIC_RULE_RX = re.compile(r"([\w\-]+)\.([\w\-]+)")

        violations: Dict[str, Violation] = {}

        violation: Optional[Violation] = None
        state = State.header
        module = "UNKNOWN"
        counter = 0
        bbox_count = 0
        for i, line in enumerate(report):
            line = line.strip()
            if ("[INFO]" in line) or (line == ""):
                continue

            if MAGIC_SPLIT_LINE in line:
                if state.value > 0:
                    violation = None
                    state = State.drc
                else:
                    state = State.data
            elif state == State.header:
                module = line
            elif state == State.drc:
                match = MAGIC_RULE_LINE_PARSER.match(line)
                assert match is not None, "universal regex did not match string"
                description = match[0]
                rules = []
                if rules_raw := match[2]:
                    for match in MAGIC_RULE_RX.finditer(rules_raw):
                        layer = match[1]
                        rule = match[2]
                        rules.append((layer, rule))
                if len(rules) == 0:
                    rules = [("UNKNOWN", f"UNKNOWN{counter}")]
                violation = Violation(rules, description)
                counter += 1
            elif state == State.data:
                assert violation is not None, "Parser reached an inconsistent state"
                try:
                    coord_list = [Decimal(coord[:-2]) for coord in line.split()]
                except InvalidOperation:
                    raise ValueError(
                        f"invalid bounding box at line {i}: number is invalid"
                    )

                if len(coord_list) != 4:
                    raise ValueError(
                        f"invalid bounding box at line {i}: bounding box has {len(coord_list)}/4 elements"
                    )

                bounding_box: BoundingBox = (
                    coord_list[0],
                    coord_list[1],
                    coord_list[2],
                    coord_list[3],
                )

                violation.bounding_boxes.append(bounding_box)
                violations[violation.category_name] = violation
                bbox_count += 1

        return (Self(module, violations), bbox_count)

    def dumps(self):
        return json.dumps(asdict(self))

    def to_klayout_xml(self, out: io.BufferedIOBase):
        from lxml import etree as ET

        with ET.xmlfile(out, encoding="utf8", buffered=False) as xf:
            with xf.element("report-database"):
                # 1. Cells
                with xf.element("cells"):
                    with xf.element("cell"):
                        name = ET.Element("name")
                        name.text = self.module
                        xf.write(name)
                # 2. Categories
                with xf.element("categories"):
                    for _, violation in self.violations.items():
                        with xf.element("category"):
                            name = ET.Element("name")
                            name.text = violation.category_name
                            description = ET.Element("description")
                            description.text = violation.description
                            xf.write(name, description)
                # 3. Items
                with xf.element("items"):
                    for _, violation in self.violations.items():
                        for bounding_box in violation.bounding_boxes:
                            with xf.element("item"):
                                cell = ET.Element("cell")
                                cell.text = self.module
                                category = ET.Element("category")
                                category.text = violation.category_name
                                visited = ET.Element("visited")
                                visited.text = "false"
                                multiplicity = ET.Element("multiplicity")
                                multiplicity.text = "1"
                                xf.write(cell, category, visited, multiplicity)
                                with xf.element("values"):
                                    llx, lly, urx, ury = bounding_box
                                    value = ET.Element("value")
                                    value.text = f"box: ({llx},{lly};{urx},{ury})"
                                    xf.write(value)
