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
  pkgs ? import ./pkgs.nix {},
}:

with pkgs; let
    uhdm' = uhdm.overrideAttrs(finalAttrs: previousAttrs: rec {
        version = "1.76";
        src = fetchFromGitHub {
            owner = "chipsalliance";
            repo = "uhdm";
            rev = "v${version}";
            hash = "sha256-Q/u5lvILYDT5iScES3CTPIm/B5apoOHXOQmCsZ73NlU=";
        };
        patches = [];
        doCheck = false;
        buildInputs = previousAttrs.buildInputs ++ [
            capnproto
        ];
        cmakeFlags = [
            "-DUHDM_BUILD_TESTS:BOOL=OFF"
            "-DUHDM_USE_HOST_CAPNP:BOOL=ON"
        ];
        postInstall = "";
    });
in stdenv.mkDerivation (finalAttrs: {
  pname = "surelog";
  version = "1.76";

  src = fetchFromGitHub {
    owner = "chipsalliance";
    repo = finalAttrs.pname;
    rev = "v${finalAttrs.version}";
    hash = "sha256-Vg9NZrgzFRVIsEbZQe8DItDhFOVG1XZoQWBrLzVNwLU=";
    fetchSubmodules = false;  # we use all dependencies from nix
  };

  nativeBuildInputs = [
    cmake
    pkg-config
    openjdk
    (python3.withPackages (p: with p; [
      psutil
      orderedmultidict
    ]))
    gtest
    antlr4
  ];

  buildInputs = [
    libuuid
    gperftools
    uhdm'
    capnproto
    antlr4.runtime.cpp
    nlohmann_json
  ];

  cmakeFlags = [
    "-DSURELOG_USE_HOST_CAPNP=On"
    "-DSURELOG_USE_HOST_UHDM=On"
    "-DSURELOG_USE_HOST_GTEST=On"
    "-DSURELOG_USE_HOST_ANTLR=On"
    "-DSURELOG_USE_HOST_JSON=On"
    "-DANTLR_JAR_LOCATION=${antlr4.jarLocation}"
  ];

  doCheck = true;
  checkPhase = ''
    runHook preCheck
    make -j $NIX_BUILD_CORES UnitTests
    ctest --output-on-failure
    runHook postCheck
  '';

  passthru = {
    inherit uhdm';
  };

})
