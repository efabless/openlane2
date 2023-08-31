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

with pkgs; clangStdenv.mkDerivation rec {
  name = "verilator";
  rev = "23fe5c1b9386228afe80a42b95e91cde8462d1c4";

  src = fetchFromGitHub {
    owner = "verilator";
    repo = "verilator";
    inherit rev;
    sha256 = "sha256-nCYlRR7qvo7W3CCCl5FS1qFO0IMKYWwiysCLcJAE7xI=";
  };

  enableParallelBuilding = true;
  buildInputs = [ perl ];
  nativeBuildInputs = [ makeWrapper flex bison python3 autoconf help2man ];
  nativeCheckInputs = [ which ];

  preConfigure = "autoconf";

  postPatch = ''
    patchShebangs bin/* src/{flexfix,vlcovgen} test_regress/{driver.pl,t/*.pl}
  '';

  postInstall = lib.optionalString stdenv.isLinux ''
    for x in $(ls $out/bin/verilator*); do
      wrapProgram "$x" --set LOCALE_ARCHIVE "${glibcLocales}/lib/locale/locale-archive"
    done
  '';
}
