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
    openlane ? import ./. {},
    name ? "ghcr.io/efabless/openlane2",
    tag-override ? null
}:

with pkgs; dockerTools.buildImage rec {
    inherit name;
    tag = if tag-override == null then "${openlane.version}" else tag-override;

    copyToRoot = pkgs.buildEnv {
        name = "image-root";
        paths = [
            # Base OS
            ## GNU
            coreutils-full
            findutils
            bashInteractive
            gnugrep
            gnused
            which

            ## Networking
            cacert
            iana-etc

            # Conveniences
            git
            neovim
            zsh
            silver-searcher

            # OpenLane
            (python3.withPackages(ps: with ps; [ openlane ]))
        ];

        postBuild = ''
        mkdir -p $out/etc
        cat <<HEREDOC > $out/etc/zshrc
        autoload -U compinit && compinit
        autoload -U promptinit && promptinit && prompt suse && setopt prompt_sp
        autoload -U colors && colors

        export PS1=$'%{\033[31m%}OpenLane Container (${openlane.version})%{\033[0m%}:%{\033[32m%}%~%{\033[0m%}%% '; 
        HEREDOC
        '';
    };

    created = "now";
    config = {
        Cmd = [ "/bin/env" "zsh" ];
        Env = [
            "LANG=C.UTF-8"
            "LC_ALL=C.UTF-8"
            "LC_CTYPE=C.UTF-8"
            "EDITOR=nvim"
            "PYTHONPATH=${openlane.computed_PYTHONPATH}"
            "PATH=${openlane}/bin:${openlane.computed_PATH}/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
        ];
    };
}