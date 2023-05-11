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
  pkgs ? import ./pkgs.nix,
}:

with pkgs; clangStdenv.mkDerivation rec {
  name = "magic-vlsi";
  rev = "44b269e037d41c312e2f7fed8fa6b349067cde74";

  src = fetchFromGitHub {
    owner = "RTimothyEdwards";
    repo = "magic";
    inherit rev;
    sha256 = "sha256-CFuvjYsq23ULqcjXxHc8I2jHNLrWY8Cd6XLlyXSp5FI=";
  };

  patches = [
    ./patches/magic/csh.patch
    ./patches/magic/efbuild_void_return.patch
  ];

  nativeBuildInputs = [ python3 tcsh gnused ];

  # So here's the situation:
  ## * Magic will not compile without X11 libraries, even for headless use.
  ## * Magic with Cairo will use Cairo-X11 headers that are not available on
  ## pre-built Mac versions of Cairo which presume you're going to use Quartz.
  ## -> Unintuitively, that means X11 libraries must be present on Mac, but not
  ## Cairo.
  buildInputs = [
    xorg.libX11
    m4
    mesa_glu
    ncurses
    tcl
    tcsh
    tk
  ] ++ lib.optionals stdenv.isLinux [cairo];

  configureFlags = [
    "--with-tcl=${tcl}"
    "--with-tk=${tk}"
    "--disable-werror"
  ];

  preConfigure = ''
    # nix shebang fix
    patchShebangs ./scripts

    # "Precompute" git rev-parse HEAD
    sed -i 's@`git rev-parse HEAD`@${rev}@' ./scripts/defs.mak.in
  '';

  NIX_CFLAGS_COMPILE = "-Wno-implicit-function-declaration -Wno-parentheses -Wno-macro-redefined";

  # Fairly sure this is deprecated?
  enableParallelBuilding = true;
}