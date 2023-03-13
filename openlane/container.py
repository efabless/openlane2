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
import pathlib
import getpass
import requests
import subprocess
from typing import List, Sequence, Set, Optional

from .logging import err, info, print, warn
from .env_info import ContainerInfo, OSInfo


def permission_args(cinfo: ContainerInfo) -> List[str]:
    if cinfo.engine != "docker":
        return []

    if cinfo.rootless:
        return []

    uid = (
        subprocess.check_output(["id", "-u", getpass.getuser()]).decode("utf8").strip()
    )
    gid = (
        subprocess.check_output(["id", "-g", getpass.getuser()]).decode("utf8").strip()
    )

    return ["--user", f"{uid}:{gid}"]


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
        subprocess.check_output(["docker", "images", image])
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
        subprocess.check_call(["docker", "pull", image])
    except subprocess.CalledProcessError:
        err(f"Failed to pull image {image} from the container registries.")
        return False

    return True


docker_ids: Set[str] = set()


def run_in_container(
    image: str,
    args: Sequence[str],
    pdk_root: Optional[str],
    pdk: Optional[str],
    scl: Optional[str],
    other_mounts: Optional[Sequence[str]],
):
    # If imported at the top level, would interfere with Conda where Volare
    # would not be installed.
    import volare

    global docker_ids

    osinfo = OSInfo.get()
    if not osinfo.supported:
        raise SystemError(f"Unsupported operating system '{osinfo.kernel}'.")

    cinfo = osinfo.container_info

    if cinfo is None:
        raise FileNotFoundError("No compatible container engine found.")

    if not ensure_image(image):
        raise ValueError(f"Failed to use image '{image}'.")

    mount_args = []
    home = os.path.abspath(pathlib.Path.home())

    mount_args += ["-v", f"{home}:{home}"]

    pdk_root = volare.get_volare_home(pdk_root)
    mount_args += [
        "-v",
        f"{pdk_root}:{pdk_root}",
        "-e",
        f"PDK_ROOT={pdk_root}",
    ]

    if pdk is not None:
        mount_args += ["-e", f"PDK={pdk}"]

    if scl is not None:
        mount_args += [
            "-e",
            f"STD_CELL_LIBRARY={scl}",
        ]

    cwd = os.path.abspath(os.getcwd())
    if not cwd.startswith(home):
        mount_args += ["-v", f"{cwd}:{cwd}"]

    if other_mounts is not None:
        for mount in other_mounts:
            mount_args += ["-v", f"{mount}:{mount}"]

    mount_args += ["-w", cwd]

    cmd = (
        [
            "docker",
            "run",
            "--rm",
            "-ti",
        ]
        + permission_args(cinfo)
        + mount_args
        + gui_args(osinfo)
        + [image]
        + list(args)
    )

    cmd_escaped = []
    for el in cmd:
        if " " in cmd:
            cmd_escaped.append(f"'{cmd}'")
        else:
            cmd_escaped.append(el)

    info("Running containerized command:")
    print(" ".join(cmd_escaped))
    subprocess.check_call(
        cmd,
        stderr=subprocess.STDOUT,
    )
