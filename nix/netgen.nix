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
}:

with pkgs; clangStdenv.mkDerivation {
  name = "netgen";
  src = fetchFromGitHub {
    owner = "RTimothyEdwards";
    repo = "netgen";
    rev = "1efa054ac1302a2b8b03a41e90420fc055d5796e";
    sha256 = "sha256-k3Ke6z2mW6BmpefgraEBBH4VHVX2v59rv8Pz3JKuEcU=";
  };

  configureFlags = [
    "--with-tk=${tk}"
    "--with-tcl=${tcl}"
  ];

  buildInputs = [
    tcl
    tk
    m4
    python3
  ];
}