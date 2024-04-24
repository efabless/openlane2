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
  fetchFromGitHub,
  buildPythonPackage,
  matplotlib,
  numpy,
  pillow,
  octave,
  xschem,
  ngspice,
  magic,
  setuptools,
  setuptools_scm,
}:
buildPythonPackage rec {
  name = "cace";
  version = "2.1.0+126";
  format = "pyproject";

  src = fetchFromGitHub {
    owner = "efabless";
    repo = "cace";
    rev = "60350f572c9a773e4e2e3e3e77d984e7c1d03d37";
    sha256 = "sha256-ZBiyCPZWYwTYXISHSjge9YJmDbQ0An8Q6Lzm7V32wRg=";
  };

  postPatch = ''
    sed -i 's/setuptools_scm>=8/setuptools_scm>=7/' pyproject.toml
  '';

  buildInputs = [
    setuptools
    setuptools_scm
  ];

  propagatedBuildInputs = [
    matplotlib
    numpy
    pillow
    ngspice
    magic
    octave
    xschem
  ];

  meta = with lib; {
    description = "Circuit Automatic Characterization Engine";
    homepage = "https://github.com/efabless/cace";
    license = licenses.asl20;
    mainProgram = "cace";
    platforms = platforms.linux ++ platforms.darwin;
  };
}
