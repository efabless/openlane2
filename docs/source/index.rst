The OpenLane Documentation
==========================
OpenLane is a RTL to GDSII infrastructure library based on several components including OpenROAD, Yosys, Magic, Netgen, CVC, SPEF-Extractor, KLayout and a number of custom scripts for design exploration and optimization.

A reference flow performs all ASIC implementation steps from RTL all the way down to GDSII. Currently, it supports both A and B variants of the sky130 and gf180mcu PDKs, and instructions to add support for other (including proprietary) PDKs are documented.

OpenLane abstracts the underlying open source utilities, and allows users to configure all their behavior with just a single configuration file, but also allows for completely custom, Python-based scripts.

Check the sidebar to the left to get started.

.. toctree::
   :glob:

   getting_started/index
   usage/index
   for_developers/index
   reference/index
   additional_material