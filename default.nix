{ pkgs ? import <nixpkgs> {} }:

with pkgs;
let
  mach-nix = import (pkgs.fetchgit {
    url = "https://github.com/DavHau/mach-nix";
    rev = "70daee1b200c9a24a0f742f605edadacdcb5c998";
    sha256 = "sha256-mia90VYv/YTdWNhKpvwvFW9RfbXZJSWhJ+yva6EnLE8=";
  }) {
    pypiDataRev = "8ac6d2d5521525132c552d4552ba28fe7996b58e";
    pypiDataSha256 = "sha256:1gvxcr8p0bvlb9z19i52kb9m7vjdvj64h05sy7jg0ii99cyfgvxq";
  }; in pkgs.mkShell {
  packages = let
    volare = mach-nix.buildPythonPackage {
      python="python38Full";
      pname="volare";
      version="0.6.2";
      src="https://github.com/efabless/volare/tarball/c9b1f82c18f9af9b3d211287cdf8b36c531a8fc0";
      requirements = ''
      click>=8.0.0,<9
      pyyaml~=5.4.0
      rich>=12,<13
      requests>=2.27.0,<3
      pcpp~=1.30
      '';
    };
    python38-ol = mach-nix.mkPython {
      python = "python38Full";
      requirements = builtins.readFile ./requirements_dev.txt + builtins.readFile ./requirements_lint.txt + builtins.readFile ./requirements.txt;
      packagesExtra = [
        volare
      ];
    }; boost-static = pkgs.boost.override {
      enableShared = false;
      enabledStatic = true;
    }; magic-vlsi = pkgs.magic-vlsi.overrideAttrs (finalAttrs: previousAttrs: {
      version = "8.3.363";
      src = fetchgit {
        url = "https://github.com/RTimothyEdwards/magic";
        rev = "8d08cb2f2f33c79bea478a79543721d476554c78";
        sha256 = "sha256-CY7Wlgvo/b3szVCnJmNaZ6OnXSGlmwyJsPz+cetLIE4=";
        leaveDotGit = true;
      };

      nativeBuildInputs = [ python3 tcsh git gnused ];

      preConfigure = ''
        for file in ./scripts/*; do
          sed -i 's@/bin/csh/@/usr/bin/env tcsh@g' $file
        done
        sed -i '5386,5388d' ./scripts/configure
        patchShebangs ./scripts/*
      '';

    }); netgen = stdenv.mkDerivation {
    
      name = "netgen";
      src = fetchgit {
        url = "https://github.com/donn/netgen";
        rev = "c10f8efd7dc1a5a1c1330784765d5a38cc22cd2d";
        sha256 = "sha256-WGWnIWL//q7z5HmJ1JpSK6QhNM+X7iWNcDzQpL5CbYc=";
      };

      configureFlags = [
        "--with-tk=${tk}"
        "--with-tcl=${tcl}"
      ];

      buildInputs = [
        tcl
        tk
        m4
        python3Full
      ];

      nativeBuildInputs = [
        clang
        clang-tools
      ];

    }; openroad = let revision = "c295b08a99aacb6147b9c51104627e78ac3859e3"; in stdenv.mkDerivation {
      
      name = "openroad";
      src = fetchgit {
        url = "https://github.com/The-OpenROAD-Project/OpenROAD";
        rev = "${revision}";
        sha256 = "sha256-7TaIz12WX6wvZN+Z+IFZh55zWtMV7ER7G5yGefR5n6I=";
        fetchSubmodules = true;
      };

      preConfigure = ''
        sed -i "s/GITDIR-NOTFOUND/${revision}/" ./cmake/GetGitRevisionDescription.cmake
        patchShebangs ./etc/find_messages.py
      '';

      buildInputs = [
        eigen
        spdlog
        tcl
        tk
        python3Full
        readline
        libffi
        qt6.full
        
        # ortools
        re2
        glpk
        zlib
        clp
        cbc
        lemon-graph
        or-tools
      ];

      nativeBuildInputs = [
        boost-static
        swig
        clang
        clang-tools
        pkg-config
        cmake
        gnumake
        flex
        bison
      ];
    }; in [
      # Requirements
      git
      clang
      clang-tools
      gnumake
      xz

      python38-ol

      # Conveniences
      neovim
      delta
      zsh

      # Tools
      klayout

      ## Customized
      yosys
      openroad
      magic-vlsi
      netgen
    ];

}