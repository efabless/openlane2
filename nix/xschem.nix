# Copyright 2024 Efabless Corporation
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
#
# Copyright (c) 2003-2024 Eelco Dolstra and the Nixpkgs/NixOS contributors
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
{
  stdenv,
  fetchFromGitHub,
  lib,
  bison,
  cairo,
  flex,
  xorg,
  pkg-config,
  tcl,
  tk-x11,
}:
stdenv.mkDerivation rec {
  pname = "xschem";
  version = "3.4.4+622";

  src = fetchFromGitHub {
    owner = "StefanSchippers";
    repo = "xschem";
    rev = "83f62bfdf903a38f6f716edcc445df26927db00c";
    sha256 = "sha256-1jP1SJeq23XNkOQgcl2X+rBrlka4a04irmfhoKRM1j4=";
  };

  nativeBuildInputs = [bison flex pkg-config];

  buildInputs = [cairo xorg.libX11 xorg.libXpm tcl tk-x11];

  hardeningDisable = ["format"];

  meta = with lib; {
    description = "Schematic capture and netlisting EDA tool";
    longDescription = ''
      Xschem is a schematic capture program, it allows creation of
      hierarchical representation of circuits with a top down approach.
      By focusing on interfaces, hierarchy and instance properties a
      complex system can be described in terms of simpler building
      blocks. A VHDL or Verilog or Spice netlist can be generated from
      the drawn schematic, allowing the simulation of the circuit.
    '';
    homepage = "https://xschem.sourceforge.io/stefan/";
    license = licenses.gpl2Plus;
    platforms = platforms.linux ++ platforms.darwin;
  };
}
