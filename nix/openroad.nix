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
  clangStdenv,
  fetchFromGitHub,
  openroad-abc,
  libsForQt5,
  opensta,
  boost183,
  eigen,
  tcl,
  python3,
  readline,
  tclreadline,
  spdlog-internal-fmt,
  libffi,
  llvmPackages,
  lemon-graph,
  or-tools,
  glpk,
  zlib,
  clp,
  cbc,
  re2,
  swig4,
  pkg-config,
  cmake,
  gnumake,
  flex,
  bison,
  clang-tools_14,
}:
clangStdenv.mkDerivation rec {
  name = "openroad";
  rev = "75f2f325b7a42e56a92404f33af8e96530d9b202";

  src = fetchFromGitHub {
    owner = "The-OpenROAD-Project";
    repo = "OpenROAD";
    inherit rev;
    sha256 = "sha256-QZ6Oui4JF4Z6e7SeAGI6pE8knbkOrdhVegABzmJHYhs=";
  };

  cmakeFlagsAll = [
    "-DTCL_LIBRARY=${tcl}/lib/libtcl${clangStdenv.hostPlatform.extensions.sharedLibrary}"
    "-DTCL_HEADER=${tcl}/include/tcl.h"
    "-DUSE_SYSTEM_BOOST:BOOL=ON"
    "-DCMAKE_CXX_FLAGS=-I${openroad-abc}/include"
    "-DENABLE_TESTS:BOOL=OFF"
    "-DVERBOSE=1"
  ];

  cmakeFlags =
    cmakeFlagsAll
    ++ [
      "-DUSE_SYSTEM_ABC:BOOL=ON"
      "-DUSE_SYSTEM_OPENSTA:BOOL=ON"
      "-DOPENSTA_HOME=${opensta}"
      "-DABC_LIBRARY=${openroad-abc}/lib/libabc.a"
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
    openroad-abc
    boost183
    eigen
    tcl
    python3
    readline
    tclreadline
    spdlog-internal-fmt
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
    swig4
    pkg-config
    cmake
    gnumake
    flex
    bison
    libsForQt5.wrapQtAppsHook
    clang-tools_14
  ];

  shellHook = ''
    export DEVSHELL_CMAKE_FLAGS="${builtins.concatStringsSep " " cmakeFlagsAll}"
  '';

  meta = with lib; {
    description = "OpenROAD's unified application implementing an RTL-to-GDS flow";
    homepage = "https://theopenroadproject.org";
    # OpenROAD code is BSD-licensed, but OpenSTA is GPLv3 licensed,
    # so the combined work is GPLv3
    license = licenses.gpl3Plus;
    platforms = platforms.linux ++ platforms.darwin;
  };
}
