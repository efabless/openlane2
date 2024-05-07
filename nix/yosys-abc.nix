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
  cmake,
  libedit,
  rev ? "896e5e7dedf9b9b1459fa019f1fa8aa8101fdf43",
  sha256 ? "sha256-sMBCIV698TIvU/sgTwgPFWDC1kl2TeGv+3pQ06gs7aM=",
}:
clangStdenv.mkDerivation rec {
  name = "yosys-abc";

  src = fetchFromGitHub {
    owner = "YosysHQ";
    repo = "abc";
    inherit rev;
    inherit sha256;
  };

  patches = [
    ./patches/yosys/abc-editline.patch
  ];

  postPatch = ''
    sed -i "s@-lreadline@-ledit@" ./Makefile
  '';

  nativeBuildInputs = [cmake];
  buildInputs = [libedit];

  installPhase = "mkdir -p $out/bin && mv abc $out/bin";

  # needed by yosys
  passthru.rev = src.rev;

  meta = with lib; {
    description = "A tool for squential logic synthesis and formal verification (YosysHQ's Fork)";
    homepage = "https://people.eecs.berkeley.edu/~alanmi/abc";
    license = licenses.mit;
    mainProgram = "abc";
    platforms = platforms.unix;
  };
}
