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
  rev,
  sha256,

  python-pname ? "python38Full",
}:

with pkgs; let boost-static = boost.override {
  enableShared = false;
  enabledStatic = true;
}; in clangStdenv.mkDerivation {
  name = "openroad";
  src = fetchgit {
    url = "https://github.com/The-OpenROAD-Project/OpenROAD";
    rev = "${rev}";
    sha256 = "${sha256}";
    fetchSubmodules = true;
  };

  preConfigure = ''
    sed -i "s/GITDIR-NOTFOUND/${rev}/" ./cmake/GetGitRevisionDescription.cmake
    patchShebangs ./etc/find_messages.py
  '';

  buildInputs = [
    eigen
    spdlog
    tcl
    tk
    python3Full
    readline
    libffi
    qt6.full
    llvmPackages.openmp
    
    # ortools
    re2
    glpk
    zlib
    clp
    cbc
    lemon-graph
    or-tools
  ];

  nativeBuildInputs = [
    boost-static
    swig
    pkg-config
    cmake
    gnumake
    flex
    bison
  ];
}