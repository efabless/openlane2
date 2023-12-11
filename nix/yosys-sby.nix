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
  pkgs ? import ./pkgs.nix {},
  yosys ? import ./yosys.nix { inherit pkgs; },
}:

with pkgs; clangStdenv.mkDerivation rec {
  name = "yosys-sby";
  dylibs = [];

  src = fetchFromGitHub {
    owner = "yosyshq";
    repo = "sby";
    rev = "7415abfcfa8bf14f024f28e61e62f23ccd892415";
    sha256 = "sha256-+h+Ddv0FYgovu4ee5e6gA+IiD2wThtzFxOMiGkG99g8=";
  };

  makeFlags = [
    "YOSYS_CONFIG=${yosys}/bin/yosys-config"
  ];

  buildInputs = [
    yosys.py3
    yosys
    libedit
    libbsd
    zlib

    # solvers
    boolector
    z3
    yices
  ];

  preConfigure = ''
  sed -i.bak "s@/usr/local@$out@" Makefile
  sed -i.bak "s@#!/usr/bin/env python3@#!${yosys.py3}/bin/python3@" sbysrc/sby.py
  sed -i.bak "s@\"/usr/bin/env\", @@" sbysrc/sby_core.py
  '';

  checkPhase = ''
  make test
  '';

  doCheck = false;

  computed_PATH = lib.makeBinPath buildInputs;
  makeWrapperArgs = [
    "--prefix PATH : ${computed_PATH}"
  ];
}