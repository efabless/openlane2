{
  pkgs ? import ./pkgs.nix
}:

with pkgs; fetchFromGitHub {
  owner = "YosysHQ";
  repo = "abc";
  rev = "a8f0ef2368aa56b3ad20a52298a02e63b2a93e2d";
  sha256 = "sha256-48i6AKQhMG5hcnkS0vejOy1PqFbeb6FpU7Yx0rEvHDI=";
}