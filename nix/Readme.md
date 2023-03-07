# OpenLane Nix Packages
These are Nix derivations for various OpenLane utilities.

There are some conventions in use here:
* All packages must accept a `pkgs` argument with a default value of `import ./pkgs.nix`.
    * https://nix.dev/tutorials/towards-reproducibility-pinning-nixpkgs
* All packages must use `fetchFromGitHub` with a commit-based `rev` and `sha256`, in addition to using `name` instead of `pname`.
    * We don't keep track of versions, only commits, so it doesn't matter. In other words, `version` should (in most cases) be `null`.
    * This will ultimately help us implement automatic tool update checks.