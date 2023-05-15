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

source $::env(SCRIPTS_DIR)/magic/def/read.tcl

load $::env(DESIGN_NAME)
select top cell

if { $::env(MAGIC_ZEROIZE_ORIGIN) } {
	# assuming scalegrid 1 2
	# makes origin zero based on the minimum enclosing box
	# all shapes will be within the block boundary
	# lower left corner will become (0, 0)
	puts "\[INFO\] Zeroizing Origin"
	set bbox [box values]
	set offset_x [lindex $bbox 0]
	set offset_y [lindex $bbox 1]
	move origin [expr {$offset_x/2}] [expr {$offset_y/2}]
	puts "\[INFO\] Current Box Values: [box values]"
	property FIXED_BBOX [box values]
} else {
	# makes origin zero based on the DIEAREA as defined in the DEF
	# file. Shapes can extend outside the block boundary.
	# magic "lef write -hide" doesn't produce nice results in this
	# case for shapes outside the boundary.
	box [lindex $::env(DIE_AREA) 0]um [lindex $::env(DIE_AREA) 1]um [lindex $::env(DIE_AREA) 2]um [lindex $::env(DIE_AREA) 3]um
	property FIXED_BBOX [box values]
}

select top cell

cellname filepath $::env(DESIGN_NAME) $::env(STEP_DIR)

save


# mark the incoming cell defs as readonly so that their
# GDS data gets copied verbatim
gds readonly true
gds rescale false

if { $::env(MAGIC_GDS_POLYGON_SUBCELLS) } {
	gds polygon subcells true
}
# # Can be obtained from the PDK's .mag files.
# set gds_files_in $::env(CELL_GDS)
# foreach gds_file $gds_files_in {
# 	puts "> gds read $gds_file"
# 	gds read $gds_file
# }
if {  [info exist ::env(MACRO_GDS_FILES)] } {
	set gds_files_in $::env(MACRO_GDS_FILES)
	foreach gds_file $gds_files_in {
		puts "> gds read $gds_file"
		gds read $gds_file
	}
}
if {  [info exist ::env(EXTRA_GDS_FILES)] } {
	set gds_files_in $::env(EXTRA_GDS_FILES)
	foreach gds_file $gds_files_in {
		puts "> gds read $gds_file"
		gds read $gds_file
	}
}

load $::env(DESIGN_NAME)

# if { $::env(MAGIC_GDS_FLATTEN) } {
# 	puts "Flattening cell"
# 	flatten top cell
# }

select top cell

if {  $::env(MAGIC_DISABLE_CIF_INFO) } {
	cif *hier write disable
	cif *array write disable
}

gds nodatestamp yes

if { $::env(MAGIC_GDS_ALLOW_ABSTRACT) } {
	gds abstract allow
}

gds write $::env(SAVE_MAG_GDS)
puts "\[INFO\] GDS Write Complete"

exit 0
