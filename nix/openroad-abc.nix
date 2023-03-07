{
  pkgs ? import ./pkgs.nix
}:

with pkgs; abc-verifier.overrideAttrs (finalAttrs: previousAttrs: {
name = "or-abc";

src = fetchFromGitHub {
  owner = "The-OpenROAD-Project";
  repo = "abc";
  rev = "95b3543e928640dfa25f9e882e72a090a8883a9c";
  sha256 = "sha256-U1E9wvEK5G4zo5Pepvsb5q885qSYyixIViweLacO5+U=";
};

installPhase = ''
  mkdir -p $out/bin
  mv abc $out/bin

  mkdir -p $out/lib
  mv libabc.a $out/lib

  mkdir -p $out/include
  for header in $(find  ../src | grep "\\.h$" | sed "s@../src/@@"); do
  header_tgt=$out/include/$header
  header_dir=$(dirname $header_tgt) 
  mkdir -p $header_dir
  cp ../src/$header $header_tgt
  done
'';
})