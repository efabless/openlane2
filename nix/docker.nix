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
  dockerTools,
  system,
  pkgs,
  lib,
  python3,
  openlane,
  git,
  neovim,
  zsh,
  silver-searcher,
  coreutils,
}: let
  # # We're fetchurl-ing this one so we don't want to use a fixed-output derivation
  # # like fetchFromGitHub
  # # See https://nixos.org/manual/nix/stable/language/import-from-derivation
  # nix-docker-image-script = builtins.fetchurl {
  #   url = "https://raw.githubusercontent.com/NixOS/nix/master/docker.nix";
  #   sha256 = "sha256:0kpj0ms09v7ss86cayf3snpsl6pnjgjzk5wcsfp16ggvr2as80ai";
  # };
  openlane-env = python3.withPackages (ps: with ps; [openlane]);
  openlane-env-sitepackages = "${openlane-env}/${openlane-env.sitePackages}";
  openlane-env-bin = "${openlane-env}/bin";
in (import ./create-docker.nix {
  inherit pkgs;
  inherit lib;
  name = "openlane";
  tag = "tmp-${system}";
  extraPkgs = with dockerTools; [
    git
    zsh
    neovim
    silver-searcher

    openlane-env
  ];
  nixConf = {
    extra-experimental-features = "nix-command flakes repl-flake";
  };
  maxLayers = 2;
  channelURL = "https://nixos.org/channels/nixos-23.11";

  image-created = "now";
  image-extraCommands = ''
    mkdir -p ./etc
    cat <<HEREDOC > ./etc/zshrc
    autoload -U compinit && compinit
    autoload -U promptinit && promptinit && prompt suse && setopt prompt_sp
    autoload -U colors && colors

    export PS1=$'%{\033[31m%}OpenLane Container (${openlane.version})%{\033[0m%}:%{\033[32m%}%~%{\033[0m%}%% ';
    HEREDOC
  '';
  image-config-cmd = ["${zsh}/bin/zsh"];
  image-config-extra-env = [
    "LANG=C.UTF-8"
    "LC_ALL=C.UTF-8"
    "LC_CTYPE=C.UTF-8"
    "EDITOR=nvim"
    "PYTHONPATH=${openlane-env-sitepackages}"
    "TMPDIR=/tmp"
  ];
  image-config-extra-path = [
    "${openlane-env-bin}"
    "${openlane.computed_PATH}"
  ];
})
