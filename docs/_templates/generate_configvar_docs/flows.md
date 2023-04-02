# Built-in Flows and their Configuration Variables
These flows come included with OpenLane. They use a variety of built-in steps to either provide a general RTL-to-GDSII flow or more specific niches.

Each Flow's list configuration variables is essentially a sum of its included steps and the "Universal" Flow Confiuguration Variables.

Additionally, the [PDK Configuration Variables](./pdk_config_vars.md) are exposed to all steps.

If you're looking for documentation for the `Flow` Python classes themselves, check the API reference [here](./api/flows/index.md).

${"##"} Flows

%for flow in flows:
${flow.get_help_md()}
%endfor


${"##"} Universal Flow Configuration Variables

These are flow configuration variables that are used commonly enough that we decided to expose them to all steps and all flows.

Configuration objects, be they JSON, Tcl or directly passed to the Python API, can freely override these values.

```{note}
`?` indicates an optional variable, i.e., a value that may hold a value of `None`.  OpenLane steps are expected to understand that these values are optional and behave accordingly.
```

| Variable Name | Type | Description | Default | Units |
| - | - | - | - | - |
%for var in module.all_variables:
| <a name="${var.name}"></a>`${var.name}` | ${var.type_repr_md()} | ${var.desc_repr_md()} | `${var.default}` | ${var.units or ""} |
%endfor
