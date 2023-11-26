# Copyright 2021-2022 Efabless Corporation
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
# flake8: noqa E402
import odb
import json
from fnmatch import fnmatch
from openroad import Tech, Design

import sys
import locale
import inspect
import functools
from typing import Callable, Dict

# -- START: Environment Fixes
try:
    locale.setlocale(locale.LC_ALL, "C.UTF-8")
except locale.Error:
    # We tried. :)
    pass
# -- END

import click
import rich
from rich.table import Table

# Re-export for subfunctions
rich
click
Table

write_fn: Dict[str, Callable] = {
    "def": lambda reader, file: file and odb.write_def(reader.block, file),
    "odb": lambda reader, file: file and odb.write_db(reader.db, file),
}


class OdbReader(object):
    def __init__(self, *args, **kwargs):
        self.ord_tech = Tech()
        self.design = Design(self.ord_tech)

        if len(args) == 1:
            db_in = args[0]
            self.design.readDb(db_in)
        elif len(args) == 2:
            lef_in, def_in = args
            if not (isinstance(lef_in, list) or isinstance(lef_in, tuple)):
                lef_in = [lef_in]
            for lef in lef_in:
                self.ord_tech.readLef(lef)
            if def_in is not None:
                self.design.readDef(def_in)

        self.config = None
        if "config_path" in kwargs and kwargs["config_path"] is not None:
            self.config = json.load(open(kwargs["config_path"], encoding="utf8"))

        self.db = self.ord_tech.getDB()
        self.tech = self.db.getTech()
        self.chip = self.db.getChip()
        self.layers = {l.getName(): l for l in self.tech.getLayers()}
        self.libs = self.db.getLibs()
        self.cells = {}
        for lib in self.libs:
            self.cells.update({m.getName(): m for m in lib.getMasters()})
        if self.chip is not None:
            self.block = self.db.getChip().getBlock()
            self.name = self.block.getName()
            self.rows = self.block.getRows()
            self.dbunits = self.block.getDefUnits()
            self.instances = self.block.getInsts()

    def add_lef(self, new_lef):
        odb.read_lef(self.db, new_lef)

    def _dpl(self):
        """
        The ``._dpl()`` method is EXPERIMENTAL and SHOULD NOT BE USED YET.

        Use a composite step with ``OpenROAD.DetailedPlacement``.
        """
        if self.config is None:
            raise RuntimeError("Attempted to call dpl without config file")

        cell_pad_value = int(self.config["DPL_CELL_PADDING"])
        cell_pad_side = cell_pad_value // 2
        dpl = self.design.getOpendp()
        dpl.setPaddingGlobal(cell_pad_side, cell_pad_side)
        if wildcards := self.config["CELL_PAD_EXCLUDE"]:
            for wildcard in wildcards:
                masters = [
                    self.cells[name] for name in self.cells if fnmatch(name, wildcard)
                ]
                for master in masters:
                    dpl.setPadding(master, 0, 0)
        if diode_padding := self.config["DIODE_PADDING"]:
            name, _ = self.config["DIODE_CELL"].split("/")
            master = self.cells[name]
            dpl.setPadding(master, int(diode_padding), 0)

        dpl.detailedPlacement(
            self.config["PL_MAX_DISPLACEMENT_X"],
            self.config["PL_MAX_DISPLACEMENT_Y"],
        )
        dpl.reportLegalizationStats()
        dpl.optimizeMirroring()

    def _grt(self):
        """
        The ``._grt()`` method is EXPERIMENTAL and SHOULD NOT BE USED YET.

        Use a composite step with ``OpenROAD.GlobalRouting``.
        """
        if self.config is None:
            raise RuntimeError("Attempted to call grt without config file")

        grt = self.design.getGlobalRouter()
        routing_layers = [l for l in self.layers.values() if l.getRoutingLevel() >= 1]
        for layer, adj in zip(routing_layers, self.config["GRT_LAYER_ADJUSTMENTS"]):
            grt.addLayerAdjustment(
                layer.getRoutingLevel(),
                float(adj),
            )

        min_layer_name = self.config["RT_MIN_LAYER"]
        if not min_layer_name in self.layers:
            raise RuntimeError(f"Unknown layer name '{min_layer_name}'")
        min_layer_idx = self.layers[min_layer_name].getRoutingLevel()

        max_layer_name = self.config["RT_MAX_LAYER"]
        if not max_layer_name in self.layers:
            raise RuntimeError(f"Unknown layer name '{max_layer_name}'")
        max_layer_idx = self.layers[max_layer_name].getRoutingLevel()

        min_clk_idx = min_layer_idx
        if min_clk_name := self.config["RT_CLOCK_MIN_LAYER"]:
            if not min_clk_name in self.layers:
                raise RuntimeError(f"Unknown layer name '{min_clk_name}'")
            min_clk_idx = self.layers[min_clk_name].getRoutingLevel()

        max_clk_idx = max_layer_idx
        if max_clk_name := self.config["RT_CLOCK_MAX_LAYER"]:
            if not max_clk_name in self.layers:
                raise RuntimeError(f"Unknown layer name '{max_clk_name}'")
            max_clk_idx = self.layers[max_clk_name].getRoutingLevel()

        grt.setMinRoutingLayer(min_layer_idx)
        grt.setMaxRoutingLayer(max_layer_idx)
        grt.setMinLayerForClock(min_clk_idx)
        grt.setMaxLayerForClock(max_clk_idx)
        grt.setMacroExtension(self.config["GRT_MACRO_EXTENSION"])
        grt.setOverflowIterations(self.config["GRT_OVERFLOW_ITERS"])
        grt.setAllowCongestion(self.config["GRT_ALLOW_CONGESTION"])
        grt.setVerbose(True)
        grt.globalRoute(
            True
        )  # The first variable updates guides- not sure why the default is False


def click_odb(function):
    @functools.wraps(function)
    def wrapper(input_db, input_lefs, config_path, **kwargs):
        reader = OdbReader(input_db, config_path=config_path)

        signature = inspect.signature(function)
        parameter_keys = signature.parameters.keys()

        kwargs = kwargs.copy()
        kwargs["reader"] = reader

        outputs = []
        for key, value in kwargs.items():
            if key.startswith("output_"):
                id = key[7:]
                outputs.append((id, value))

        kwargs = {k: kwargs[k] for k in kwargs.keys() if not k.startswith("output_")}

        if "input_db" in parameter_keys:
            kwargs["input_db"] = input_db
        if "input_lefs" in parameter_keys:
            kwargs["input_lefs"] = input_lefs

        if input_db.endswith(".def"):
            print(
                "Error: Invocation was not updated to use an odb file.", file=sys.stderr
            )
            exit(1)

        function(**kwargs)

        for format, path in outputs:
            fn = write_fn[format]
            fn(reader, path)

    for format in write_fn:
        wrapper = click.option(
            f"--output-{format}",
            default=None,
            help=f"Write {format} view",
        )(wrapper)

    wrapper = click.option(
        "-l",
        "--input-lef",
        "input_lefs",
        default=(),
        help="LEF file needed to have a proper view of the DEF files",
        multiple=True,
    )(wrapper)
    wrapper = click.option(
        "--step-config",
        "config_path",
        type=click.Path(exists=True, dir_okay=False, file_okay=True, readable=True),
        required=False,
    )(wrapper)
    wrapper = click.argument("input_db")(wrapper)

    return wrapper
