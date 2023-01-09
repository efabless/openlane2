import os

import click
import volare

from .flow import Prototype
from .config import Config, Keys, env_from_tcl


@click.command()
#@click.option("--verbose", type=click.choice('BASIC', 'INFO', 'DEBUG', 'SILLY'), default="INFO", )
@click.option("--pdk-root", default=None, help="Volare PDK root folder")
@click.argument("config_file")
def cli(pdk_root, config_file):

    design_dir = os.path.dirname(config_file)
    config_str = open(config_file).read()
    process_info = Config.from_json(
        config_str,
        only_extract_process_info=True,
        design_dir=design_dir,
    )

    pdk_root = volare.get_volare_home(pdk_root)

    pdk = process_info.get(Keys.pdk) or "sky130A"

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

    design_config = Config.from_json(
        config_str,
        pdk=pdk,
        pdkpath=pdkpath,
        scl=scl,
        sclpath=sclpath,
        design_dir=design_dir,
    )

    config_in.update(design_config)

    flow = Prototype(config_in)
    flow.run(design_dir)


if __name__ == "__main__":
    cli()
