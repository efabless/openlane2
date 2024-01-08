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
{ lib
, yosys
, clangStdenv
, fetchFromGitHub
, surelog
, capnproto
, antlr4
, pkg-config
, writeText
}:

clangStdenv.mkDerivation rec {
  name = "yosys-synlig-sv";
  dylibs = [ "synlig-sv" ];

  src = fetchFromGitHub {
    owner = "chipsalliance";
    repo = "synlig";
    rev = "e41b39653b5bc45f464825affa5464473be7b92a";
    sha256 = "sha256-2KM7JZhfHfNPu9LtLsoN7e3q+U32p+ybL36y9ae/wdU=";
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

  buildPhase = ''
    rm third_party/Build.surelog.mk
    cp ${yosys-mk} third_party/Build.yosys.mk
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
