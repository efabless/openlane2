{
  nixConfig = {
    extra-substituters = [
      "https://openlane.cachix.org"
    ];
    extra-trusted-public-keys = [
      "openlane.cachix.org-1:qqdwh+QMNGmZAuyeQJTH9ErW57OWSvdtuwfBKdS254E="
    ];
  };

  inputs = {
    nixpkgs.url = github:nixos/nixpkgs/nixos-23.11;
    flake-compat.url = "https://flakehub.com/f/edolstra/flake-compat/1.tar.gz";
  };

  outputs = {
    self,
    nixpkgs,
    ...
  }: {
    # Helper functions
    forAllSystems = function:
      nixpkgs.lib.genAttrs [
        "x86_64-linux"
        "aarch64-linux"
        "x86_64-darwin"
        "aarch64-darwin"
      ] (
        system:
          function (import nixpkgs {
            inherit system;
            overlays = [
              (import ./nix/overlay.nix)
            ];
          })
      );

    createOpenLaneShell = import ./nix/create-shell.nix;

    # Outputs
    packages = self.forAllSystems (pkgs: let
      callPackage = pkgs.lib.callPackageWith (pkgs // self.packages.${pkgs.system});
      callPythonPackage = pkgs.lib.callPackageWith (pkgs // pkgs.python3.pkgs // self.packages.${pkgs.system});
    in
      rec {
        ioplace-parser = callPackage ./nix/ioplace-parser.nix {};
        libparse = callPackage ./nix/libparse.nix {};
        netgen = callPackage ./nix/netgen.nix {};
        magic = callPackage ./nix/magic.nix {};
        klayout = callPackage ./nix/klayout.nix {};
        klayout-pymod = callPackage ./nix/klayout-pymod.nix {};
        opensta = callPackage ./nix/opensta.nix {};
        openroad-abc = callPackage ./nix/openroad-abc.nix {};
        openroad = callPackage ./nix/openroad.nix {};
        openlane = callPythonPackage ./default.nix {};
        surelog = callPackage ./nix/surelog.nix {};
        verilator = callPackage ./nix/verilator.nix {};
        volare = callPackage ./nix/volare.nix {};
        yosys-abc = callPackage ./nix/yosys-abc.nix {};
        yosys = callPackage ./nix/yosys.nix {};
        yosys-sby = callPackage ./nix/yosys-sby.nix {};
        yosys-eqy = callPackage ./nix/yosys-eqy.nix {};
        yosys-lighter = callPackage ./nix/yosys-lighter.nix {};
        yosys-synlig-sv = callPackage ./nix/yosys-synlig-sv.nix {};
        default = openlane;
      }
      // (pkgs.lib.optionalAttrs (pkgs.system == "x86_64-linux") {yosys-ghdl = callPackage ./nix/yosys-ghdl.nix {};})
      // (pkgs.lib.optionalAttrs (pkgs.stdenv.isLinux) {openlane-docker = callPackage ./nix/docker.nix {};}));

    devShells = self.forAllSystems (
      pkgs:
        self.createOpenLaneShell {pkgs = pkgs // self.packages.${pkgs.system};}
    );
  };
}
