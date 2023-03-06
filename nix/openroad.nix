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
  rev,
  sha256,
  abc-rev,
  abc-sha256,
  libsForQt5 ? pkgs.libsForQt5,
}:

with pkgs; let boost-static = boost.override {
  enableShared = false;
  enabledStatic = true;
}; lemon-graph-crossplat = lemon-graph.overrideAttrs (finalAttrs: previousAttrs: {
  meta = {
    broken = false;
  };
  doCheck = !stdenv.isDarwin; # Some tests fail to compile on Darwin
}); abc-derivation = abc-verifier.overrideAttrs (finalAttrs: previousAttrs: {
  pname = "or-abc";
  version = "${abc-rev}";

  src = fetchFromGitHub {
    owner = "The-OpenROAD-Project";
    repo = "abc";
    rev = "${abc-rev}";
    hash = "${abc-sha256}";
  };

  installPhase = ''
  mkdir -p $out/bin
  mv abc $out/bin

  mkdir -p $out/lib
  mv libabc.a $out/lib

  mkdir -p $out/include
  for header in $(find  ../src | grep "\\.h$" | sed "s@../src/@@"); do
    header_tgt=$out/include/$header
    header_dir=$(dirname $header_tgt) 
    mkdir -p $header_dir
    cp ../src/$header $header_tgt
  done
  '';
}); in clangStdenv.mkDerivation {
  pname = "openroad";
  version = "${rev}";

  src = fetchgit {
    url = "https://github.com/The-OpenROAD-Project/OpenROAD";
    rev = "${rev}";
    sha256 = "${sha256}";
    fetchSubmodules = true;
  };

  cmakeFlags = [
    "-DTCL_LIBRARY=${tcl}/lib/libtcl${stdenv.hostPlatform.extensions.sharedLibrary}"
    "-DTCL_HEADER=${tcl}/include/tcl.h"
    "-DUSE_SYSTEM_ABC:BOOL=ON"
    "-DUSE_SYSTEM_BOOST:BOOL=ON"
    "-DABC_LIBRARY=${abc-derivation}/lib/libabc.a"
    "-DCMAKE_CXX_FLAGS=-I${abc-derivation}/include"
    "-DVERBOSE=1"
  ];

  preConfigure = ''
    sed -i "s/GITDIR-NOTFOUND/${rev}/" ./cmake/GetGitRevisionDescription.cmake
    patchShebangs ./etc/find_messages.py
    
    sed -i 's@#include "base/abc/abc.h"@#include <base/abc/abc.h>@' src/rmp/src/Restructure.cpp
    sed -i 's@#include "base/main/abcapis.h"@#include <base/main/abcapis.h>@' src/rmp/src/Restructure.cpp
    sed -i 's@# tclReadline@target_link_libraries(openroad readline)@' src/CMakeLists.txt
  '' + (lib.optionalString (!stdenv.isLinux) ''
    sed -i "s/add_subdirectory(mpl2)//" ./src/CMakeLists.txt
  '');

  buildInputs = [
    abc-derivation
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
    
    # ortools
    re2
    glpk
    zlib
    clp
    cbc
    
    lemon-graph-crossplat
  ] ++ lib.optionals stdenv.isLinux [or-tools];

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