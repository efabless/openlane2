#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

import os
import re
import traceback

import jinja2
from sphinx.config import Config
from sphinx.application import Sphinx

import openlane


def setup(app: Sphinx):
    app.connect("config-inited", generate_module_docs)
    return {"version": "1.0"}


newline_rx = re.compile("\n")


def generate_module_docs(app: Sphinx, conf: Config):
    try:
        conf_py_path: str = conf._raw_config["__file__"]
        doc_root_dir: str = os.path.dirname(conf_py_path)

        template_relpath: str = conf.templates_path[0]
        all_templates_path = os.path.abspath(template_relpath)
        template_path = os.path.join(all_templates_path, "generate_configvar_docs")

        lookup = jinja2.FileSystemLoader(searchpath=template_path)

        # Mako-like environment
        env = jinja2.Environment(
            "<%",
            "%>",
            "${",
            "}",
            "<%doc>",
            "</%doc>",
            "%",
            "##",
            loader=lookup,
        )

        # 1. PDK
        template = env.get_template("pdk.md")
        module = openlane.config.pdk
        with open(
            os.path.join(doc_root_dir, "reference", "pdk_config_vars.md"), "w"
        ) as f:
            f.write(
                template.render(
                    module=module,
                )
            )

        # 2. Flow
        template = env.get_template("flow.md")
        module = openlane.config.flow
        with open(
            os.path.join(doc_root_dir, "reference", "flow_config_vars.md"), "w"
        ) as f:
            f.write(
                template.render(
                    module=module,
                )
            )

        # 3. Steps
        template = env.get_template("steps.md")
        factory = openlane.Step.factory

        # Pre-processing
        by_category = {}
        for step in factory.list():
            category, _ = step.split(".")
            if by_category.get(category) is None:
                by_category[category] = []
            by_category[category].append((step, factory.get(step)))

        misc = ("Misc", by_category["Misc"])
        del by_category["Misc"]

        ## Sort Categories
        categories_sorted = list(sorted(by_category.items(), key=lambda c: c[0])) + [
            misc
        ]

        ## Sort Steps
        for i in range(0, len(categories_sorted)):
            category, step_list = categories_sorted[i]
            steps_sorted = list(sorted(step_list, key=lambda s: s[0]))
            categories_sorted[i] = (category, steps_sorted)

        # --

        with open(
            os.path.join(doc_root_dir, "reference", "step_config_vars.md"), "w"
        ) as f:
            f.write(
                template.render(
                    factory=factory,
                    categories_sorted=categories_sorted,
                )
            )

    except Exception:
        print(traceback.format_exc())
        exit(-1)
