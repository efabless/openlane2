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
  pkgs ? import ./nix/pkgs.nix,

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

  or-abc-rev ? "95b3543e928640dfa25f9e882e72a090a8883a9c",
  or-abc-sha256 ? "sha256-U1E9wvEK5G4zo5Pepvsb5q885qSYyixIViweLacO5+U=",
  or-abc ? import ./nix/or-abc.nix {
    inherit pkgs;
    rev = or-abc-rev;
    sha256 = or-abc-sha256;
  },

  openroad-rev ? "2f330b3bf473a81f751d6388e1c26e6aa831a9c4",
  openroad-sha256 ? "sha256-UhVyK4k+bAxUSf+OnHZMEqXcxGYk9tXZKf+A2zTGFHE=",
  openroad ? pkgs.libsForQt5.callPackage ./nix/openroad.nix {
    inherit pkgs;
    rev = openroad-rev;
    sha256 = openroad-sha256;
    abc-derivation = or-abc;
  },
  
  volare-rev ? "852e565f30f3445c6fa59f15cea85c461e3bdddd",
  volare-sha256 ? "sha256-U8pyGJjEYlSU2oaofZIaUUNbkn9uHv5LQ5074ZUqZjA=",
  volare ? let src = pkgs.fetchFromGitHub {
    owner = "efabless";
    repo = "volare";
    rev = volare-rev;
    sha256 = volare-sha256;
  }; in import "${src}" {
    inherit pkgs;
  },

  klayout-rev ? "8bed8bcc3ca19f7e1a810815541977fd16bc1db5",
  klayout-sha256 ? "sha256-w3ag+TPUrjPbPIy6N4HPsfraOyoHqBbvjwB1M6+qh60=",
  klayout ? import ./nix/klayout.nix {
    inherit pkgs;
    rev = klayout-rev;
    sha256 = klayout-sha256;
  },

  yosys-abc-rev ? "a8f0ef2368aa56b3ad20a52298a02e63b2a93e2d",
  yosys-abc-sha256 ? "sha256-48i6AKQhMG5hcnkS0vejOy1PqFbeb6FpU7Yx0rEvHDI=",
  yosys-rev ? "7e588664e7efa36ff473f0497feacaad57f5e90c",
  yosys-sha256 ? "sha256-0xV+323YTK+VhnD05SmvGv8uT4TzqA9IZ/iKl1as1Kc=",
  yosys ? import ./nix/yosys.nix {
    inherit pkgs;
    rev = yosys-rev;
    sha256 = yosys-sha256;
    abc-rev = yosys-abc-rev;
    abc-sha256 = yosys-abc-sha256;
  },

  
  ...
}:

with pkgs; with python3.pkgs; buildPythonPackage rec {
  pname = "openlane";
  name = pname;

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
  
  doCheck = false;
  propagatedBuildInputs = [
    # Tools
    openroad
    klayout
    yosys
    netgen
    python3
    ruby
    tcl

    # Python
    click
    pyyaml
    rich
    requests
    pcpp
    volare
    tkinter
  ] ++ (lib.optionals stdenv.isLinux [ magic ]);
}