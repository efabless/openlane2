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
  pkgs ? import ./pkgs.nix {},
}:
let
  rev = "8221a19ff69dda55590bd0b2ff676d4ed53e8e3d";
  sha256 = "sha256-J10jufeYwKE9t76XJA2bCiVRfwA/FuuuvuHjafUNN58=";
in let src = pkgs.fetchFromGitHub {
  owner = "efabless";
  repo = "volare";
  inherit rev;
  inherit sha256;
}; in import "${src}" {
  inherit pkgs;
}
