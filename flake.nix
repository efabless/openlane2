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
  nixConfig = {
    extra-substituters = [
      "https://openlane.cachix.org"
    ];
    extra-trusted-public-keys = [
      "openlane.cachix.org-1:qqdwh+QMNGmZAuyeQJTH9ErW57OWSvdtuwfBKdS254E="
    ];
  };

  inputs = {
    nix-eda.url = github:efabless/nix-eda/composable_overlays;
    libparse.url = github:efabless/libparse-python;
    ioplace-parser.url = github:efabless/ioplace_parser;
    volare.url = github:efabless/volare;
    devshell.url = github:numtide/devshell;
    flake-compat.url = "https://flakehub.com/f/edolstra/flake-compat/1.tar.gz";
  };

  inputs.libparse.inputs.nixpkgs.follows = "nix-eda/nixpkgs";
  inputs.ioplace-parser.inputs.nixpkgs.follows = "nix-eda/nixpkgs";
  inputs.volare.inputs.nixpkgs.follows = "nix-eda/nixpkgs";
  inputs.devshell.inputs.nixpkgs.follows = "nix-eda/nixpkgs";

  outputs = {
    self,
    nix-eda,
    libparse,
    ioplace-parser,
    volare,
    devshell,
    ...
  }: let
    nixpkgs = nix-eda.inputs.nixpkgs;
    lib = nixpkgs.lib;
  in {
    # Common
    overlays = {
      default = lib.composeManyExtensions [
        (import ./nix/overlay.nix)
        (nix-eda.flakesToOverlay [libparse ioplace-parser volare])
        (
          pkgs': pkgs: let
            callPackage = lib.callPackageWith pkgs';
          in
            {
              colab-env = callPackage ./nix/colab-env.nix {};
              opensta = callPackage ./nix/opensta.nix {};
              openroad-abc = callPackage ./nix/openroad-abc.nix {};
              openroad = callPackage ./nix/openroad.nix {};
            }
            // (lib.optionalAttrs (pkgs.stdenv.isLinux) {openlane-docker = callPackage ./nix/docker.nix {createDockerImage = nix-eda.createDockerImage;};})
        )
        (
          nix-eda.composePythonOverlay (pkgs': pkgs: pypkgs': pypkgs: let
            callPythonPackage = lib.callPackageWith (pkgs' // pkgs'.python3.pkgs);
          in {
            mdformat = pypkgs.mdformat.overridePythonAttrs (old: {
              patches = [
                ./nix/patches/mdformat/donns_tweaks.patch
              ];
              doCheck = false;
            });
            sphinx-tippy = callPythonPackage ./nix/sphinx-tippy.nix {};
            sphinx-subfigure = callPythonPackage ./nix/sphinx-subfigure.nix {};
            yamlcore = callPythonPackage ./nix/yamlcore.nix {};

            # ---
            openlane = callPythonPackage ./default.nix {};
          })
        )
      ];
    };

    # Helper functions
    createOpenLaneShell = import ./nix/create-shell.nix;

    # Packages
    legacyPackages = nix-eda.forAllSystems (
      system:
        import nix-eda.inputs.nixpkgs {
          inherit system;
          overlays = [devshell.overlays.default nix-eda.overlays.default self.overlays.default];
        }
    );

    packages = nix-eda.forAllSystems (
      system: {
        inherit (self.legacyPackages."${system}") colab-env opensta openroad-abc openroad;
        inherit (self.legacyPackages."${system}".python3.pkgs) openlane;
        default = self.legacyPackages."${system}".python3.pkgs.openlane;
      }
    );

    # devshells

    devShells = nix-eda.forAllSystems (
        system: let
          pkgs = self.legacyPackages."${system}";
          callPackage = lib.callPackageWith (pkgs // { inherit (self.legacyPackages."${system}".python3.pkgs) openlane; });
        in {
          default =
            callPackage (self.createOpenLaneShell {
              }) {};
          notebook = callPackage (self.createOpenLaneShell {
            extra-packages = with pkgs; [
              jupyter
            ];
          }) {};
          dev = callPackage (self.createOpenLaneShell {
            extra-packages = with pkgs; [
              jdupes
              alejandra
            ];
            extra-python-packages = with pkgs.python3.pkgs; [
              pyfakefs
              pytest
              pytest-xdist
              pytest-cov
              pillow
              mdformat
              black
              ipython
              tokenize-rt
              flake8
              mypy
              types-deprecated
              types-pyyaml
              types-psutil
              lxml-stubs
            ];
          }) {};
          docs = callPackage (self.createOpenLaneShell {
            extra-packages = with pkgs; [
              jdupes
              alejandra
              imagemagick
              nodejs.pkgs.nodemon
            ];
            extra-python-packages = with pkgs.python3.pkgs; [
              pyfakefs
              pytest
              pytest-xdist
              pillow
              mdformat
              furo
              docutils
              sphinx
              sphinx-autobuild
              sphinx-autodoc-typehints
              sphinx-design
              myst-parser
              docstring-parser
              sphinx-copybutton
              sphinxcontrib-spelling
              sphinxcontrib-bibtex
              sphinx-tippy
              sphinx-subfigure
            ];
          }) {};
        }
    );
  };
}
