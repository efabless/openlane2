(nix-based-installation)=

# Nix-based Installation

Nix is a package manager for Linux and macOS allowing for _cachable_ and _reproducible_ builds, and is the primary build system for OpenLane.

Nix offers:

- Support for Mac, Linux, and the Windows Subsystem for Linux on both x86-64 and aarch64
- **Filesystem integration:** No need to worry about which folders are being
  mounted
- **Smaller deltas:** if one tool is updated, you do not need to re-download
  everything
- **Dead-simple customization:** You can modify any tool versions and/or any
  OpenLane code and all you need to do is re-invoke `nix-shell`. Nix's smart
  cache-substitution feature will automatically figure out whether your build is
  cached or not, and if not, will automatically attempt to build any tools that
  have been changed.

```{tip}
On Windows, you can use the Windows Subsystem for Linux, which we provide
instructions for below.
```

```{toctree}
:maxdepth: 1

installation_win
installation_macos
installation_linux
```
