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
import shlex
import pathlib
import getpass
import tempfile
import requests
import subprocess
from typing import List, Sequence, Optional, Union, Tuple

from .logging import err, info, print, warn
from .env_info import OSInfo

CONTAINER_ENGINE = os.getenv("OPENLANE_CONTAINER_ENGINE", "docker")


def permission_args(osinfo: OSInfo) -> List[str]:
    if (
        osinfo.kernel == "Linux"
        and osinfo.container_info is not None
        and osinfo.container_info.engine == "docker"
        and not osinfo.container_info.rootless
    ):
        uid = (
            subprocess.check_output(["id", "-u", getpass.getuser()])
            .decode("utf8")
            .strip()
        )
        gid = (
            subprocess.check_output(["id", "-g", getpass.getuser()])
            .decode("utf8")
            .strip()
        )

        return ["--user", f"{uid}:{gid}"]

    return []


def gui_args(osinfo: OSInfo) -> List[str]:
    args = []
    if osinfo.kernel == "Linux":
        if os.environ.get("DISPLAY") is None:
            warn(
                "DISPLAY environment variable not set. GUI features will not be available."
            )
        else:
            args += [
                "-e",
                f"DISPLAY={os.environ.get('DISPLAY')}",
                "-v",
                "/tmp/.X11-unix:/tmp/.X11-unix",
                "-v",
                f"{os.path.expanduser('~')}/.Xauthority:/.Xauthority",
                "--network",
                "host",
                "--security-opt",
                "seccomp=unconfined",
            ]
    return args


def image_exists(image: str) -> bool:
    images = (
        subprocess.check_output([CONTAINER_ENGINE, "images", image])
        .decode("utf8")
        .rstrip()
        .split("\n")[1:]
    )
    return len(images) >= 1


def remote_manifest_exists(image: str) -> bool:
    registry = "docker.io"
    image_elements = image.split("/", maxsplit=1)
    if len(image_elements) > 1:
        registry = image_elements[0]
        image = image_elements[1]
    elements = image.split(":")
    repo = elements[0]
    tag = "latest"
    if len(elements) > 1:
        tag = elements[1]

    url = None
    if registry == "docker.io":
        url = f"https://registry.hub.docker.com/v2/repositories/{repo}/tags/{tag}"
    elif registry == "ghcr.io":
        url = f"https://ghcr.io/v2/{repo}/manifests/{tag}"
        print(url)
    else:
        err(f"Unknown registry '{registry}'.")
        return False

    try:
        request = requests.get(url, headers={"Accept": "application/json"})
        request.raise_for_status()
    except requests.exceptions.ConnectionError:
        err("Couldn't connect to the internet to pull container images.")
        return False
    except requests.exceptions.HTTPError:
        err(
            f"The image {image} was not found. This may be because the CI for this image is running- in which case, please try again later."
        )
        return False
    return True


def ensure_image(image: str) -> bool:
    if image_exists(image):
        return True

    try:
        subprocess.check_call([CONTAINER_ENGINE, "pull", image])
    except subprocess.CalledProcessError:
        err(f"Failed to pull image {image} from the container registries.")
        return False

    return True


win_path_sep = re.compile(r"\\")


def sanitize_path(path: Union[str, os.PathLike]) -> Tuple[str, str]:
    path_str = str(path)
    abspath = os.path.abspath(path_str)
    mountable_path = abspath
    if os.path.sep == "\\":
        mountable_path = win_path_sep.sub("/", abspath)[2:]
    return (abspath, mountable_path)


def run_in_container(
    image: str,
    args: Sequence[str],
    pdk_root: Optional[str] = None,
    pdk: Optional[str] = None,
    scl: Optional[str] = None,
    other_mounts: Optional[Sequence[str]] = None,
    interactive: bool = False,
) -> int:
    # If imported at the top level, would interfere with Conda where Volare
    # would not be installed.
    import volare

    osinfo = OSInfo.get()
    if not osinfo.supported:
        warn(
            f"Unsupported host operating system '{osinfo.kernel}'. You may encounter unexpected issues."
        )

    if osinfo.container_info is None:
        raise FileNotFoundError("No compatible container engine found.")

    if not ensure_image(image):
        raise ValueError(f"Failed to use image '{image}'.")

    mount_args = []
    from_home, to_home = sanitize_path(pathlib.Path.home())

    mount_args += ["-v", f"{from_home}:{to_home}"]

    from_pdk, to_pdk = sanitize_path(volare.get_volare_home(pdk_root))
    mount_args += [
        "-v",
        f"{from_pdk}:{to_pdk}",
        "-e",
        f"PDK_ROOT={to_pdk}",
    ]

    if pdk is not None:
        mount_args += ["-e", f"PDK={pdk}"]

    if scl is not None:
        mount_args += [
            "-e",
            f"STD_CELL_LIBRARY={scl}",
        ]

    from_cwd, to_cwd = sanitize_path(os.getcwd())
    if not from_cwd.startswith(from_home):
        mount_args += ["-v", f"{from_cwd}:{to_cwd}"]
    mount_args += ["-w", to_cwd]

    tempdir = tempfile.mkdtemp("openlane_docker")

    mount_args += [
        "-v",
        f"{tempdir}:/tmp",
        "-e",
        "TMPDIR=/tmp",
    ]

    if other_mounts is not None:
        for mount in other_mounts:
            mount_from, mount_to = sanitize_path(mount)
            mount_args += ["-v", f"{mount_from}:{mount_to}"]

    cmd = (
        [
            CONTAINER_ENGINE,
            "run",
            "--rm",
            "-ti" if interactive else "-t",
        ]
        + permission_args(osinfo)
        + mount_args
        + gui_args(osinfo)
        + [image]
        + list(args)
    )

    info("Running containerized command:")
    print(shlex.join(cmd))

    result = subprocess.call(
        cmd,
        stderr=subprocess.STDOUT,
    )

    return result
