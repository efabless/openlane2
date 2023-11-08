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
  opensta ? import ./opensta.nix {},
  libsForQt5 ? pkgs.libsForQt5,
}:

with pkgs; let
  abc = import ./openroad-abc.nix { inherit pkgs; };
in clangStdenv.mkDerivation rec {
  name = "openroad";
  rev = "95df42f3e443fe945902ce11b3e585f3e686e89e";

  src = fetchFromGitHub {
    owner = "The-OpenROAD-Project";
    repo = "OpenROAD";
    inherit rev;
    sha256 = "sha256-E0vo0OPRFH5TT9PjMpHJoS9AWoAI7c3L/kzl3pcg4j8=";
  };

  cmakeFlags = [
    "-DTCL_LIBRARY=${tcl}/lib/libtcl${stdenv.hostPlatform.extensions.sharedLibrary}"
    "-DTCL_HEADER=${tcl}/include/tcl.h"
    "-DUSE_SYSTEM_ABC:BOOL=ON"
    "-DUSE_SYSTEM_BOOST:BOOL=ON"
    "-DUSE_SYSTEM_OPENSTA:BOOL=ON"
    "-DOPENSTA_HOME=${opensta}"
    "-DABC_LIBRARY=${abc}/lib/libabc.a"
    "-DCMAKE_CXX_FLAGS=-I${abc}/include"
    "-DENABLE_TESTS:BOOL=OFF"
    "-DVERBOSE=1"
  ];

  preConfigure = ''
    sed -i "s/GITDIR-NOTFOUND/${rev}/" ./cmake/GetGitRevisionDescription.cmake
    patchShebangs ./etc/find_messages.py
    
    sed -i 's@#include "base/abc/abc.h"@#include <base/abc/abc.h>@' src/rmp/src/Restructure.cpp
    sed -i 's@#include "base/main/abcapis.h"@#include <base/main/abcapis.h>@' src/rmp/src/Restructure.cpp
    sed -i 's@# tclReadline@target_link_libraries(openroad readline)@' src/CMakeLists.txt
    sed -i 's@%include "../../src/Exception.i"@%include "../../Exception.i"@' src/dbSta/src/dbSta.i
  '';

  buildInputs = [
    abc
    boost
    eigen
    spdlog
    tcl
    python3
    readline
    tclreadline
    libffi
    libsForQt5.qtbase
    llvmPackages.openmp
    
    lemon-graph
    or-tools
    opensta
    glpk
    zlib
    clp
    cbc
    re2
  ];

  nativeBuildInputs = [
    swig
    pkg-config
    cmake
    gnumake
    flex
    bison
    libsForQt5.wrapQtAppsHook
  ];
}
