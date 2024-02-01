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
  beautifulsoup4,
  jinja2,
  requests,
  flit,
}:
buildPythonPackage rec {
  name = "sphinx-tippy";
  version = "0.4.1";
  format = "pyproject";

  src = builtins.fetchurl {
    url = "https://github.com/sphinx-extensions2/sphinx-tippy/archive/refs/tags/v${version}.tar.gz";
    sha256 = "sha256:0y8zfi7371ca4pkrl1x1bxg9g6lrfr7sgjbk4v411hm5nsb60hww";
  };

  propagatedBuildInputs = [
    sphinx
    beautifulsoup4
    jinja2
    requests
  ];

  buildInputs = [
    flit
  ];

  meta = with lib; {
    description = "Get rich tool tips in your sphinx documentation!";
    homepage = "https://github.com/sphinx-extensions2/sphinx-tippy";
    license = licenses.mit;
    platforms = platforms.linux ++ platforms.darwin;
  };
}
