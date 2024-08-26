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
source $::env(SCRIPTS_DIR)/openroad/common/io.tcl
read_current_odb

log_cmd cut_rows\
    -endcap_master $::env(ENDCAP_CELL)\
    -halo_width_x $::env(FP_MACRO_HORIZONTAL_HALO)\
    -halo_width_y $::env(FP_MACRO_VERTICAL_HALO)

# Prune really short rows (<25 sites) so the PDN doesn't scream and complain
## Replace with https://github.com/The-OpenROAD-Project/OpenROAD/issues/5648 when this is available
foreach lib $::libs {
    set current_sites [$lib getSites]
    foreach site $current_sites {
        set name [$site getName]
        set ::sites($name) $site
    }
}

set ::default_site $::sites($::env(PLACE_SITE))
foreach row [$::block getRows] {
    set bbox [$row getBBox]
    set site_count [expr ([$bbox xMax] - [$bbox xMin]) / [$::default_site getWidth]]
    if { $site_count < 25 } {
        odb::dbRow_destroy $row
    }
}

write_views

report_design_area_metrics
