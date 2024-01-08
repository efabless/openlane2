# OpenLane Nix Repository
{ pkgs ? import ./pkgs.nix { inherit system; }
, system ? builtins.currentSystem
}:
let
  callPackage = pkgs.lib.callPackageWith (pkgs // self);
  callPythonPackage = pkgs.lib.callPackageWith (pkgs // pkgs.python3.pkgs // self);
  self = {
    nixpkgs = pkgs;
    inherit system;

    # Packages
    ioplace-parser = import ./ioplace-parser.nix { };
    libparse = callPackage ./libparse.nix { };
    netgen = callPackage ./netgen.nix { };
    magic = callPackage ./magic.nix { };
    klayout = callPackage ./klayout.nix { };
    klayout-pymod = callPackage ./klayout-pymod.nix { };
    opensta = callPackage ./opensta.nix { };
    openroad-abc = callPackage ./openroad-abc.nix { };
    openroad = callPackage ./openroad.nix { };
    openlane = callPythonPackage ../. { };
    surelog = callPackage ./surelog.nix { };
    verilator = callPackage ./verilator.nix { };
    volare = callPackage ./volare.nix { };
    yosys-abc = callPackage ./yosys-abc.nix { };
    yosys = callPackage ./yosys.nix { };
    yosys-sby = callPackage ./yosys-sby.nix { };
    yosys-eqy = callPackage ./yosys-eqy.nix { };
    yosys-ghdl = callPackage ./yosys-ghdl.nix { };
    yosys-lighter = callPackage ./yosys-lighter.nix { };
    yosys-synlig-sv = callPackage ./yosys-synlig-sv.nix { };
  };
in
self
