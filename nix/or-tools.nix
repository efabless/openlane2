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

# Copyright (c) 2003-2023 Eelco Dolstra and the Nixpkgs/NixOS contributors

# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:

# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

{
  pkgs ? import ./pkgs.nix
}:

with pkgs; let abseil-cpp17 = abseil-cpp.overrideAttrs(finalAttrs: previousAttrs: {
  stdenv = clangStdenv;
  cmakeFlags = [
    "-DCMAKE_CXX_STANDARD=17"
  ];
}); in clangStdenv.mkDerivation rec {
  pname = "or-tools";
  version = "9.4";

  src = fetchFromGitHub {
    owner = "google";
    repo = "or-tools";
    rev = "v${version}";
    sha256 = "sha256-joWonJGuxlgHhXLznRhC1MDltQulXzpo4Do9dec1bLY=";
  };
  patches = [
    # Disable test that requires external input: https://github.com/google/or-tools/issues/3429
    (fetchpatch {
      url = "https://github.com/google/or-tools/commit/7072ae92ec204afcbfce17d5360a5884c136ce90.patch";
      hash = "sha256-iWE+atp308q7pC1L1FD6sK8LvWchZ3ofxvXssguozbM=";
    })
    # Fix test that broke in parallel builds: https://github.com/google/or-tools/issues/3461
    (fetchpatch {
      url = "https://github.com/google/or-tools/commit/a26602f24781e7bfcc39612568aa9f4010bb9736.patch";
      hash = "sha256-gM0rW0xRXMYaCwltPK0ih5mdo3HtX6mKltJDHe4gbLc=";
    })
  ];

  cmakeFlags = [
    "-DBUILD_DEPS=OFF"
    "-DBUILD_PYTHON=ON"
    "-DBUILD_pybind11=OFF"
    "-DFETCH_PYTHON_DEPS=OFF"
    "-DUSE_GLPK=ON"
    "-DUSE_SCIP=OFF"
  ];
  nativeBuildInputs = [
    cmake
    ensureNewerSourcesForZipFilesHook
    pkg-config
    python3
    python3.pkgs.pip
    python3.pkgs.virtualenv
    swig4
    unzip
  ];
  buildInputs = [
    bzip2
    cbc
    eigen
    glpk
    python3.pkgs.absl-py
    python3.pkgs.mypy-protobuf
    python3.pkgs.pybind11
    python3.pkgs.setuptools
    python3.pkgs.wheel
    re2
    zlib
  ];
  propagatedBuildInputs = [
    abseil-cpp17
    protobuf
    python3.pkgs.protobuf
    python3.pkgs.numpy
  ];
  nativeCheckInputs = [
    python3.pkgs.matplotlib
    python3.pkgs.pandas
  ];

  doCheck = false;

  # This extra configure step prevents the installer from littering
  # $out/bin with sample programs that only really function as tests,
  # and disables the upstream installation of a zipped Python egg that
  # can’t be imported with our Python setup.
  installPhase = ''
    cmake . -DBUILD_EXAMPLES=OFF -DBUILD_PYTHON=OFF -DBUILD_SAMPLES=OFF
    cmake --install .
    pip install --prefix="$python" python/
  '';

  outputs = [ "out" "python" ];
}