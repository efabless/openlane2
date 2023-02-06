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
  pkgs ? import ./nix/pkgs.nix {},
  ...
}:

with pkgs; with python3.pkgs; buildPythonPackage rec {
  pname = "python-slugify";
  name = pname;
  version = "v8.0.0";
  
  src = fetchFromGitHub {
    owner = "un33k";
    repo = pname;
    rev = version;
    sha256 = "sha256-8qiG6P+tx9aovPNqZJSBW1d1DcHhsRMr9dZFPMDe2Aw=";
  };

  doCheck = false;
  propagatedBuildInputs = [
    text-unidecode
  ];
}