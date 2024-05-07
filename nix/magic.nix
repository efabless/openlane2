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
  lib,
  clangStdenv,
  fetchFromGitHub,
  xorg,
  m4,
  ncurses,
  tcl,
  tcsh,
  tk,
  cairo,
  python3,
  gnused,
  rev ? "bfd938b5e2321cf9a6c15f398fbc987b56fcc179",
  sha256 ? "sha256-xNhPnNGoJ8YiG6NFeFhOuKTB56rQvggJugIvukao6U8=",
}:
clangStdenv.mkDerivation rec {
  name = "magic-vlsi";
  inherit rev;

  src = fetchFromGitHub {
    owner = "RTimothyEdwards";
    repo = "magic";
    inherit rev;
    inherit sha256;
  };

  nativeBuildInputs = [python3 gnused];

  buildInputs = [
    xorg.libX11
    m4
    ncurses
    tcl
    tcsh
    tk
    cairo
  ];

  configureFlags = [
    "--with-tcl=${tcl}"
    "--with-tk=${tk}"
    "--disable-werror"
  ];

  NIX_CFLAGS_COMPILE = "-Wno-implicit-function-declaration -Wno-parentheses -Wno-macro-redefined";

  postPatch = ''
    sed -i "s/dbReadOpen(cellDef, name,/dbReadOpen(cellDef, name != NULL,/" database/DBio.c
  '';

  preConfigure = ''
    # nix shebang fix
    patchShebangs ./scripts

    # "Precompute" git rev-parse HEAD
    sed -i 's@`git rev-parse HEAD`@${rev}@' ./scripts/defs.mak.in
  '';

  fixupPhase = ''
    sed -i "13iexport CAD_ROOT='$out/lib'" $out/bin/magic
    patchShebangs $out/bin/magic
  '';

  meta = with lib; {
    description = "VLSI layout tool written in Tcl";
    homepage = "http://opencircuitdesign.com/magic/";
    license = licenses.mit;
    platforms = platforms.linux ++ platforms.darwin;
  };
}
