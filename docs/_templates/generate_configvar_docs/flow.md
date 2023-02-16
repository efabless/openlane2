# PDK Configuration Variables
These are variables that affect various Steps' behavior. They typically have default values

```{note}
`?` indicates an optional variable, i.e., a value that may hold a value of `None`.
```

| Variable Name | Type | Default | Description | Units |
| - | - | - | - | - |
%for var in module.flow_variables:
| `${var.name}` | ${type_pretty(var)} | `${var.default}` | ${desc_clean(var.description)} | ${var.doc_units or ""} |
%endfor
