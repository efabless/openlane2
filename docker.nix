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
    openlane-app ? import ./. {},
    name ? "ghcr.io/efabless/openlane2",
    tag ? null
}:

with pkgs; let
    olenv = python3Full.withPackages(ps: with ps; [ openlane-app ]);
in dockerTools.streamLayeredImage {
    inherit name;
    tag = if tag == null then "${openlane-app.version}" else tag;

    contents = [
        # Base OS
        ## GNU
        coreutils-full
        bashInteractive
        gnugrep
        gnused
        which

        ## Networking
        cacert
        iana-etc

        # OpenLane
        olenv

        # Conveniences
        git
        neovim
        zsh
    ] ++ openlane-app.propagatedBuildInputs;

    created = "now";
    config = {
        Cmd = [ "/bin/env" "zsh" ];
        Env = [
            "LANG=C.UTF-8"
            "LC_ALL=C.UTF-8"
            "LC_CTYPE=C.UTF-8"
        ];
    };
}