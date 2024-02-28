# Frequently-Asked Questions (FAQ)

```{contents}
:local:
:class: this-will-duplicate-information-and-it-is-still-useful-here
```

## General

(faq-openlane-vs-openroad)=

### How is OpenLane different from OpenROAD?

OpenROAD is one of many utilities used by OpenLane, which integrates it and many
other tools in order to achieve a full RTL-to-GDSII flow.

OpenROAD is primarily developed by The OpenROAD Project, which involves many
corporations and academic institutions (primarily the University of California,
San Diego, Parallax Software, and Precision Innovations). OpenLane, on the other
hand, is primarily developed by Efabless Corporation.

The two projects are affiliated but are otherwise distinct and are managed by
different teams.

(faq-proprietary-pdks)=

### Can I use OpenLane with my (company's) proprietary PDK?

In general, yes, but you would have to create OpenLane configuration files for
said PDK. See {ref}`porting-pdks` for more info.

(faq-silicon-proven)=

### Is OpenLane silicon-proven?

OpenLane 1.0 has been used for countless verified tapeouts, including more or
less every open-source design on the Google MPW shuttles.

OpenLane 2.0 is relatively less battle-tested but was used for TinyTapeout 3.5.

(faq-comparison)=

### Why should I use OpenLane over other open-source RTL-to-GDS-II flows?

| Point of Comparison | [OpenROAD Flow Scripts](https://github.com/The-OpenROAD-Project/OpenROAD-Flow-Scripts) | [SiliconCompiler](https://github.com/siliconcompiler/siliconcompiler) | OpenLane \<2.0 | OpenLane ≥2 |
| - | - | - | - | - |
| Architecture | Monolithic | Plugin-based | Monolithic | Plugin-based |
| Configuration | Tcl Files | Python Files | JSON/Tcl Files | JSON/Tcl/Python Files |
| Programming Language | GNU Make | Python | Tcl | Type-checked Python |
| Maintainer | The OpenROAD Project | ZeroASIC | Efabless | Efabless |
| Dependencies | Separate (Build Scripts) | Separate (Build Scripts) | Bundled | Bundled  |
| Cloud Service | No | Yes | No | No (Planned) |
| Proprietary Tool Support | No | Yes | No | Yes (with Plugins) |
| Pre-built Binaries | `.deb` (x86-64) | N/A | Docker (x86-64, ARM64) | * Natively through [Nix](https://nixos.org): Linux and macOS (x86-64, ARM64) <br /> * Docker (x86-64, ARM64)|
| Open-Source PDK Support | `sky130`, `gf180mcu`, `nangate45`, `asap7`| `sky130`, `gf180mcu`, `asap7` | `sky130`, `gf180mcu` | `sky130`, `gf180mcu` |
| Community Examples | Limited | Limited | [9+ public multi-project wafer shuttles](https://platform.efabless.com/projects/public) | Backwards Compatible with OL1 Examples |

## Setup

(faq-wsl)=

### Why does running OpenLane on Windows require the Windows Subsystem for Linux (WSL)?

In short, a lot of the open-source EDA tools OpenLane relies on presume a
Linux-based environment, so they would be non-trivial to port to Windows as we'd
have to make sure every tool both compiles *and* behaves as expected on Windows.

(faq-nix)=

### Why do you use Nix?

{term}`Nix` allows us to create a near-perfectly reproducible environment on
macOS and all Linux distributions with just a single set of scripts, and the
rich community ecosystem surrounding it also enables us to distribute these
environments in their entirety to end-users.

Similar to Docker, this mostly eliminates variables related to the user's
environment, although unlike Docker, it maintains integration with the user's
filesystem, doesn't add a virtualization penalty on macOS, and does not require
the entire image to be re-downloaded every time an update occurs.
