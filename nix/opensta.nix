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
  swig,
  pkg-config,
  cmake,
  gnumake,
  flex,
  bison,
  tcl,
  zlib,
  eigen,
  rev ? "ee8d3d0fa23bfbc69f3e936ff884c3d30f5bfb59",
  sha256 ? "sha256-ZLCXEmuSxGnht/ILLQSpOGHlJiDHo6gHUp+ZjV+6wxQ=",
}:
clangStdenv.mkDerivation rec {
  name = "opensta";
  inherit rev;

  src = fetchFromGitHub {
    owner = "The-OpenROAD-Project";
    repo = "OpenSTA";
    inherit rev;
    inherit sha256;
  };

  cmakeFlags = [
    "-DTCL_LIBRARY=${tcl}/lib/libtcl${clangStdenv.hostPlatform.extensions.sharedLibrary}"
    "-DTCL_HEADER=${tcl}/include/tcl.h"
  ];

  buildInputs = [
    eigen
    tcl
    zlib
  ];

  # Files needed by OpenROAD when building with external OpenSTA
  postInstall = ''
    for file in $(find ${src} | grep -v examples | grep -E "(\.tcl|\.i)\$"); do
      relative_dir=$(dirname $(realpath --relative-to=${src} $file))
      true_dir=$out/$relative_dir
      mkdir -p $true_dir
      cp $file $true_dir
    done
    for file in $(find ${src} | grep -v examples | grep -E "(\.hh)\$"); do
      relative_dir=$(dirname $(realpath --relative-to=${src} $file))
      true_dir=$out/include/$relative_dir
      mkdir -p $true_dir
      cp $file $true_dir
    done
    find $out
  '';

  nativeBuildInputs = [
    swig
    pkg-config
    cmake
    gnumake
    flex
    bison
  ];

  meta = with lib; {
    description = "Gate-level static timing verifier";
    homepage = "https://parallaxsw.com";
    license = licenses.gpl3Plus;
    platforms = platforms.darwin ++ platforms.linux;
  };
}
