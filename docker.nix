{
    pkgs ? import ./nix/pkgs.nix,
    openlane-app ? import ./. {}
}:

with pkgs; let
    olenv = python3.withPackages(ps: with ps; [ openlane-app ]);
in dockerTools.streamLayeredImage {
    name = "ghcr.io/efabless/openlane2";
    tag = "${openlane-app.version}";

    contents = [
        # Base OS
        ## GNU
        coreutils-full
        gnugrep
        gnused
        bashInteractive

        ## Networking
        cacert
        iana-etc

        # OpenLane
        olenv

        # Conveniences
        git
        neovim
        delta
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