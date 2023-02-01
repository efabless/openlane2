{
  pkgs,
  mach-nix
}:

mach-nix.mkPython {
  requirements =
    builtins.readFile ../requirements_dev.txt +
    builtins.readFile ../requirements.txt
    ;
}