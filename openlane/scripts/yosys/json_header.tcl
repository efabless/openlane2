# Copyright 2020-2023 Efabless Corporation
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
yosys -import
source $::env(SCRIPTS_DIR)/yosys/common.tcl

source $::env(_DEPS_SCRIPT)

yosys_ol::read_verilog_files $::env(DESIGN_NAME)
hierarchy -check -top $::env(DESIGN_NAME) -nokeep_prints -nokeep_asserts
yosys rename -top $::env(DESIGN_NAME)
yosys proc
flatten
opt_clean -purge
json -o $::env(SAVE_JSON_HEADER)
