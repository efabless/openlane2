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
  rev,
  sha256
}:

with pkgs; abc-verifier.overrideAttrs (finalAttrs: previousAttrs: {
  pname = "or-abc";
  version = "${rev}";

  src = fetchFromGitHub {
    owner = "The-OpenROAD-Project";
    repo = "abc";
    rev = "${rev}";
    hash = "${sha256}";
  };

  installPhase = ''
  mkdir -p $out/bin
  mv abc $out/bin

  mkdir -p $out/lib
  mv libabc.a $out/lib

  mkdir -p $out/include
  for header in $(find  ../src | grep "\\.h$" | sed "s@../src/@@"); do
    header_tgt=$out/include/$header
    header_dir=$(dirname $header_tgt) 
    mkdir -p $header_dir
    cp ../src/$header $header_tgt
  done
  '';
})