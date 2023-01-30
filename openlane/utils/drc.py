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
import re
import json
from enum import IntEnum
from decimal import Decimal
from typing import List, Optional, Tuple
from dataclasses import dataclass, field, asdict

BoundingBox = Tuple[Decimal, Decimal, Decimal, Decimal]  # microns


@dataclass
class Violation:
    layer: str
    rule: str
    description: str
    bounding_boxes: List[BoundingBox] = field(default_factory=list)


@dataclass
class DRC:
    module: str
    violations: List[Violation]

    @classmethod
    def from_magic(Self, report: str) -> "DRC":
        class State(IntEnum):
            drc = 0
            data = 1

        MAGIC_SPLIT_LINE = "-" * 40
        MAGIC_RULE_PARSER = re.compile(r"\s*(.+)\s*\((\w+)\.(\w+)\)\s*")

        report_lines = report.split("\n")

        module = report_lines[0].strip()

        violations: List[Violation] = []
        violation: Optional[Violation] = None

        state = State.data
        for line in report_lines[1:]:
            if ("[INFO]" in line) or (line.strip() == ""):
                continue

            if MAGIC_SPLIT_LINE in line:
                if state == State.data:
                    if violation is not None:
                        violations.append(violation)
                    violation = None
                    state = State.drc
                else:
                    state = State.data
                continue

            if state == State.drc:
                if match := MAGIC_RULE_PARSER.match(line):
                    description = match[1]
                    layer = match[2]
                    rule = match[3]
                    violation = Violation(layer, rule, description)
            else:
                coord_list = [Decimal(coord[:-2]) for coord in line.split()]
                bounding_box: BoundingBox = (
                    coord_list[0],
                    coord_list[1],
                    coord_list[2],
                    coord_list[3],
                )
                if violation is None:
                    raise ValueError("Malformed Magic report")
                else:
                    violation.bounding_boxes.append(bounding_box)

        if violation is not None:
            violations.append(violation)
        violation = None

        return Self(module, violations)

    def dumps(self):
        return json.dumps(asdict(self))

    def to_klayout_xml(self):
        import xml.etree.ElementTree as ET
        import xml.dom.minidom as minidom

        def prettify(elem):  # Return a pretty-printed XML string for the Element.
            rough_string = ET.tostring(elem, "utf8")
            reparsed = minidom.parseString(rough_string)
            return reparsed.toprettyxml(indent="    ", newl="\n")

        report_database = ET.Element("report-database")
        categories = ET.SubElement(report_database, "categories")
        cells = ET.SubElement(report_database, "cells")
        cell = ET.SubElement(cells, "cell")
        ET.SubElement(cell, "name").text = self.module

        items = ET.SubElement(report_database, "items")

        for violation in self.violations:
            category_name = f"{violation.layer}_{violation.rule}"
            category = ET.SubElement(categories, "category")

            ET.SubElement(category, "name").text = category_name
            ET.SubElement(category, "description").text = violation.description

            for bounding_box in violation.bounding_boxes:
                item = ET.SubElement(items, "item")

                ET.SubElement(item, "category").text = category_name
                ET.SubElement(item, "cell").text = self.module
                ET.SubElement(item, "visited").text = "false"
                ET.SubElement(item, "multiplicity").text = "1"

                values = ET.SubElement(item, "values")
                llx, lly, urx, ury = bounding_box
                ET.SubElement(values, "value").text = f"box: ({llx},{lly};{urx},{ury})"

        return prettify(report_database)
