# Copyright 2020 Efabless Corporation
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
drc off
crashbackups stop

source $::env(SCRIPTS_DIR)/magic/mag/read.tcl

select top cell
expand
if {  $::env(MAGIC_DISABLE_CIF_INFO) } {
	cif *hier write disable
	cif *array write disable
}
gds write $::env(SAVE_MAG_GDS)

exit 0
