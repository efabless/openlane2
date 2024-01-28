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
}:
clangStdenv.mkDerivation rec {
  name = "opensta";
  rev = "42b994d429aef6d553baae6aac8c23477b6e0654";

  src = fetchFromGitHub {
    owner = "The-OpenROAD-Project";
    repo = "OpenSTA";
    inherit rev;
    sha256 = "sha256-N0oU8INj+kaGOLHRIVOEIV2Dh8fB0GUBbLIBMYlXJYE=";
  };

  cmakeFlags = [
    "-DTCL_LIBRARY=${tcl}/lib/libtcl${clangStdenv.hostPlatform.extensions.sharedLibrary}"
    "-DTCL_HEADER=${tcl}/include/tcl.h"
  ];

  buildInputs = [
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
