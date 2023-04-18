# Copyright 2023 Efabless Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from __future__ import annotations

from .flow import Flow
from .sequential import SequentialFlow
from ..steps import KLayout, OpenROAD


@Flow.factory.register()
class OpenInKLayout(SequentialFlow):
    """
    This 'flow' actually just has one step that opens the LEF/DEF from the
    initial state object in KLayout. Fancy that.

    Intended for use with run tags that have already been run with
    another flow, i.e.: ::

      openlane [...]
      openlane --last-run --flow OpenInKLayout [...]
    """

    name = "Opening in KLayout"
    Steps = [KLayout.OpenGUI]


@Flow.factory.register()
class OpenInOpenROAD(SequentialFlow):
    """
    This 'flow' actually just has one step that opens the ODB from
    the initial state object in OpenROAD.

    Intended for use with run tags that have already been run with
    another flow, i.e. ::

      openlane [...]
      openlane --last-run --flow OpenInOpenROAD [...]
    """

    name = "Opening in OpenROAD"

    Steps = [OpenROAD.OpenGUI]
