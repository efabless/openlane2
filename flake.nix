{
  inputs = {
    nixpkgs.url = github:nixos/nixpkgs/nixos-23.11;
    flake-compat.url = "https://flakehub.com/f/edolstra/flake-compat/1.tar.gz";
  };

  outputs = {
    self,
    nixpkgs,
    ...
  }: let
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
              (new: old: {
                # Clang 16 flags "register" as an error by default
                lemon-graph = old.lemon-graph.overrideAttrs (finalAttrs: previousAttrs: {
                  postPatch = "sed -i 's/register //' lemon/random.h";
                });

                # Version mismatch causes OpenROAD to fail otherwise
                spdlog-internal-fmt = old.spdlog.overrideAttrs (finalAttrs: previousAttrs: {
                  cmakeFlags = builtins.filter (flag: (!old.lib.strings.hasPrefix "-DSPDLOG_FMT_EXTERNAL" flag)) previousAttrs.cmakeFlags;
                  doCheck = false;
                });

                # Formatter for the Changelog
                python3 = old.python3.override {
                  packageOverrides = pFinalAttrs: pPreviousAttrs: {
                    mdformat = pPreviousAttrs.mdformat.overrideAttrs (finalAttrs: previousAttrs: {
                      postPatch = ''
                        sed -i 's/primary_marker = "-"/primary_marker = "*"/' src/mdformat/renderer/_util.py
                      '';
                      pytestCheckPhase = "true";
                    });
                  };
                };

                # Platform-specific
                ## Undeclared Platform
                clp =
                  if old.system == "aarch64-linux"
                  then
                    (old.clp.overrideAttrs (finalAttrs: previousAttrs: {
                      meta = {
                        platforms = previousAttrs.meta.platforms ++ [old.system];
                      };
                    }))
                  else (old.clp);

                ## Clang 16's Default is C++17, which cbc does not support
                cbc =
                  if (old.stdenv.isDarwin)
                  then
                    old.cbc.overrideAttrs
                    (finalAttrs: previousAttrs: {
                      configureFlags = previousAttrs.configureFlags ++ ["CXXFLAGS=-std=c++14"];
                    })
                  else (old.cbc);

                ## Clang 16 breaks Jshon
                jshon =
                  if (old.stdenv.isDarwin)
                  then
                    old.jshon.override
                    {
                      stdenv = old.gccStdenv;
                    }
                  else (old.jshon);

                ## Cairo X11 on Mac
                cairo =
                  if (old.stdenv.isDarwin)
                  then
                    (old.cairo.override {
                      x11Support = true;
                    })
                  else (old.cairo);

                ## Alligned alloc not available on the default SDK for x86_64-darwin (10.12!!)
                or-tools =
                  if old.system == "x86_64-darwin"
                  then
                    (old.or-tools.override {
                      stdenv = old.overrideSDK old.stdenv "11.0";
                    })
                  else (old.or-tools);
              })
            ];
          })
      );
  in {
    packages = forAllSystems (pkgs: let
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
      // (pkgs.lib.optionalAttrs (pkgs.system == "x86_64-linux") {yosys-ghdl = callPackage ./nix/yosys-ghdl.nix {};}));

    devShells = forAllSystems (
      pkgs:
        with pkgs;
        with self.packages.${pkgs.system}; let
          openlane-env = (
            python3.withPackages (pp:
              with pp; [
                openlane
                pyfakefs
                pytest
                pillow
                mdformat
              ])
          );
          openlane-env-sitepackages = "${openlane-env}/${openlane-env.sitePackages}";
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
              ++ openlane.includedTools;

            PYTHONPATH = "${openlane-env-sitepackages}"; # Allows venvs to work properly
            shellHook = ''
              export PS1="\n\[\033[1;32m\][nix-shell:\w]\$\[\033[0m\] ";
            '';
          };
        }
    );
  };
}
