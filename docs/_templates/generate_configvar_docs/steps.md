# Built-in Steps and their Configuration Variables
These steps are included with OpenLane and are used by its various built-in flows.

This page documents these steps, how to get them and their configuration variables (if applicable).

Additionally, the [PDK Configuration Variables](./pdk_config_vars.md) are exposed to all steps.

If you're looking for documentation for the `Step` Python classes themselves, check the API reference [here](./api/steps/index.md).

```{warning}
* Two steps in a given Flow may share a configuration variable name if-and-only-if the variables are otherwise identical, i.e., the name, type, and default value all match. Otherwise, the flow will not compile.
* Some steps have a variable prefixed with `RUN_` that enables or disables said step. This is a vestige from OpenLane 1 and it is recommended to explicitly specify your flow either by using the API or in your JSON configuration file's `meta` object.
```


```{note}
`?` indicates an optional variable, i.e., a value that may hold a value of `None`.  OpenLane steps are expected to understand that these values are optional and behave accordingly.
```

%for category, steps in categories_sorted:
${"##"} ${category}
%for key, step in steps:
${step.get_help_md()}
%endfor
%endfor
