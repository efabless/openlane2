# The OpenLane 2.0.0 BETA Documentation

```{note}
This documentation pertains to the OpenLane 2.0.0 beta release available at
https://github.com/efabless/openlane2. To disambiguate it from the stable
version, the landing page refers to this release as "OpenLane 2."

If you're using the stable version of OpenLane (available at
https://github.com/The-OpenROAD-Project/OpenLane), you'll find the documentation
at https://openlane.readthedocs.io.
```

OpenLane 2 is a RTL to GDSII infrastructure library based on several components
including OpenROAD, Yosys, Magic, KLayout, Netgen and a number of custom scripts
for design exploration and optimization.

A reference flow performs all ASIC implementation steps from RTL all the way down
to GDSII.

OpenLane 2 abstracts the underlying open source utilities, and allows users to configure all their behavior with just a single configuration file, but also allows for completely custom, Python-based scripts.

Currently, OpenLane 2 and its default flow support all variants of the open-source
[Skywater PDK](https://github.com/google/skywater-pdk) and some variants of
the open-source [GlobalFoundries PDK](https://github.com/google/gf180mcu-pdk).
See [Using PDKs](./usage/about_pdks.md) for more info.


Check the sidebar to the left to get started.

```{toctree}
:glob:
:hidden:

getting_started/index
usage/index
reference/index
additional_material
contributors/index
```