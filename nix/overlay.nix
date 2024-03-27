new: old: {
  # Clang 16 flags "register" as an error by default
  lemon-graph = old.lemon-graph.overrideAttrs (finalAttrs: previousAttrs: {
    postPatch = "sed -i 's/register //' lemon/random.h";
  });

  # Version mismatch causes OpenROAD to fail otherwise
  spdlog-internal-fmt = old.spdlog.overrideAttrs (finalAttrs: previousAttrs: {
    cmakeFlags = builtins.filter (flag: (!old.lib.strings.hasPrefix "-DSPDLOG_FMT_EXTERNAL" flag)) previousAttrs.cmakeFlags;
    doCheck = false;
  });

  # Formatter for the Changelog
  python3 = old.python3.override {
    packageOverrides = pFinalAttrs: pPreviousAttrs: {
      mdformat = pPreviousAttrs.mdformat.overrideAttrs (finalAttrs: previousAttrs: {
        patches = [
          ./patches/mdformat/donns_tweaks.patch
        ];
        pytestCheckPhase = "true";
      });
    };
  };

  # Platform-specific
  ## Undeclared Platform
  clp =
    if old.system == "aarch64-linux"
    then
      (old.clp.overrideAttrs (finalAttrs: previousAttrs: {
        meta = {
          platforms = previousAttrs.meta.platforms ++ [old.system];
        };
      }))
    else (old.clp);

  ## Clang 16's Default is C++17, which cbc does not support
  cbc =
    if (old.stdenv.isDarwin)
    then
      old.cbc.overrideAttrs
      (finalAttrs: previousAttrs: {
        configureFlags = previousAttrs.configureFlags ++ ["CXXFLAGS=-std=c++14"];
      })
    else (old.cbc);

  ## Clang 16 breaks Jshon
  jshon =
    if (old.stdenv.isDarwin)
    then
      old.jshon.override
      {
        stdenv = old.gccStdenv;
      }
    else (old.jshon);

  ## Cairo X11 on Mac
  cairo =
    if (old.stdenv.isDarwin)
    then
      (old.cairo.override {
        x11Support = true;
      })
    else (old.cairo);

  ## Alligned alloc not available on the default SDK for x86_64-darwin (10.12!!)
  or-tools =
    if old.system == "x86_64-darwin"
    then
      (old.or-tools.override {
        stdenv = old.overrideSDK old.stdenv "11.0";
      })
    else (old.or-tools);
}
