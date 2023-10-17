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

with pkgs; let
    surelog = import ./surelog.nix { inherit pkgs; };
in clangStdenv.mkDerivation rec {
  name = "yosys-synlig";
  dylibs = ["synlig-sv"];

  full-src = fetchFromGitHub {
    owner = "chipsalliance";
    repo = "synlig";
    rev = "e41b39653b5bc45f464825affa5464473be7b92a";
    sha256 = "sha256-2KM7JZhfHfNPu9LtLsoN7e3q+U32p+ybL36y9ae/wdU=";
  };

  src = "${full-src}/frontends/systemverilog";

  makeFlags = [
    "YOSYS_CONFIG=${yosys}/bin/yosys-config"
  ];

  propagatedBuildInputs = [
    yosys
    libedit
    libbsd
    zlib
  ];

  buildInputs = [
    yosys.py3
    cmake
    surelog
    surelog.uhdm'
    capnproto
  ];

  buildPhase = ''
  set -x
  yosys-config --build synlig-sv.so\
    --std=c++17\
    -I${full-src}/third_party/yosys_mod\
    *.cc\
    ${surelog.uhdm'}/lib/*.a\
    ${capnproto}/lib/*.a
  '';

  installPhase = ''
  mkdir -p $out/share/yosys/plugins
  cp synlig-sv.so $out/share/yosys/plugins/synlig-sv.so
  '';

  dontUseCmakeConfigure = true;

#   preConfigure = ''
#   sed -i.bak "s@/usr/local@$out@" Makefile
#   sed -i.bak "s@#!/usr/bin/env python3@#!${yosys.py3}/bin/python3@" sbysrc/sby.py
#   sed -i.bak "s@\"/usr/bin/env\", @@" sbysrc/sby_core.py
#   '';

#   checkPhase = ''
#   make test
#   '';

#   doCheck = false;

  computed_PATH = lib.makeBinPath propagatedBuildInputs;
  makeWrapperArgs = [
    "--prefix PATH : ${computed_PATH}"
  ];
}