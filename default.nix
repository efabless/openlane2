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
  pkgs ? import ./nix/pkgs.nix,
  gitignore-src ? import ./nix/gitignore.nix { inherit pkgs; },
  
  magic ? import ./nix/magic.nix { inherit pkgs; },

  netgen ? import ./nix/netgen.nix { inherit pkgs; },

  openroad ? pkgs.libsForQt5.callPackage ./nix/openroad.nix {
    inherit pkgs;
  },

  klayout ? pkgs.libsForQt5.callPackage ./nix/klayout.nix {
    inherit pkgs;
  },

  yosys ? import ./nix/yosys.nix { inherit pkgs; },
  
  volare-rev ? "25ac34672c7c76ef7efc0d7581ce35a16db0865a",
  volare-sha256 ? "sha256-KEn8EwKSoMl6CrDbyRotZ5psgQVlQMYkJMeFo7V55Dc=",
  volare ? let src = pkgs.fetchFromGitHub {
    owner = "efabless";
    repo = "volare";
    rev = volare-rev;
    sha256 = volare-sha256;
  }; in import "${src}" {
    inherit pkgs;
  },

  
  ...
}:

with pkgs; with python3.pkgs; buildPythonPackage rec {
  name = "openlane";

  version_file = builtins.readFile ./openlane/__version__.py;
  version_list = builtins.match ''.+''\n__version__ = "([^"]+)"''\n.+''$'' version_file;
  version = builtins.head version_list;

  src = gitignore-src.gitignoreSource ./.;
  
  doCheck = false;

  propagatedBuildInputs = [
    # Tools
    openroad
    klayout
    yosys
    netgen
    python3
    ruby
    tcl

    # Python
    click
    pyyaml
    rich
    requests
    pcpp
    volare
    tkinter
    magic
  ];
}