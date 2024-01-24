# Glossary

```{glossary}

IPVT
    Abbreviation for Interconnect, Process, Voltage, and Temperature, the four
    components of a timing corner.

timing corner
    A set of simulated physical conditions under which timing analysis is
    performed.

Nix
    Nix is a tool that takes a unique approach to package management and system
    configuration. Learn how to make reproducible, declarative and reliable systems.
    For more information visit [https://nixos.org/](https://nixos.org/).

cachix
    Cachix is a service for Nix binary cache hosting.
    For more information visit [https://docs.cachix.org/](https://docs.cachix.org/).

sky130
    The SkyWater Open Source PDK is a collaboration between Google, Efabless and
    SkyWater Technology Foundry to provide a fully open source PDK and related
    resources, which can be used to create manufacturable designs at SkyWater’s
    facility. The SKY130 is a mature 180nm-130nm hybrid technology originally
    developed internally by Cypress Semiconductor before being spun out into
    SkyWater Technology and made accessible to general industry.

PDK
    Stands for Process Design Kit is a set of files used within the
    semiconductor industry to model a fabrication process for the design
    tools used to design an integrated circuit.

RTL
    Stands for Register Transfer Level.
    Register-transfer-level abstraction is used in hardware description languages
    (HDLs) like Verilog and VHDL to create high-level representations of a
    circuit, from which lower-level representations and ultimately actual wiring
    can be derived. Design at the RTL level is typical practice in modern digital
    design.

Variable
    An OpenLane configuration variable. It used to control steps and flows.
    For more information visit {doc}`./reference/flows` and
    {doc}`./reference/step_config_vars`.

GDSII
    Stands for Graphic design system. It is a binary stream format which is the
    de facto industry standard for data exchange of integrated circuit or IC layout
    artwork. It was developed by calma company in 1978. A GDSII file contains planar
    geometric shapes, text labels, and other information about the layout in
    hierarchical form. The data can be used to reconstruct all or part of the
    artwork to be used in sharing layouts, transferring artwork between different
    tools, or creating photomasks. It captures all the layout details needed by
    the manufacturer.

KLayout
    A free and open-source layout viewer and editor. For more information visit
    [https://www.klayout.de/](https://www.klayout.de/).

OpenROAD
    An open-source tool chain for digital SoC layout generation, focusing on the
    RTL-to-GDSII phase of system-on-chip design. It is used for floorplanning,
    design optimizations, placement, CTS(Clock Tree Synthesis) and routing inside
    OpenLane. For more information visit
    [https://openroad.readthedocs.io/en/latest/](https://openroad.readthedocs.io/en/latest/).

Flow
    Flows encapsulates a subroutine that runs multiple steps: either
    synchronously, asynchronously, serially or in any manner.
    For more information visit {py:class}`openlane.flows.Flow`.

Step
    Steps encapsulate a subroutine that acts upon certain classes of formats in
    an input state and returns a new output state with updated design format
    paths and/or metrics.
    For more information visit {py:class}`openlane.steps.Step`.

Metrics
    TODO: Insert description here

DEF
    Stands for Design Exchange Format. A DEF file contains representation of the
    design at any point during the layout process. It contains the
    design-specific information of a circuit.

LEF
    Stands for Library Exchange Format.
    A LEF file contains the abstract view of a digital
    standard cell library’s cells layout. It only gives the idea about the cell
    bounding box (PR boundary), pin position and metal layer information of
    every cell.

CSV
    Stands for Comma-separated Values. It is a text file that represents tabular
    data.

Verilog
    Verilog is a hardware description language (HDL) used to model electronic
    systems. It is most commonly used in the design and verification of digital
    circuits at the register-transfer level (RTL) of abstraction.

Netgen
    A free and open-source tool for running Layout Versus Schematic (LVS).
    For more information visit
    [http://opencircuitdesign.com/netgen/](http://opencircuitdesign.com/netgen/).

SPICE netlist
    SPICE stands for Simulation Program with Integrated Circuit Emphasis.
    A SPICE netlist is a textual representation of a design. Generally,
    it has more information than a Verilog netlist, especially regarding
    parasitics. It is typically used to perform SPICE simulations to verify the
    functionality of the design.
    TODO: check

DRC deck
    TODO: insert description

```
