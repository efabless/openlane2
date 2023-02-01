#!/usr/bin/env bash
nix-store --query --references $(nix-instantiate shell.nix) |\
    xargs nix-store --realise | xargs nix-store --query --requisites |\
    cachix push openlane