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
  pkgs ? import ./pkgs.nix,
}:

with pkgs; let
  abc = import ./yosys-abc.nix { inherit pkgs; };
in yosys.overrideAttrs (finalAttrs: previousAttrs: rec {
  name = "yosys";
  version = null;

  src = fetchFromGitHub {
    owner = "YosysHQ";
    repo = "yosys";
    rev = "f7a8284c7b095bca4bc2c65032144c4e3264ee4d";
    sha256 = "sha256-qhMcXJFEuBPl7vh+gYTu7PnSWi+L3YMLrBMQyYqfc0w=";
  };

  patches = [];

  nativeBuildInputs = [ pkg-config bison flex ];
  propagatedBuildInputs = [
    tcl
  ];

  doCheck = false;
  preBuild = ''
    cp -r ${abc} abc/
    chmod -R 777 .
    # Verbose
    sed -Ei 's@PRETTY = 1@PRETTY = 0@' ./Makefile
    # Don't compare ABC revisions
    sed -Ei 's@ABCREV = \w+@ABCREV = default@' ./Makefile
    # Compile ABC First (Common Build Point of Failure)
    sed -Ei 's@TARGETS =@TARGETS = $(PROGRAM_PREFIX)yosys-abc$(EXE)@' ./Makefile
    make config-${if stdenv.cc.isClang or false then "clang" else "gcc"} VERBOSE=1
  '';

  postBuild = "";
  postInstall = "";
})