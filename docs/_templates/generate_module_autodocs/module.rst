``${full_name}`` API
================================================================================

.. automodule:: ${full_name}
  :show-inheritance:
  :members:
  :member-order: bysource
  ${ ":imported-members:" if include_imported_members else ""}

%if submodules:
.. toctree::
  :maxdepth: 1
  :titlesonly:
  :hidden:

%for name, desc, path in submodules:
  ${path}
%endfor

.. list-table::
  :header-rows: 1
   
  * - Submodule
    - Short Description
%for name, desc, path in submodules:
  * - :doc:`${name} <${path}>`
    - ${desc}
%endfor
%endif