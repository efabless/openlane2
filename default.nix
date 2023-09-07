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
  gitignore-src ? import ./nix/gitignore.nix { inherit pkgs; },
  

  klayout ? pkgs.libsForQt5.callPackage ./nix/klayout.nix {
    inherit pkgs;
  },
  libparse ? import ./nix/libparse.nix { inherit pkgs; },
  magic ? import ./nix/magic.nix { inherit pkgs; },
  netgen ? import ./nix/netgen.nix { inherit pkgs; },
  openroad ? pkgs.libsForQt5.callPackage ./nix/openroad.nix {
    inherit pkgs;
  },
  verilator ? import ./nix/verilator.nix { inherit pkgs; },
  volare ? import ./nix/volare.nix { inherit pkgs; },
  yosys ? import ./nix/yosys.nix { inherit pkgs; },
  
  ...
}:

with pkgs; with python3.pkgs; buildPythonPackage rec {
  name = "openlane";

  version_file = builtins.readFile ./openlane/__version__.py;
  version_list = builtins.match ''.+''\n__version__ = "([^"]+)"''\n.+''$'' version_file;
  version = builtins.head version_list;

  src = gitignore-src.gitignoreSource ./.;
  
  doCheck = false;

  propagatedBuildInputs = [
    # Tools
    openroad
    klayout
    python3
    netgen
    yosys
    magic
    verilator
    ruby
    tcl

    # Python
    click
    cloup
    pyyaml
    rich
    requests
    pcpp
    volare
    tkinter
    lxml
    deprecated
    immutabledict
    libparse
  ];

  computed_PATH = lib.makeBinPath propagatedBuildInputs;
  computed_PYTHONPATH = lib.makeSearchPath "lib/${python3.libPrefix}/site-packages" propagatedBuildInputs;

  # Make PATH/PYTHONPATH available to OpenLane subprocesses
  makeWrapperArgs = [
    "--prefix PATH : ${computed_PATH}"
    "--prefix PYTHONPATH : ${computed_PYTHONPATH}"  
  ];
}
