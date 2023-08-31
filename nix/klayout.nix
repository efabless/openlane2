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
  libsForQt5 ? pkgs.libsForQt5,
}:

with pkgs; let
  rev = "6a36bfa7c04f55bd732f8e0f91b553c8f9cebed7";
in clangStdenv.mkDerivation {
  pname = "klayout";
  version = "${rev}"; # I'm going to avoid a KLayout rebuild like the goddamn plague

  src = fetchFromGitHub {
    owner = "KLayout";
    repo = "klayout";
    rev = "${rev}";
    sha256 = "sha256-fjKxQ3oVtnFwzLeeE6kN0jKE5PIfBZubTF54KO+k/DE=";
  };

  postPatch = ''
    substituteInPlace src/klayout.pri --replace "-Wno-reserved-user-defined-literal" ""
    patchShebangs .
  '';

  nativeBuildInputs = [
    which
    perl
    python3
    ruby
    gnused
    libsForQt5.wrapQtAppsHook
  ];

  buildInputs = with libsForQt5; [
    qtbase
    qtmultimedia
    qttools
    qtxmlpatterns
    curl
    gcc
  ];

  propagatedBuildInputs = [
    ruby
  ];
  
  buildPhase = ''
    runHook preBuild
    mkdir -p $out/lib
    CC=clang CXX=clang++ ./build.sh -prefix $out/lib -option -j$NIX_BUILD_CORES -expert -verbose
    runHook postBuild
  '';

  postBuild = if stdenv.isDarwin then ''
    mkdir $out/bin
    cp $out/lib/klayout.app/Contents/MacOS/klayout $out/bin/
  '' else ''
    mkdir $out/bin
    cp $out/lib/klayout $out/bin/
  '';

  # Make libraries also accessible to standalone binary on macOS
  postFixup = if stdenv.isDarwin then ''
    sed -Ei "2iexport DYLD_LIBRARY_PATH=$out/lib:\$DYLD_LIBRARY_PATH" $out/bin/klayout
  '' else '''';

  dontInstall = true; # "Installation" already happens as part of "build.sh"
}