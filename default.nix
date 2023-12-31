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
  system ? builtins.currentSystem,
  pkgs ? import ./nix/pkgs.nix {},


  klayout ? import ./nix/klayout.nix { inherit pkgs; },
  klayout-pymod ? import ./nix/klayout-pymod.nix { inherit pkgs; inherit klayout; },
  libparse ? import ./nix/libparse.nix { inherit pkgs; },
  ioplace-parser ? import ./nix/ioplace-parser.nix { inherit pkgs; },
  magic ? import ./nix/magic.nix { inherit pkgs; },
  netgen ? import ./nix/netgen.nix { inherit pkgs; },
  opensta ? import ./nix/opensta.nix { inherit pkgs; },
  openroad ? import ./nix/openroad.nix {
    inherit pkgs;
    inherit opensta;
  },
  surelog ? import ./nix/surelog.nix { inherit pkgs; },
  verilator ? import ./nix/verilator.nix { inherit pkgs; },
  volare ? import ./nix/volare.nix { inherit pkgs; },
  yosys ? import ./nix/yosys.nix { inherit pkgs; },

  synlig-sv ? import ./nix/yosys-synlig-sv.nix { inherit pkgs; inherit yosys; inherit surelog; },
  lighter ? import ./nix/yosys-lighter.nix { inherit pkgs; inherit yosys; },
  sby ? import ./nix/yosys-sby.nix { inherit pkgs; inherit yosys; },
  eqy ? import ./nix/yosys-eqy.nix { inherit pkgs; inherit yosys; inherit sby; },
  ys-ghdl ? import ./nix/yosys-ghdl.nix { inherit pkgs; inherit yosys; inherit sby; },

  ...
}:

with pkgs; with python3.pkgs; buildPythonPackage rec {
  name = "openlane";

  version_file = builtins.readFile ./openlane/__version__.py;
  version_list = builtins.match ''.+''\n__version__ = "([^"]+)"''\n.+''$'' version_file;
  version = builtins.head version_list;

  src = [
    ./Readme.md
    ./setup.py
    (nix-gitignore.gitignoreSourcePure "__pycache__\nruns/\n" ./openlane)
    ./type_stubs
    ./requirements.txt
  ];

  unpackPhase = ''
    echo $src
    for file in $src; do
      BASENAME=$(python3 -c "import os; print('$file'.split('-', maxsplit=1)[1], end='$EMPTY')")
      cp -r $file $PWD/$BASENAME
    done
    ls -lah
  '';

  buildInputs = [];

  includedTools = [
    (yosys.withPlugins([
      sby
      eqy
      lighter
      synlig-sv
    ] ++ (if system == "x86_64-linux" then [ys-ghdl] else []) ))
    opensta
    openroad
    klayout
    netgen
    magic
    verilog
    verilator
    tcl
    surelog
  ];

  propagatedBuildInputs = [
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
    ioplace-parser
    psutil
    klayout-pymod
  ] ++ includedTools;

  doCheck = false;
  checkInputs = [ pytestCheckHook pyfakefs ];

  computed_PATH = lib.makeBinPath (propagatedBuildInputs);
  
  # Make PATH available to OpenLane subprocesses
  makeWrapperArgs = [
    "--prefix PATH : ${computed_PATH}"
  ];
}
