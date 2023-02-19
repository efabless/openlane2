${"#"} ${short_desc}

%if len(submodules) != 0:
| Submodule | Short Description |
| - | - |
%for name, desc, path in submodules:
| [${name}](${path})  | ${desc}  |  
%endfor
%endif


```{eval-rst}
.. automodule:: ${full_name}
   :members:${ "\n   :imported-members:" if include_imported_members else ""}
   :show-inheritance:
```

%if len(submodules) != 0:
```{toctree}
:hidden:
%for name, desc, path in submodules:
${path}
%endfor
```
%endif