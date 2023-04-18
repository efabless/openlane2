# Pin Placer Configuration Files

If you're using the step [Odb.CustomIOPlacement](./step_config_vars.md#Odb.CustomIOPlacement), the variable `FP_PIN_ORDER_CFG` asks you to create a `.cfg` file that can be used to configure this placement step.

This document outlines the structrure of this file.

## Instructions

The document is a **line-delimited** set of instructions.

## Sections

There are four sections, `N`, `S`, `E`, and `W`, corresponding to the four
cardinal directions.

The sections are marked using a `#` instruction. For example, `#N` marks the
beginning of the section for the pins on the north of the chip.

## Section Minimum Distance

You can set the minimum distance between two pins for a specific section
using the `@min_distance=<distance>` instruction, where the distance is in microns.
Be advised, if this distance is less than the legal minimum distance
for this section, the legal minimum will be used.

## Pins

You can capture one or more pins by writing
a [regular expression](https://en.wikipedia.org/wiki/Regular_expression).

For example, a line with simply `y` will match a pin named y, meanwhile, a line
with `x\[\d+\]` will match `x[0]`, `x[1]`, `x[2]`, ..., `x[10]`, et cetera.

```{warning}
A line with just `x[0]` is still a regular expression which will match the string
`x0`. Be sure to escape all special regex characters: `x\[0\]` would match `x[0]`.
```

## Virtual Pins

You can add one or more "virtual pins" (i.e. pins that occupy a slot but do not
actually exist) using the `$` instruction, where `$1` adds one virtual pin,
`$2` adds two, and so on.


## Example

Here is the `.cfg` file for the SPM design:

```{literalinclude} ../../../designs/spm/pin_order.cfg
```