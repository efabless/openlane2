# Built-in Steps and their Configuration Variables
These steps are included with OpenLane and are used by its various built-in flows.

This page documents these steps, how to get them and their configuration variable.

```{warning}
* Two steps in a given Flow may share a configuration variable name if-and-only-if the variables are otherwise identical, i.e., the name, type, default value and description all match letter-for-letter. Otherwise, the flow will not compile.
* Some steps have a variable prefixed with `RUN_` that enables or disables said step. This is a vestige from OpenLane 1 and it is recommended to explicitly specify your flow either by using the API or in your JSON configuration file's `meta` object.
```


```{note}
`?` indicates an optional variable, i.e., a value that may hold a value of `None`.  OpenLane steps are expected to understand that these values are optional and behave accordingly.
```

<%
by_category = {}
for step in factory.list():
    category, name = step.split(".")
    if by_category.get(category) is None:
        by_category[category] = []
    by_category[category].append((step, factory.get(step)))

misc = ("Misc", by_category["Misc"])
del by_category["Misc"]
%>
%for category, steps in list(sorted(by_category.items(), key=lambda c: c[0])) + [misc]:
${"##"} ${category}
%for key, step in sorted(steps, key=lambda t: t[0]):
${"###"} ${step._get_desc()}
* Get via `Step.get("${key}")`.

${step.__doc__ or ""}

| Variable Name | Type | Default | Description | Units |
| - | - | - | - | - |
%for var in step.config_vars:
| `${var.name}` | ${type_pretty(var)} | `${var.default}` | ${desc_clean(var.description)} | ${var.doc_units or ""} |
%endfor


%endfor
%endfor
