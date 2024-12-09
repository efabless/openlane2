# Copyright 2023-2024 Efabless Corporation
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
  llvmPackages_17,
  fetchFromGitHub,
  openroad-abc,
  libsForQt5,
  opensta,
  boost186,
  eigen,
  cudd,
  tcl,
  python3,
  readline,
  tclreadline,
  spdlog,
  libffi,
  llvmPackages,
  lemon-graph,
  or-tools_9_11,
  glpk,
  zlib,
  clp,
  cbc,
  re2,
  swig4,
  pkg-config,
  gnumake,
  flex,
  bison,
  buildEnv,
  makeBinaryWrapper,
  cmake,
  ninja,
  git,
  rev ? "1d610077e69607c430ffedd0dc6034c6af701a39",
  rev-date ? "2024-12-05",
  sha256 ? "sha256-jkyugDqA5I54Xozdf6xbajCmghNt3rF0srzGMzcKxQ8=",
  # environments,
  openroad,
  buildPythonEnvForInterpreter,
}: let
  stdenv = llvmPackages_17.stdenv;
in
  stdenv.mkDerivation (finalAttrs: {
    pname = "openroad";
    version = rev-date;

    src = fetchFromGitHub {
      owner = "The-OpenROAD-Project";
      repo = "OpenROAD";
      inherit rev;
      inherit sha256;
    };

    patches = [./patches/openroad/patches.diff];

    cmakeFlagsAll = [
      "-DTCL_LIBRARY=${tcl}/lib/libtcl${stdenv.hostPlatform.extensions.sharedLibrary}"
      "-DTCL_HEADER=${tcl}/include/tcl.h"
      "-DUSE_SYSTEM_BOOST:BOOL=ON"
      "-DCMAKE_CXX_FLAGS=-I${openroad-abc}/include"
      "-DENABLE_TESTS:BOOL=OFF"
      "-DVERBOSE=1"
    ];

    cmakeFlags =
      finalAttrs.cmakeFlagsAll
      ++ [
        "-DUSE_SYSTEM_ABC:BOOL=ON"
        "-DUSE_SYSTEM_OPENSTA:BOOL=ON"
        "-DCMAKE_CXX_FLAGS=-I${eigen}/include/eigen3"
        "-DOPENSTA_HOME=${opensta}"
        "-DABC_LIBRARY=${openroad-abc}/lib/libabc.a"
      ];

    preConfigure = ''
      sed -i "s/GITDIR-NOTFOUND/${rev}/" ./cmake/GetGitRevisionDescription.cmake
      patchShebangs ./etc/find_messages.py

      sed -i 's@#include "base/abc/abc.h"@#include <base/abc/abc.h>@' src/rmp/src/Restructure.cpp
      sed -i 's@#include "base/main/abcapis.h"@#include <base/main/abcapis.h>@' src/rmp/src/Restructure.cpp
      sed -i 's@# tclReadline@target_link_libraries(openroad readline)@' src/CMakeLists.txt
      sed -i 's@''${TCL_LIBRARY}@''${TCL_LIBRARY}\n${cudd}/lib/libcudd.a@' src/CMakeLists.txt
    '';

    buildInputs = [
      openroad-abc
      boost186
      eigen
      cudd
      tcl
      python3
      readline
      tclreadline
      spdlog
      libffi
      libsForQt5.qtbase
      libsForQt5.qt5.qtcharts
      llvmPackages.openmp

      lemon-graph
      opensta
      glpk
      zlib
      clp
      cbc

      or-tools_9_11
    ];

    nativeBuildInputs = [
      swig4
      pkg-config
      cmake
      gnumake
      flex
      bison
      ninja
      libsForQt5.wrapQtAppsHook
      llvmPackages_17.clang-tools
    ];

    shellHook = ''
      alias ord-format-changed="${git}/bin/git diff --name-only | grep -E '\.(cpp|cc|c|h|hh)$' | xargs clang-format -i -style=file:.clang-format";
      alias ord-cmake-debug="cmake -DCMAKE_BUILD_TYPE=Debug -DCMAKE_CXX_FLAGS="-g" -G Ninja $cmakeFlags .."
      alias ord-cmake-release="cmake -DCMAKE_BUILD_TYPE=Release -G Ninja $cmakeFlags .."
    '';

    passthru = {
      inherit python3;
      withPythonPackages = buildPythonEnvForInterpreter {
        target = openroad;
        inherit lib;
        inherit buildEnv;
        inherit makeBinaryWrapper;
      };
    };

    meta = with lib; {
      description = "OpenROAD's unified application implementing an RTL-to-GDS flow";
      homepage = "https://theopenroadproject.org";
      # OpenROAD code is BSD-licensed, but OpenSTA is GPLv3 licensed,
      # so the combined work is GPLv3
      license = licenses.gpl3Plus;
      platforms = platforms.linux ++ platforms.darwin;
    };
  })
