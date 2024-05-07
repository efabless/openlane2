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
  libedit,
  libbsd,
  yosys,
  clangStdenv,
  fetchFromGitHub,
  zlib,
  bash,
  rev ? "dfe9b1a15b494e7dd81a2b394dac30ea707ec5cc",
  sha256 ? "sha256-NJnu/uFCF+esqV2hrZughn1gdZXQJNTJbl1VyKns3XE=",
}:
clangStdenv.mkDerivation rec {
  name = "yosys-f4pga-sdc";
  dylibs = ["sdc" "design_introspection"];

  src = fetchFromGitHub {
    owner = "chipsalliance";
    repo = "yosys-f4pga-plugins";
    inherit rev;
    inherit sha256;
  };
  buildInputs = [
    yosys
    yosys.py3env
    libedit
    libbsd
    zlib
  ];

  preConfigure = ''
    patchShebangs .
  '';

  buildPhase = ''
    make SHELL=${bash}/bin/bash -C sdc-plugin -j$NIX_BUILD_CORES
    make SHELL=${bash}/bin/bash -C design_introspection-plugin -j$NIX_BUILD_CORES
  '';

  installPhase = ''
    mkdir -p $out/share/yosys/plugins
    mv sdc-plugin/build/sdc.so $out/share/yosys/plugins/sdc.so
    mv design_introspection-plugin/build/design_introspection.so $out/share/yosys/plugins/design_introspection.so
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
