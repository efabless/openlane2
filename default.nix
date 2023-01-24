{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  packages = with pkgs; let
    boost-static = pkgs.boost.override {
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

    }); openroad = stdenv.mkDerivation {
      
      name = "openroad";

      src = fetchgit {
        url = "https://github.com/The-OpenROAD-Project/OpenROAD";
        rev = "c295b08a99aacb6147b9c51104627e78ac3859e3";
        sha256 = "sha256-mfU9SW91CpZ6+FkT57nsHLcTuJmi9gyVll6sH0LptLg=";
        fetchSubmodules = true;
        leaveDotGit = true;
      };

      preConfigure = ''
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
      neovim
      git
      clang
      clang-tools
      gnumake
      python3Full
      xz

      openroad
      magic-vlsi
      yosys
    ];

}