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
import re
import subprocess
from typing import List, Optional, Tuple

from .step import Step, StepException, ViewsUpdate, MetricsUpdate
from ..common import DesignFormat
from ..config import Variable
from ..state import State, Path


@Step.factory.register()
class Lint(Step):
    """Lint design verilog source files"""

    id = "Verilator.Lint"
    inputs = []  # The input RTL is part of the configuration
    outputs = []

    config_vars = [
        Variable(
            "VERILOG_FILES",
            List[Path],
            "The paths of the design's Verilog files.",
        ),
        Variable(
            "LINTER_INCLUDE_PDK_MODELS",
            bool,
            "Include verilog models of the PDK",
            default=False,
        ),
        Variable(
            "LINTER_RELATIVE_INCLUDES",
            bool,
            "When a file references an include file, resolve the filename relative to the path of the referencing file, instead of relative to the current directory.",
            default=True,
            deprecated_names=["VERILATOR_RELATIVE_INCLUDES"],
        ),
        Variable(
            "LINTER_ERROR_ON_LATCH",
            bool,
            "When a latch is inferred by an `always` block that is not explicitly marked as `always_latch`, report this as a linter error.",
            default=True,
        ),
        Variable(
            "SYNTH_DEFINES",
            Optional[List[str]],
            "Synthesis defines",
        ),
        Variable(
            "LINTER_DEFINES",
            Optional[List[str]],
            "Linter defines overriding SYNTH_DEFINES",
        ),
        Variable(
            "QUIT_ON_LINTER_WARNINGS",
            bool,
            "Quit on linter warnings.",
            default=False,
            deprecated_names=["QUIT_ON_VERILATOR_WARNINGS"],
        ),
    ]

    def run(self, state_in: State, **kwargs) -> Tuple[ViewsUpdate, MetricsUpdate]:
        kwargs, env = self.extract_env(kwargs)
        views_updates: ViewsUpdate = {}
        metrics_updates: MetricsUpdate = {}
        extra_args = []

        scl_models = (
            self.config["CELL_VERILOG_MODELS"]
            or self.config["CELL_BB_VERILOG_MODELS"]
            or []
        )
        input_models = (
            scl_models
            + self.toolbox.get_macro_views(self.config, DesignFormat.NETLIST)
            + (self.config["EXTRA_VERILOG_MODELS"] or [])
        )  # not +=: break reference!

        defines = self.config["LINTER_DEFINES"] or self.config["SYNTH_DEFINES"] or []

        bb_path = self.toolbox.create_blackbox_model(
            frozenset([str(path) for path in input_models]),
            frozenset(defines),
        )

        bb_with_guards = os.path.join(self.step_dir, "bb.v")
        with open(bb_path, "r", encoding="utf8",) as bb_in, open(
            bb_with_guards,
            "w",
            encoding="utf8",
        ) as bb_out:
            "\n/* verilator lint_off UNUSEDSIGNAL */\n$out_str\n/* verilator lint_on UNUSEDSIGNAL */\n/* verilator lint_on UNDRIVEN */"
            print("/* verilator lint_off UNDRIVEN */", file=bb_out)
            print("/* verilator lint_off UNUSEDSIGNAL */", file=bb_out)
            for line in bb_in:
                bb_out.write(line)
            print("/* verilator lint_on UNDRIVEN */", file=bb_out)
            print("/* verilator lint_on UNUSEDSIGNAL */", file=bb_out)

        if not self.config["QUIT_ON_LINTER_WARNINGS"]:
            extra_args.append("--Wno-fatal")

        if self.config["LINTER_RELATIVE_INCLUDES"]:
            extra_args.append("--relative-includes")

        if self.config["LINTER_ERROR_ON_LATCH"]:
            extra_args.append("--Werror-LATCH")

        for define in defines:
            extra_args.append(f"+define+{define}")
        extra_args += defines

        exit_error: Optional[subprocess.CalledProcessError] = None
        try:
            self.run_subprocess(
                [
                    "verilator",
                    "--lint-only",
                    "--Wall",
                    "--Wno-DECLFILENAME",
                    "--Wno-EOFNEWLINE",
                    "--top-module",
                    self.config["DESIGN_NAME"],
                ]
                + [bb_with_guards]
                + self.config["VERILOG_FILES"]
                + extra_args,
                env=env,
            )
        except subprocess.CalledProcessError as e:
            exit_error = e

        warnings_count = 0
        errors_count = 0
        latch_count = 0
        timing_constructs = 0

        exiting_rx = re.compile(r"^\s*%Error: Exiting due to (\d+) error\(s\)")
        with open(self.get_log_path(), "r", encoding="utf8") as f:
            for line in f:
                line = line.strip()
                if r"%Warning-" in line:
                    warnings_count += 1
                if r"%Error-LATCH" in line:
                    latch_count += 1
                if r"%Error-NEEDTIMINGOPT" in line:
                    timing_constructs = 1
                if match := exiting_rx.search(line):
                    errors_count = int(match[1])

            if exit_error is not None and errors_count == 0:
                raise StepException(
                    f"Verilator exited unexpectedly: Not exiting due to errors"
                )

        metrics_updates.update({"design__lint_errors__count": errors_count})
        metrics_updates.update(
            {"design__lint_timing_constructs__count": timing_constructs}
        )
        metrics_updates.update({"design__lint_warnings__count": warnings_count})
        metrics_updates.update({"design__latch__count": latch_count})
        return views_updates, metrics_updates

    def layout_preview(self) -> Optional[str]:
        return None
