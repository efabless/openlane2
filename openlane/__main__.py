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
from typing import Type

import click

from .flows import Flow, SequentialFlow
from .config import ConfigBuilder, InvalidConfig
from .common import err, warn, log


@click.command()
# @click.option("--verbose", type=click.choice('BASIC', 'INFO', 'DEBUG', 'SILLY'), default="INFO", )
@click.option(
    "-p",
    "--pdk",
    type=str,
    default="sky130A",
    help="The process design kit to use. [default: sky130A]",
)
@click.option(
    "-s",
    "--scl",
    type=str,
    default=None,
    help="The standard cell library to use. [default: varies by PDK]",
)
@click.option(
    "-f",
    "--flow",
    "flow_name",
    type=click.Choice(Flow.factory.list(), case_sensitive=False),
    default=None,
    help="The built-in OpenLane flow to use",
)
@click.option("--pdk-root", default=None, help="Override volare PDK root folder")
@click.argument("config_file")
def cli(flow_name: str, pdk_root, pdk, scl, config_file):

    try:
        config_in, design_dir = ConfigBuilder.load(
            config_file,
            pdk_root=pdk_root,
            pdk=pdk,
            scl=scl,
        )
    except InvalidConfig as e:
        log(f"[green]Errors have occurred while loading the {e.config}:")
        for error in e.errors:
            err(error)
        if len(e.warnings) > 0:
            log("The following warnings have also been generated:")
            for warning in e.warnings:
                warn(warning)
        log("OpenLane will now quit. Please check your configuration.")
        exit(-1)

    flow_description = flow_name or config_in.meta.flow

    TargetFlow: Type[Flow]

    if not isinstance(flow_description, str):
        TargetFlow = SequentialFlow.make(flow_description)
    else:
        if FlowClass := Flow.factory.get(flow_description):
            TargetFlow = FlowClass
        else:
            err(
                f"Unknown flow '{flow_description}' specified in configuration's 'meta' object."
            )
            exit(-1)

    flow = TargetFlow(config_in, design_dir)
    flow.start()


if __name__ == "__main__":
    cli()
