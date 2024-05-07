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
# Copyright (c) 2003-2023 Eelco Dolstra and the Nixpkgs/NixOS contributors
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
{
  lib,
  stdenv,
  fetchFromGitHub,
  cmake,
  pkg-config,
  openjdk,
  python3,
  gtest,
  antlr4,
  libuuid,
  gperftools,
  capnproto,
  nlohmann_json,
  rev ? "3e9c2d03c8164f76bf289f141856303477df5dec",
  sha256 ? "sha256-c4i/1tUONb5sz3OD1w8FSD7VRn/xoBGaVX7ChmujGCk=",
}:
stdenv.mkDerivation (finalAttrs: {
  name = "surelog";

  src = fetchFromGitHub {
    owner = "chipsalliance";
    repo = finalAttrs.name;
    inherit rev;
    inherit sha256;
    fetchSubmodules = true; # Use the included UHDM to avoid extreme brainrot
  };

  nativeBuildInputs = [
    cmake
    pkg-config
    openjdk
    (python3.withPackages (p:
      with p; [
        psutil
        orderedmultidict
      ]))
    gtest
    antlr4
  ];

  buildInputs = [
    libuuid
    gperftools
    capnproto
    antlr4.runtime.cpp
    nlohmann_json
  ];

  cmakeFlags = [
    "-DSURELOG_USE_HOST_CAPNP=On"
    "-DSURELOG_USE_HOST_GTEST=On"
    "-DSURELOG_USE_HOST_ANTLR=On"
    "-DSURELOG_USE_HOST_JSON=On"
    "-DSURELOG_BUILD_TESTS=Off" # Broken on macOS, CBA to fix them
    "-DANTLR_JAR_LOCATION=${antlr4.jarLocation}"
  ];

  doCheck = false;

  meta = with lib; {
    description = "SystemVerilog 2017 Pre-processor, Parser, Elaborator, UHDM Compiler";
    homepage = "https://github.com/chipsalliance/Surelog";
    license = licenses.asl20;
    mainProgram = "surelog";
    platforms = platforms.linux ++ platforms.darwin;
  };
})
