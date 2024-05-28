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
  extra-packages ? [],
  extra-python-packages ? [],
  openlane-plugins ? [],
  numtide-devshell ? false,
}: ({
  lib,
  openlane,
  git,
  zsh,
  delta,
  neovim,
  gtkwave,
  coreutils,
  graphviz,
  python3,
  mkShell,
  devshell,
}: let
  openlane-env = (
    python3.withPackages (pp:
      with pp;
        [
          openlane
        ]
        ++ extra-python-packages
        ++ openlane-plugins)
  );
  openlane-env-sitepackages = "${openlane-env}/${openlane-env.sitePackages}";
  pluginIncludedTools = lib.lists.flatten (map (n: n.includedTools) openlane-plugins);
  prompt = ''\[\033[1;32m\][nix-shell:\w]\$\[\033[0m\] '';
  packages =
    [
      openlane-env

      # Conveniences
      git
      zsh
      delta
      neovim
      gtkwave
      coreutils
      graphviz
    ]
    ++ extra-packages
    ++ openlane.includedTools
    ++ pluginIncludedTools;
in
  if numtide-devshell
  then
    devshell.mkShell {
      devshell.packages = packages;
      env = [
        {
          name = "PYTHONPATH";
          value = "${openlane-env-sitepackages}";
        }
      ];
      devshell.interactive.PS1 = {
        text = ''PS1="${prompt}"'';
      };
      motd = "";
    }
  else
    mkShell {
      name = "openlane-shell";

      propagatedBuildInputs = packages;

      PYTHONPATH = "${openlane-env-sitepackages}"; # Allows venvs to work properly
      shellHook = ''
        export PS1="\n${prompt}";
      '';
    })
