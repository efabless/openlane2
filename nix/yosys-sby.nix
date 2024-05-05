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
  yosys,
  fetchFromGitHub,
  libedit,
  libbsd,
  zlib,
  boolector,
  z3,
  yices,
}:
yosys.stdenv.mkDerivation rec {
  name = "yosys-sby";
  dylibs = [];

  src = fetchFromGitHub {
    owner = "yosyshq";
    repo = "sby";
    rev = "7dd287f287a4e6ed5ea37026df90276b360482b8";
    sha256 = "sha256-B5CpS3fXdRv7hDjpNsT1k/287ZLM6dIVCPkf0Cfbb+Y=";
  };

  makeFlags = [
    "YOSYS_CONFIG=${yosys}/bin/yosys-config"
  ];

  buildInputs = [
    yosys.py3env
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
    sed -i.bak "s@#!/usr/bin/env python3@#!${yosys.py3env}/bin/python3@" sbysrc/sby.py
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

  meta = with lib; {
    description = "An automatic clock gating utility.";
    homepage = "https://github.com/AUCOHL/Lighter";
    license = licenses.asl20;
    platforms = platforms.linux ++ platforms.darwin;
  };
}
