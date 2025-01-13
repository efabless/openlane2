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
  tclreadline,
  python3,
  readline,
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
  gtest,
  # environments,
  rev ? "2fb3cdf40ebc3f578ae29a6cd7bd6939868af495",
  rev-date ? "2025-01-12",
  sha256 ? "sha256-B120jqfaWMVrfUom8BEu9RnyCpwVtt4wj7Qrs/ySBtI=",
  openroad,
  buildPythonEnvForInterpreter,
}: let
  stdenv = llvmPackages_17.stdenv;
  cmakeFlagsCommon = debug: [
    "-DTCL_LIBRARY=${tcl}/lib/libtcl${stdenv.hostPlatform.extensions.sharedLibrary}"
    "-DTCL_HEADER=${tcl}/include/tcl.h"
    "-DUSE_SYSTEM_BOOST:BOOL=ON"
    "-DCMAKE_CXX_FLAGS=-DBOOST_STACKTRACE_GNU_SOURCE_NOT_REQUIRED=1 -I${eigen}/include/eigen3 ${lib.strings.optionalString debug "-g -O0"}"
    "-DCMAKE_EXE_LINKER_FLAGS=-L${cudd}/lib -lcudd"
    "-DVERBOSE=1"
  ];
in
  stdenv.mkDerivation (finalAttrs: {
    __structuredAttrs = true; # better serialization; enables spaces in cmakeFlags

    pname = "openroad";
    version = rev-date;

    src = fetchFromGitHub {
      owner = "The-OpenROAD-Project";
      repo = "OpenROAD";
      inherit rev;
      inherit sha256;
    };

    cmakeFlagsDevDebug = lib.strings.concatMapStrings (
      x: " \"${x}\" "
    ) (cmakeFlagsCommon true);

    cmakeFlagsDevRelease = lib.strings.concatMapStrings (
      x: " \"${x}\" "
    ) (cmakeFlagsCommon false);

    cmakeFlags =
      (cmakeFlagsCommon false)
      ++ [
        "-DUSE_SYSTEM_ABC:BOOL=ON"
        "-DUSE_SYSTEM_OPENSTA:BOOL=ON"
        "-DENABLE_TESTS:BOOL=OFF"
        "-DOPENSTA_HOME=${opensta}"
        "-DABC_LIBRARY=${openroad-abc}/lib/libabc.a"
      ];

    preConfigure = ''
      sed -i "s/GITDIR-NOTFOUND/${rev}/" ./cmake/GetGitRevisionDescription.cmake
      patchShebangs ./etc/find_messages.py

      sed -i 's@#include "base/abc/abc.h"@#include <base/abc/abc.h>@' src/rmp/src/Restructure.cpp
      sed -i 's@#include "base/main/abcapis.h"@#include <base/main/abcapis.h>@' src/rmp/src/Restructure.cpp
      sed -i 's@# tclReadline@target_link_libraries(openroad readline ${cudd}/lib/libcudd.a)@' src/CMakeLists.txt
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
      llvmPackages.libunwind

      lemon-graph
      opensta
      glpk
      zlib
      clp
      cbc
      gtest

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
      python3.pkgs.tclint
    ];

    shellHook = ''
      ord-format-changed() {
        ${git}/bin/git diff --name-only | grep -E '\.(cpp|cc|c|h|hh)$' | xargs clang-format -i -style=file:.clang-format
        ${git}/bin/git diff --name-only | grep -E '\.(tcl)$' | xargs tclfmt --in-place
      }
      alias ord-cmake-debug="cmake -DCMAKE_BUILD_TYPE=Debug $cmakeFlagsDevDebug -G Ninja"
      alias ord-cmake-release="cmake -DCMAKE_BUILD_TYPE=Release $cmakeFlagsDevRelease -G Ninja"
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
