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
  pkgs,
  openlane-plugins ? [],
}:
with pkgs; let
  openlane-env = (
    python3.withPackages (pp:
      with pp;
        [
          openlane
          pyfakefs
          pytest
          pillow
          mdformat
        ]
        ++ openlane-plugins)
  );
  openlane-env-sitepackages = "${openlane-env}/${openlane-env.sitePackages}";
  pluginIncludedTools = lib.lists.flatten (map (n: n.includedTools) openlane-plugins);
in {
  default = mkShell {
    name = "openlane-shell";

    propagatedBuildInputs =
      [
        openlane-env

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
        alejandra
      ]
      ++ openlane.includedTools
      ++ pluginIncludedTools;

    PYTHONPATH = "${openlane-env-sitepackages}"; # Allows venvs to work properly
    shellHook = ''
      export PS1="\n\[\033[1;32m\][nix-shell:\w]\$\[\033[0m\] ";
    '';
  };
}
