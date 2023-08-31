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
  abc = import ./yosys-abc.nix { inherit pkgs; };
in clangStdenv.mkDerivation rec {
  name = "yosys";

  src = fetchFromGitHub {
    owner = "YosysHQ";
    repo = "yosys";
    rev = "14d50a176d59a5eac95a57a01f9e933297251d5b";
    sha256 = "sha256-ZdtQ3tUEImJGYzN2j4f3fuxYUzTmSx6Vz8U7mLjgZXY=";
  };

  nativeBuildInputs = [ pkg-config bison flex ];
  propagatedBuildInputs = [ tcl ];

  buildInputs = [
    tcl
    readline
    libffi
    zlib
    (python3.withPackages (pp: with pp; [
      click
    ]))
  ];

  patches = [
    ./patches/yosys/fix-clang-build.patch
  ];

  postPatch = ''
    substituteInPlace ./Makefile \
      --replace 'echo UNKNOWN' 'echo ${builtins.substring 0 10 src.rev}'

    chmod +x ./misc/yosys-config.in
    patchShebangs tests ./misc/yosys-config.in
  '';

  preBuild = ''
    cp -r ${abc} abc/
    chmod -R 777 .
    # Verbose
    sed -Ei 's@PRETTY = 1@PRETTY = 0@' ./Makefile
    # Don't compare ABC revisions
    sed -Ei 's@ABCREV = \w+@ABCREV = default@' ./Makefile
    # Compile ABC First (Common Build Point of Failure)
    sed -Ei 's@TARGETS =@TARGETS = $(PROGRAM_PREFIX)yosys-abc$(EXE)@' ./Makefile
    make config-clang VERBOSE=1
  '';

  makeFlags = [ "PREFIX=${placeholder "out"}"];

  postBuild = "";
  postInstall = "";

  doCheck = false;
}