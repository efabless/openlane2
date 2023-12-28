#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2023 Efabless Corporation
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

from typing import List
from enum import IntEnum

from sphinx.application import Sphinx


def setup(app):
    app.connect("source-read", subst_migration_comparison)
    return {"version": "1.0", "parallel_read_safe": True}


def subst_migration_comparison(app: Sphinx, docname: str, sourceRef: List[str]):
    class State(IntEnum):
        default = 0
        before = 1
        after = 2
        rationale = 3

    source = sourceRef[0]

    final_string = ""
    state = State.default
    before = ""
    after = ""
    rationale = ""
    lines_in = source.splitlines()
    START_PFX = "```!migration_comparison"
    if lines_in[0] != "!register migration_comparison":
        return
    for line in lines_in[1:]:
        if state == State.default:
            if line.startswith(START_PFX):
                final_string += line[len(START_PFX) :] + "\n"
                state = State.before
                before = ""
                after = ""
                rationale = ""
            else:
                final_string += line + "\n"
        elif state == State.before:
            if line == "---":
                state = State.after
                continue
            before += line + "\n"
        elif state == State.after:
            if line == "---":
                state = State.rationale
                continue
            after += line + "\n"
        elif state == State.rationale:
            if line == "```":
                state = State.default
                final_string += f"""
<table style="width: 100%">
<tr>
<th style="width: 50%;"> OpenLane &lt;2.0 </th>
<th style="width: 50%;"> OpenLane ≥2.0    </th>
</tr>
<tr>
<td>

```bash
{before}
```

</td>
<td>

```bash
{after}
```

</td>
</tr>
</table>

{rationale}
"""

                continue
            rationale += line + "\n"

    sourceRef[0] = final_string
    print(final_string)
