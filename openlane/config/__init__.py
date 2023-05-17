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
The Configuration Module

This modules includes various functions for importing and/or generating OpenLane
configuration objects. Configuration objects are the primary input to a flow.
"""
from .builder import ConfigBuilder, InvalidConfig
from .config import Config, StringEnum, ConfigEncoder
from .variable import Variable
from .resolve import Keys
from .macro import Macro, Instance

from .tcleval import env_from_tcl
from .flow import all_variables as universal_flow_config_variables
