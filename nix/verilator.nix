{
  pkgs ? import ./pkgs.nix,
}:

with pkgs; clangStdenv.mkDerivation rec {
  name = "verilator";
  rev = "23fe5c1b9386228afe80a42b95e91cde8462d1c4";

  src = fetchFromGitHub {
    owner = "verilator";
    repo = "verilator";
    inherit rev;
    sha256 = "sha256-nCYlRR7qvo7W3CCCl5FS1qFO0IMKYWwiysCLcJAE7xI=";
  };

  enableParallelBuilding = true;
  buildInputs = [ perl ];
  nativeBuildInputs = [ makeWrapper flex bison python3 autoconf help2man ];
  nativeCheckInputs = [ which ];

  preConfigure = "autoconf";

  postPatch = ''
    patchShebangs bin/* src/{flexfix,vlcovgen} test_regress/{driver.pl,t/*.pl}
  '';

  postInstall = lib.optionalString stdenv.isLinux ''
    for x in $(ls $out/bin/verilator*); do
      wrapProgram "$x" --set LOCALE_ARCHIVE "${glibcLocales}/lib/locale/locale-archive"
    done
  '';
}
