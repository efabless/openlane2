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
  openlane ? import ./. { inherit pkgs; },
  openlane-plugins ? [],
}:

with pkgs; let
  pluginIncludedTools = lib.lists.flatten (map (n: n.includedTools) openlane-plugins)
  
; in mkShell {
  name = "openlane-shell";

  propagatedBuildInputs = [
    (python3.withPackages(pp: with pp; [
      openlane
      pyfakefs
      pytest
      pillow
      mdformat
    ] ++ openlane-plugins ))

    # Conveniences
    git
    zsh
    delta
    jdupes
    neovim
    gtkwave
    coreutils

    # Docs + Testing
    jupyter
    graphviz
    nodejs
    yarn
  ] ++ openlane.includedTools ++ pluginIncludedTools;

  PYTHONPATH = openlane.computed_PYTHONPATH;
}