# Multi-Macro Top Level Chips

The current methodology views a multi-macro top-level chip using the following hierarchy:

- Chip Core
  - Macros
  - Rest of the Design
- Chip IO
  - IO Pads
  - Power Pads
  - Corner Pads

The current methodology goes as follows:

1. Hardening the hard macros.
2. Hardening the core with the hard macros inside it.
3. Hardening the padframe
4. Hardening the full chip with the padframe.

You already know how to harden individual macros from the previous document. Now, a couple are left.

## Hardening The Core

The chip core would usually have other macros inside it.

In addition to the configuration variables for most cores, you will also need
to set the {var}`::MACROS` configuration object.

The Macro configuration object may look kind of like this:

```json
{
  "MACROS": {
    "spm": {
      "instances": {
        "spm_1": {
          "location": [100, 100],
          "orientation": "N"
        }
      },
      "lib": {
        "*": ["dir::macros/spm/lib/spm.lib"]
      },
      "gds": ["dir::macros/spm/gds/spm.magic.gds"],
      "lef": ["dir::macros/spm/lef/spm.lef"],
      "nl": ["dir::macros/spm/nl/spm.nl.v"],
      "spef": {
        "nom_*": "dir::macros/spm/spef/nom/spm.nom.spef",
        "min_*": "dir::macros/spm/spef/min/spm.min.spef",
        "max_*": "dir::macros/spm/spef/max/spm.max.spef"
      }
    }
  }
}
```

The flow will handle loading any views you specify appropriately: `nl` will be
loaded during STA for example, `lef` during PNR and `gds` during stream-out.

For backwards compatibility with OpenLane 1, there exist a number of variables
that load views indiscriminately, but their use is discouraged:

- {var}`::EXTRA_LIBS`
- {var}`::EXTRA_LEFS`
- {var}`::EXTRA_VERILOG_MODELS`
- {var}`::EXTRA_GDS_FILES`
<!--
TODO:
    * Padframe
    * PDN
-->
