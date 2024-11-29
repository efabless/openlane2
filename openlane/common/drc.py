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
import shlex
from enum import IntEnum
from decimal import Decimal, InvalidOperation
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Tuple, Dict, Union


BoundingBox = Tuple[Decimal, Decimal, Decimal, Decimal]  # microns
BoundingBoxWithDescription = Tuple[Decimal, Decimal, Decimal, Decimal, str]  # microns


@dataclass
class Violation:
    rules: List[Tuple[str, str]]  # (layer, rule)
    description: str
    bounding_boxes: List[Union[BoundingBox, BoundingBoxWithDescription]] = field(
        default_factory=list
    )

    @property
    def layer(self) -> str:
        return self.rules[0][0]

    @property
    def rule(self) -> str:
        return self.rules[0][1]

    @property
    def category_name(self) -> str:
        return f"{self.layer}.{self.rule}"


illegal_overlap_rx = re.compile(r"between (\w+) and (\w+)")


@dataclass
class DRC:
    """
    A primitive database representing DRC violations generated by a design.
    """

    module: str
    violations: Dict[str, Violation]

    @classmethod
    def from_openroad(
        Self,
        report: io.TextIOWrapper,
        module: str,
    ) -> Tuple["DRC", int]:
        class State(IntEnum):
            vio_type = 0
            src = 1
            bbox = 10

        re_violation = re.compile(r"violation type: (?P<type>.*)$")
        re_src = re.compile(r"srcs: (?P<src1>\S+)( (?P<src2>\S+))?")
        re_bbox = re.compile(
            r"bbox = \( (?P<llx>\S+), (?P<lly>\S+) \) - \( (?P<urx>\S+), (?P<ury>\S+) \) on Layer (?P<layer>\S+)"
        )
        bbox_count = 0
        violations: Dict[str, Violation] = {}
        state = State.vio_type
        vio_type = src1 = src2 = lly = llx = urx = ury = ""
        for line in report:
            line = line.strip()
            if state == State.vio_type:
                vio_match = re_violation.match(line)
                assert vio_match is not None, "Error while parsing drc report file"
                vio_type = vio_match.group("type")
                state = State.src
            elif state == State.src:
                src_match = re_src.match(line)
                assert src_match is not None, "Error while parsing drc report file"
                src1 = src_match.group("src1")
                src2 = src_match.group("src2")
                state = State.bbox
            elif state == State.bbox:
                bbox_match = re_bbox.match(line)
                assert bbox_match is not None, "Error while parsing drc report file"
                llx = bbox_match.group("llx")
                lly = bbox_match.group("lly")
                urx = bbox_match.group("urx")
                ury = bbox_match.group("ury")
                layer = bbox_match.group("layer")
                bbox_count += 1
                bounding_box = (
                    Decimal(llx),
                    Decimal(lly),
                    Decimal(urx),
                    Decimal(ury),
                    f"{src1} to {src2}",
                )
                violation = (layer, vio_type)
                description = vio_type
                if violations.get(vio_type) is not None:
                    violations[vio_type].bounding_boxes.append(bounding_box)
                else:
                    violations[vio_type] = Violation(
                        [violation], description, [bounding_box]
                    )
                state = State.vio_type

        return (Self(module, violations), bbox_count)

    @classmethod
    def from_magic(
        Self,
        report: io.TextIOWrapper,
    ) -> Tuple["DRC", int]:
        """
        Parses a report generated by Magic into a DRC object.

        :param report: A **text** input stream containing the report in question.
            You can pass the result of ``open("drc.rpt")``, for example.
        :returns: A tuple of the DRC object and an int representing the number
            of DRC violations.
        """

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

                bounding_box = (
                    coord_list[0],
                    coord_list[1],
                    coord_list[2],
                    coord_list[3],
                )

                violation.bounding_boxes.append(bounding_box)
                violations[violation.category_name] = violation
                bbox_count += 1

        return (Self(module, violations), bbox_count)

    @classmethod
    def from_magic_feedback(
        Self, feedback: io.TextIOWrapper, cif_scale: Decimal, module: str
    ) -> Tuple["DRC", int]:
        bbox_count = 0
        violations: Dict[str, Violation] = {}
        last_bounding_box: Optional[BoundingBox] = None
        lex = shlex.shlex(feedback.read(), posix=True)
        components = list(lex)
        while len(components):
            instruction = components.pop(0)
            if instruction == "box":
                if len(components) < 4:
                    raise ValueError(
                        "Invalid syntax: 'box' command has less than 4 arguments"
                    )
                lx, ly, ux, uy = components[0:4]
                last_bounding_box = (
                    Decimal(lx) * cif_scale,
                    Decimal(ly) * cif_scale,
                    Decimal(ux) * cif_scale,
                    Decimal(uy) * cif_scale,
                )
                bbox_count += 1
                components = components[4:]
            elif instruction == "feedback":
                try:
                    subcmd = components.pop(0)
                except IndexError:
                    raise ValueError("feedback not given subcommand")
                if subcmd != "add":
                    raise ValueError(f"Unsuppoorted feedback subcommand {subcmd}")

                try:
                    rule = components.pop(0)
                    _ = components.pop(0)
                except IndexError:
                    raise ValueError(
                        "Invalid syntax: 'feedback add' command has less than 2 arguments"
                    )
                vio_layer = "UNKNOWN"
                vio_rulenum = f"UNKNOWN{len(violations)}"
                if "Illegal overlap" in rule:
                    vio_rulenum = "ILLEGAL_OVERLAP"
                    if match := illegal_overlap_rx.search(rule):
                        vio_layer = "-".join((match[1], match[2]))
                if rule not in violations:
                    violations[rule] = Violation([(vio_layer, vio_rulenum)], rule, [])
                if last_bounding_box is None:
                    raise ValueError("Attempted to add feedback without a box selected")
                violations[rule].bounding_boxes.append(last_bounding_box)
        violations = {vio.category_name: vio for vio in violations.values()}
        return (Self(module, violations), bbox_count)

    def dumps(self):
        """
        :returns: The DRC object as a JSON string.
        """
        return json.dumps(asdict(self))

    def to_klayout_xml(self, out: io.BufferedIOBase):
        """
        Converts the DRC object to a KLayout-compatible XML database.

        :param out: A **binary** output stream to the target XML file.
            You can pass the result of ``open("drc.xml",  "wb")``, for example.
        """
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
                                category.text = f"'{violation.category_name}'"
                                visited = ET.Element("visited")
                                visited.text = "false"
                                multiplicity = ET.Element("multiplicity")
                                multiplicity.text = str(len(violation.bounding_boxes))
                                xf.write(cell, category, visited, multiplicity)
                                with xf.element("values"):
                                    value = ET.Element("value")
                                    value.text = f"polygon: ({bounding_box[0]},{bounding_box[1]};{bounding_box[2]},{bounding_box[1]};{bounding_box[2]},{bounding_box[3]};{bounding_box[0]},{bounding_box[3]})"
                                    xf.write(value)
                                    if len(bounding_box) == 5:
                                        value = ET.Element("value")
                                        value.text = f"text: '{bounding_box[4]}'"
                                        xf.write(value)
