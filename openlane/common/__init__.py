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
"""
Common Utilities Module
-----------------------

A number of common utility functions and classes used throughout the codebase.
"""
import os
from concurrent.futures import ThreadPoolExecutor

from .tcl import TclUtils
from .metrics import parse_metric_modifiers, aggregate_metrics
from .design_format import DesignFormat, DesignFormatObject
from .generic_dict import (
    GenericDictEncoder,
    GenericDict,
    GenericImmutableDict,
    copy_recursive,
    is_string,
)
from .misc import (
    idem,
    get_openlane_root,
    get_script_dir,
    get_opdks_rev,
    slugify,
    protected,
    final,
    mkdirp,
    StringEnum,
    Path,
    zip_first,
    format_size,
    format_elapsed_time,
)
from .toolbox import Toolbox
from .drc import DRC, Violation


## TPE

TPE = ThreadPoolExecutor(max_workers=os.cpu_count())


def set_tpe(tpe: ThreadPoolExecutor):
    """
    Allows replacing OpenLane's global ``ThreadPoolExecutor`` with a customized
    one.

    :param tpe: The replacemend ThreadPoolExecutor
    """
    global TPE
    TPE = tpe


def get_tpe() -> ThreadPoolExecutor:
    """
    :returns: OpenLane's global ``ThreadPoolExecutor``
    """
    global TPE
    return TPE
