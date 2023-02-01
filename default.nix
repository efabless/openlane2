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
{
  pkgs ? import ./nix/pkgs.nix {},
  python-pname ? "python38Full",
  mach-nix ? import ./nix/mach.nix {
    inherit pkgs;
    inherit python-pname;
  },

  magic-rev ? "8d08cb2f2f33c79bea478a79543721d476554c78",
  magic-sha256 ? "sha256-V+3XduqeUVjaua8JIhln0imLFs4og9ibeUOh0N5aXa0=",
  magic ? import ./nix/magic.nix {
    inherit pkgs;
    rev = magic-rev;
    sha256 = magic-sha256;
  },

  netgen-rev ? "c10f8efd7dc1a5a1c1330784765d5a38cc22cd2d",
  netgen-sha256 ? "sha256-WGWnIWL//q7z5HmJ1JpSK6QhNM+X7iWNcDzQpL5CbYc=",
  netgen ? import ./nix/netgen.nix {
    inherit pkgs;
    rev = netgen-rev;
    sha256 = netgen-sha256;
  },

  openroad-rev ? "c295b08a99aacb6147b9c51104627e78ac3859e3",
  openroad-sha256 ? "sha256-HwnGuUPxUbRRq1my/5B5hGWtSrCWPVblkdvychnk/HM=",
  openroad ? import ./nix/openroad.nix {
    inherit pkgs;
    inherit python-pname;
    
    rev = openroad-rev;
    sha256 = openroad-sha256;
  },
  
  ol-python ? (import ./nix/ol-python.nix {
    inherit pkgs;
    inherit mach-nix;
  }).withPackages (p: with p; [volare]),
}:

nix.buildPythonPackage rec {
  pname = "openlane-app";
  name = "openlane-app";

  python = python-pname;

  version_file = builtins.readFile ./openlane/__version__.py;
  version_list = builtins.match ''^__version__ = "([^"]+)"''\n''$'' version_file;
  version = builtins.head version_list;

  src = builtins.filterSource (path: type:
    (builtins.match ''${builtins.toString ./.}/(openlane(/.+)?|setup.py|requirements(_dev)?.txt|Readme.md)'' path) != null &&
    (builtins.match ''.+__pycache__.*'' path == null)
  ) ./.;

  requirements = 
    builtins.readFile ./requirements_dev.txt +
    builtins.readFile ./requirements.txt
    ;

  propagatedBuildInputs = [
    # Tools
    openroad
    klayout
    yosys
    magic
    netgen
  ];
}