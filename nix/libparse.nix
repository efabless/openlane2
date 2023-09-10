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
  pkgs ? import ./pkgs.nix {}
}:

with pkgs; with python3.pkgs; buildPythonPackage rec {
  name = "libparse";

  src = fetchFromGitHub {
    owner = "efabless";
    repo = "libparse-python";
    rev = "15fbd65b5e4eb3964fbf7e7291c9ce2cf7f02113";
    sha256 = "sha256-zWV2pw1NkmzXNcO9456OfOUPZIXsSrEB0fMQ/NU060Y=";
    fetchSubmodules = true;
  };

  nativeBuildInputs = [
    clang
    swig
  ];

  doCheck = false;
}