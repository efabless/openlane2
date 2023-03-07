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

with pkgs; stdenv.mkDerivation {
  name = "netgen";
  src = fetchFromGitHub {
    owner = "RTimothyEdwards";
    repo = "netgen";
    rev = "e12883037c9844fb1bd61f861b264fc7e1028237";
    sha256 = "sha256-uSOem6zNRTZkT2OFgP80PJuLmsewPuyzPAvJWmTPQ44=";
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

  nativeBuildInputs = [
    clang
    clang-tools
  ];
}