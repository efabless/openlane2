# Universal Flow Configuration Variables
These are flow configuration variables that are used commonly enough that we decided to expose them to all steps and all flows.

Configuration objects, be they JSON, Tcl or directly passed to the Python API, can freely override these values.

```{note}
`?` indicates an optional variable, i.e., a value that may hold a value of `None`.  OpenLane steps are expected to understand that these values are optional and behave accordingly.
```

| Variable Name | Type | Description | Default | Units |
| - | - | - | - | - |
%for var in module.all_variables:
| `${var.name}` | ${var.type_repr_md()} | ${var.desc_repr_md()} | `${var.default}` | ${var.units or ""} |
%endfor
