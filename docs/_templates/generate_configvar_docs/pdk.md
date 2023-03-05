# PDK Configuration Variables
These are variables that are to be defined by a process design kit's configuration files. For a PDK to be compatible with OpenLane, all non-`Optional` variables *must* be given a value.

Like with flow configuration variables, configuration objects can freely override these values.

```{note}
`?` indicates an optional variable, i.e., a value that does not need to be implemented by a PDK or an SCL. OpenLane steps are expected to understand that these values are optional and behave accordingly.
```

${"##"} PDK-Level

These are variables that affect the entire PDK.

| Variable Name | Type | Description | Units |
| - | - | - | - |
%for var in module.pdk_variables:
| `${var.name}` | ${var.type_repr_md()} | ${var.desc_repr_md()} | ${var.units or ""} |
%endfor

${"##"} SCL-Level

These are variables that affect a specific standard-cell library.

| Variable Name | Type | Description | Units |
| - | - | - | - |
%for var in module.scl_variables:
| `${var.name}` | ${var.type_repr_md()}  | ${var.desc_repr_md()} | ${var.units or ""} |
%endfor