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
  libsForQt5 ? pkgs.libsForQt5,
}:

with pkgs; let
  abc = import ./openroad-abc.nix { inherit pkgs; };
  or-tools = import ./or-tools.nix { inherit pkgs; };
  lemon = lemon-graph.overrideAttrs (finalAttrs: previousAttrs: {
    meta = {
      broken = false;
    };
    doCheck = !stdenv.isDarwin; # Some tests fail to compile on Darwin
  });
in clangStdenv.mkDerivation rec {
  name = "openroad";
  rev = "6de104daffe029fd717645b21f3e6ed6aad1042b";

  src = fetchFromGitHub {
    owner = "The-OpenROAD-Project";
    repo = "OpenROAD";
    inherit rev;
    sha256 = "sha256-nXAHbfEIQlZrvYynL7uQDAl2JTCpqMcWVrJQP/3SK+w=";
    fetchSubmodules = true;
  };

  cmakeFlags = [
    "-DTCL_LIBRARY=${tcl}/lib/libtcl${stdenv.hostPlatform.extensions.sharedLibrary}"
    "-DTCL_HEADER=${tcl}/include/tcl.h"
    "-DUSE_SYSTEM_ABC:BOOL=ON"
    "-DUSE_SYSTEM_BOOST:BOOL=ON"
    "-DABC_LIBRARY=${abc}/lib/libabc.a"
    "-DCMAKE_CXX_FLAGS=-I${abc}/include"
    "-DVERBOSE=1"
  ];

  preConfigure = ''
    sed -i "s/GITDIR-NOTFOUND/${rev}/" ./cmake/GetGitRevisionDescription.cmake
    patchShebangs ./etc/find_messages.py
    
    sed -i 's@#include "base/abc/abc.h"@#include <base/abc/abc.h>@' src/rmp/src/Restructure.cpp
    sed -i 's@#include "base/main/abcapis.h"@#include <base/main/abcapis.h>@' src/rmp/src/Restructure.cpp
    sed -i 's@# tclReadline@target_link_libraries(openroad readline)@' src/CMakeLists.txt
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
    
    or-tools
    re2
    glpk
    zlib
    clp
    cbc
    
    lemon
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