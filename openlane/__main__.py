import os
from typing import Optional

import click
import volare

from .flow import Prototype
from .config import Config, Keys, env_from_tcl, validate_pdk_config
from .common import error, warn, log


def run_default_flow(pdk_root: str, pdk: str, scl: str, config_file: str):
    design_dir = os.path.dirname(config_file)
    config_str = open(config_file).read()

    process_info = Config.from_json(
        config_str,
        only_extract_process_info=True,
        design_dir=design_dir,
    )
    pdk_root = volare.get_volare_home(pdk_root)
    pdk = process_info.get(Keys.pdk) or pdk
    config_in = Config(
        {
            "PDK_ROOT": pdk_root,
            Keys.pdk: pdk,
        }
    )

    pdkpath = os.path.join(pdk_root, pdk)
    pdk_config_path = os.path.join(pdkpath, "libs.tech", "openlane", "config.tcl")
    config_in = env_from_tcl(config_in, pdk_config_path)

    scl = config_in["STD_CELL_LIBRARY"]
    sclpath = os.path.join(pdkpath, "libs.ref", scl)
    scl_config_path = os.path.join(pdkpath, "libs.tech", "openlane", scl, "config.tcl")
    config_in = env_from_tcl(config_in, scl_config_path)

    config_in, warnings, errors = validate_pdk_config(
        config_in, ["PDK_ROOT", "PDK", "STD_CELL_LIBRARY"]
    )
    if len(warnings) > 0:
        log("Loading the PDK configuration has generated the following warnings:")
    for warning in warnings:
        warn(warning)

    if len(errors) > 0:
        error(
            "The following errors were encountered while loading the PDK configuration files:"
        )
    for err in errors:
        error(err)
    if len(errors) > 0:
        log("OpenLane will now quit.")
        exit(-1)

    design_config = Config.from_json(
        config_str,
        pdk=pdk,
        pdkpath=pdkpath,
        scl=scl,
        sclpath=sclpath,
        design_dir=design_dir,
    )

    config_in.update(design_config)

    flow = Prototype(config_in, design_dir)
    flow.run()


@click.command()
# @click.option("--verbose", type=click.choice('BASIC', 'INFO', 'DEBUG', 'SILLY'), default="INFO", )
@click.option(
    "--pdk",
    type=str,
    default="sky130A",
    help="The process design kit to use. [default: sky130A]",
)
@click.option(
    "--scl",
    type=str,
    default=None,
    help="The standard cell library to use. [default: varies by PDK]",
)
@click.option("--pdk-root", default=None, help="Override volare PDK root folder")
@click.argument("config_file")
def cli(pdk_root, pdk, scl, config_file):
    run_default_flow(pdk_root, pdk, scl, config_file)


if __name__ == "__main__":
    cli()
