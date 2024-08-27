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
    nix-eda.url = github:efabless/nix-eda/python_cleanup;
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
  }: {
    # Common
    input-overlays = [
      (import ./nix/overlay.nix)
      (devshell.overlays.default)
    ];

    # Helper functions
    createOpenLaneShell = import ./nix/create-shell.nix;

    # Outputs
    packages =
      nix-eda.forAllSystems {
        current = self;
        withInputs = [nix-eda ioplace-parser libparse volare];
      } (util:
        with util;
          rec {
            mdformat = pkgs.python3.pkgs.mdformat.overridePythonAttrs (old: {
              patches = [
                ./nix/patches/mdformat/donns_tweaks.patch
              ];
              doCheck = false;
            });
            colab-env = callPackage ./nix/colab-env.nix {};
            opensta = callPackage ./nix/opensta.nix {};
            openroad-abc = callPackage ./nix/openroad-abc.nix {};
            openroad = callPythonPackage ./nix/openroad.nix {
              inherit (nix-eda) buildPythonEnvForInterpreter;
            };
            openlane = callPythonPackage ./default.nix {};
            sphinx-tippy = callPythonPackage ./nix/sphinx-tippy.nix {};
            sphinx-subfigure = callPythonPackage ./nix/sphinx-subfigure.nix {};
            default = openlane;
          }
          // (pkgs.lib.optionalAttrs (pkgs.stdenv.isLinux) {openlane-docker = callPackage ./nix/docker.nix {createDockerImage = nix-eda.createDockerImage;};}));

    devShells = nix-eda.forAllSystems {withInputs = [self devshell nix-eda ioplace-parser libparse volare];} (
      util:
        with util; rec {
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
