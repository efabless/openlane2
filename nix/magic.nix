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
  sha256,

  python-pname ? "python38Full",
}:

with pkgs; magic-vlsi.overrideAttrs (finalAttrs: previousAttrs: {
  version = "${rev}";

  src = fetchgit {
    url = "https://github.com/RTimothyEdwards/magic";
    rev = "${rev}";
    sha256 = "${sha256}";
  };

  nativeBuildInputs = [ pkgs."${python-pname}" tcsh gnused ];

  preConfigure = ''
  # Replace csh invocations with tcsh
  for file in ./scripts/*; do
      sed -i 's@/bin/csh/@/usr/bin/env tcsh@g' $file
  done

  # Remove manual csh test
  sed -i '5386,5388d' ./scripts/configure

  # "Precompute" git rev-parse HEAD
  sed -i 's@`git rev-parse HEAD`@${rev}@' ./scripts/defs.mak.in

  # Patch all shebangs to meet Nix standards
  patchShebangs ./scripts/*
  '';
})