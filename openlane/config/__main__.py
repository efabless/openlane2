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
import click
import json

from .config import Config
from ..flows.flow import universal_flow_config_variables
from ..steps.yosys import verilog_rtl_cfg_vars
from ..flows.cli import cloup_flow_opts


@click.group
def cli():
    pass


@click.argument(
    "file_name",
    type=click.Path(exists=False, file_okay=True, dir_okay=False),
)
@click.command()
@cloup_flow_opts(
    config_options=False,
    run_options=False,
    sequential_flow_controls=False,
    jobs=False,
    accept_config_files=False,
)
def create_config(file_name, pdk_root, pdk, scl):
    """
    Generate a JSON config interactively
    """

    design_dir = input("Enter your design directory: ")
    design_name = input("Enter the name of your top level name (design name): ")
    clock_port = input("Enter the name of the design's clock port: ")
    clock_period = input("Enter your desired clock period in nanoseconds(ns): ")
    verilog_files = ",".split(
        input(
            "Enter your design's RTL source files (put a comma between each entry): # Tip use dir:: to reference your design directory\n"
        )
    )
    config_dict = {
        "DESIGN_NAME": design_name,
        "CLOCK_PORT": clock_port,
        "CLOCK_PERIOD": clock_period,
        "VERILOG_FILES": verilog_files,
        "meta": {
            "version": 1,
        },
    }
    config, _ = Config.load(
        config_dict,
        universal_flow_config_variables + verilog_rtl_cfg_vars,
        design_dir=design_dir,
        pdk=pdk,
        pdk_root=pdk_root,
        scl=scl,
    )
    config_parsed = {
        key: value
        for key, value in config.to_raw_dict(include_meta=False).items()
        if key in config_dict.keys()
    }
    print(
        json.dumps(config_parsed, cls=config.get_encoder(), indent=4),
        file=open(file_name, "w"),
    )


cli.add_command(create_config)

if __name__ == "__main__":
    cli()
