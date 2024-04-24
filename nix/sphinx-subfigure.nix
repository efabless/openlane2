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
  lib,
  buildPythonPackage,
  sphinx,
  flit,
}:
buildPythonPackage rec {
  name = "sphinx-subfigure";
  version = "0.2.4";
  format = "pyproject";

  src = builtins.fetchurl {
    url = "https://github.com/sphinx-extensions2/sphinx-subfigure/archive/refs/tags/v${version}.tar.gz";
    sha256 = "sha256:1lr0n3yag7r1dkh78prb2qx2dyvmczzbw3cjy18gph8m18zvqm9c";
  };

  propagatedBuildInputs = [
    sphinx
  ];

  buildInputs = [
    flit
  ];

  meta = with lib; {
    description = "A sphinx extension to create figures with multiple images";
    homepage = "https://github.com/sphinx-extensions2/sphinx-subfigure";
    license = licenses.mit;
    platforms = platforms.linux ++ platforms.darwin;
  };
}
