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
  rev = "47325949b87e857d75f81d306f02ebccf952cb15";
  sha256 = "sha256-H9B/vZUs0O2jwmidCTMYhO0JY4DL+gmQNeVawaccvuU=";
in let src = pkgs.fetchFromGitHub {
  owner = "efabless";
  repo = "volare";
  inherit rev;
  inherit sha256;
}; in import "${src}" {
  inherit pkgs;
}
