{ pkgs ? import ./pkgs.nix }:

with pkgs; let src = fetchFromGitHub { 
  owner = "hercules-ci";
  repo = "gitignore.nix";
  rev = "a20de23b925fd8264fd7fad6454652e142fd7f73";
  sha256 = "sha256-8DFJjXG8zqoONA1vXtgeKXy68KdJL5UaXR8NtVMUbx8=";
}; in import src { inherit (pkgs) lib; }