```{eval-rst}
.. automodule:: ${full_name}
   :members:${ "\n   :imported-members:" if include_imported_members else ""}
   :show-inheritance:
```

%if submodules:
| Submodule | Short Description |
| - | - |
%for name, desc, path in submodules:
| [${name}](${path})  | ${desc}  |  
%endfor
%endif



%if submodules:
```{toctree}
:hidden:
%for name, desc, path in submodules:
${path}
%endfor
```
%endif