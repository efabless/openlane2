{
    pkgs ? import ./nix/pkgs.nix,
    openlane-app ? import ./. {}
}:

with pkgs; let olenv = python3.withPackages(ps:
    with ps; [ openlane-app ]
); in dockerTools.streamLayeredImage {
    name = "donnio/openlane";
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
    ];

    created = "now";
    config.Cmd = [ "/usr/bin/env" "zsh" ];
}

# {
#     pkgs ? import ./nix/pkgs.nix,
#     openlane-app ? import ./. {}
# }:

# with pkgs; let olenv = python3.withPackages(ps:
#     with ps; [ openlane-app ]
# ); in dockerTools.buildImage {
#     name = "efabless/openlane";
#     tag = "${openlane-app.version}";
#     copyToRoot = olenv;

#     created = "now";
#     config.Cmd = [ "/usr/bin/env" "zsh" ];
# }