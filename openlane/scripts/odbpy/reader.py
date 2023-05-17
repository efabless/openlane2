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

import os
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

if python_path := os.environ.get("ODB_PYTHONPATH", None):
    sys.path = python_path.split(":") + sys.path

sys.path.insert(0, os.path.dirname(os.environ["OPENLANE_ROOT"]))
# -- END

import click
import rich
from rich.table import Table
from openlane.state.design_format import DesignFormat, DesignFormatObject

click  # Re-export now that the environment actually works properly

write_fn: Dict[DesignFormat, Callable] = {
    DesignFormat.DEF: lambda reader, file: odb.write_def(reader.block, file),
    DesignFormat.ODB: lambda reader, file: odb.write_db(reader.db, file),
}


class OdbReader(object):
    def __init__(self, *args):
        self.db = odb.dbDatabase.create()
        if len(args) == 1:
            db_in = args[0]
            self.db = odb.read_db(self.db, db_in)
        elif len(args) == 2:
            lef_in, def_in = args
            if not (isinstance(lef_in, list) or isinstance(lef_in, tuple)):
                lef_in = [lef_in]
            for lef in lef_in:
                odb.read_lef(self.db, lef)
            if def_in is not None:
                odb.read_def(self.db, def_in)

        self.tech = self.db.getTech()
        self.chip = self.db.getChip()
        if self.chip is not None:
            self.block = self.db.getChip().getBlock()
            self.name = self.block.getName()
            self.rows = self.block.getRows()
            self.dbunits = self.block.getDefUnits()
            self.instances = self.block.getInsts()

    def add_lef(self, new_lef):
        odb.read_lef(self.db, new_lef)


def click_odb(function):
    @functools.wraps(function)
    def wrapper(input_db, input_lefs, **kwargs):
        reader = OdbReader(input_db)

        signature = inspect.signature(function)
        parameter_keys = signature.parameters.keys()

        kwargs = kwargs.copy()
        kwargs["reader"] = reader

        outputs = []
        for key, value in kwargs.items():
            if key.startswith("output_"):
                id = key[7:]
                outputs.append((DesignFormat.by_id(id), value))

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

    for format in DesignFormat:
        if write_fn.get(format) is None:
            continue
        # For type-checker: all guaranteed to be DesignFormatObjects
        assert isinstance(format.value, DesignFormatObject)
        wrapper = click.option(
            f"--output-{format.value.id}",
            default=None,
            help=f"Write {format.value.name}",
        )(wrapper)

    wrapper = click.option(
        "-l",
        "--input-lef",
        "input_lefs",
        default=(),
        help="LEF file needed to have a proper view of the DEF files",
        multiple=True,
    )(wrapper)
    wrapper = click.argument("input_db")(wrapper)

    return wrapper
