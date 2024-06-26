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
  clangStdenv,
  fetchFromGitHub,
  surelog,
  capnproto,
  antlr4,
  pkg-config,
  writeText,
}:
clangStdenv.mkDerivation rec {
  name = "yosys-synlig-sv";
  dylibs = ["synlig-sv"];

  src = fetchFromGitHub {
    owner = "rowanG077";
    repo = "synlig";
    rev = "c342ac4ca66fd2dbee5e1122d1a0380a3d13d0ef";
    sha256 = "sha256-DpXxU+SdP8DybN2yyHlzLk65F50oOt8mxGijGeWyKSM=";
  };

  buildInputs = [
    yosys
    yosys.py3env
    surelog
    capnproto
    antlr4.runtime.cpp
  ];

  nativeBuildInputs = [
    pkg-config
  ];

  yosys-mk = writeText "yosys-mk" ''
    t  := yosys
    ts := ''$(call GetTargetStructName,''${t})

    ''${ts}.src_dir         := ''$(shell yosys-config --datdir/include)
    ''${ts}.mod_dir         := ''${TOP_DIR}third_party/yosys_mod/
  '';

  postPatch = ''
    rm third_party/Build.surelog.mk
    cp ${yosys-mk} third_party/Build.yosys.mk
  '';

  buildPhase = ''
    make build@systemverilog-plugin\
      -j$NIX_BUILD_CORES\
      LDFLAGS="''$(yosys-config --ldflags)"
  '';

  installPhase = ''
    mkdir -p $out/share/yosys/plugins
    mv build/release/systemverilog-plugin/systemverilog.so $out/share/yosys/plugins/synlig-sv.so
  '';

  computed_PATH = lib.makeBinPath buildInputs;
  makeWrapperArgs = [
    "--prefix PATH : ${computed_PATH}"
  ];

  meta = with lib; {
    description = "SystemVerilog and UHDM front end plugin for Yosys";
    homepage = "https://github.com/chipsalliance/synlig";
    license = licenses.asl20;
    platforms = platforms.linux ++ platforms.darwin;
  };
}
