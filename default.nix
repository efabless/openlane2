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
  lib,
  system,
  clangStdenv,
  fetchFromGitHub,
  nix-gitignore,
  # Tools
  klayout,
  klayout-pymod,
  libparse,
  magic-vlsi,
  netgen,
  opensta,
  openroad,
  ruby,
  surelog,
  tclFull,
  verilator,
  verilog,
  volare,
  yosys,
  yosys-synlig-sv,
  yosys-lighter,
  yosys-sby,
  yosys-eqy,
  yosys-ghdl,
  yosys-f4pga-sdc,
  # Python
  buildPythonPackage,
  click,
  cloup,
  pyyaml,
  rich,
  requests,
  pcpp,
  tkinter,
  lxml,
  deprecated,
  psutil,
  pytestCheckHook,
  pytest-xdist,
  pyfakefs,
  rapidfuzz,
  ioplace-parser,
  poetry-core,
}: let
  self = buildPythonPackage {
    pname = "openlane";
    version = (builtins.fromTOML (builtins.readFile ./pyproject.toml)).tool.poetry.version;
    format = "pyproject";

    src = nix-gitignore.gitignoreSourcePure ./.gitignore ./.;

    nativeBuildInputs = [
      poetry-core
    ];

    includedTools = [
      (yosys.withPlugins ([
          yosys-sby
          yosys-eqy
          yosys-lighter
          yosys-synlig-sv
          yosys-f4pga-sdc
        ]
        ++ lib.optionals (system == "x86_64-linux") [yosys-ghdl]))
      opensta
      openroad
      klayout
      netgen
      magic-vlsi
      verilog
      verilator
      tclFull
      surelog
    ];

    propagatedBuildInputs =
      [
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
        libparse
        psutil
        klayout-pymod
        rapidfuzz
        ioplace-parser

        # Ruby
        ruby
      ]
      ++ self.includedTools;

    doCheck = true;
    checkInputs = [pytestCheckHook pytest-xdist pyfakefs];

    computed_PATH = lib.makeBinPath self.propagatedBuildInputs;

    # Make PATH available to OpenLane subprocesses
    makeWrapperArgs = [
      "--prefix PATH : ${self.computed_PATH}"
    ];

    meta = with lib; {
      description = "Hardware design and implementation infrastructure library and ASIC flow";
      homepage = "https://efabless.com/openlane";
      mainProgram = "openlane";
      license = licenses.asl20;
      platforms = platforms.linux ++ platforms.darwin;
    };
  };
in
  self
