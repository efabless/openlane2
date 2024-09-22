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
{
  lib,
  fetchurl,
  buildPythonPackage,
  fetchPypi,
  pyyaml,
  setuptools,
  version ? "0.0.2",
  sha256 ? "sha256-iy65VBy+Fq+XsSy9w2+rkqjG9Y/ImL1oZR6Vnn2Okm8=",
}: let
  self = buildPythonPackage {
    pname = "yamlcore";
    inherit version;
    format = "pyproject";

    src = fetchPypi {
      inherit (self) pname version;
      inherit sha256;
    };

    nativeBuildInputs = [
      setuptools
    ];

    meta = with lib; {
      description = "YAML 1.2 Core Schema Support for PyYAML";
      homepage = "https://github.com/perlpunk/pyyaml-core";
      license = licenses.mit;
      inherit (pyyaml.meta) platforms;
    };
  };
in
  self
