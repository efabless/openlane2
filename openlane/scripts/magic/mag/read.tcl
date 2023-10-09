addpath [file dirname $::env(CURRENT_MAG)]

#if {  [info exist ::env(MACRO_GDS_FILES)] } {
#	set gds_files_in $::env(MACRO_GDS_FILES)
#	foreach gds_file $gds_files_in {
#		puts "> load $gds_file"
#        load [file rootname [file rootname [file tail $gds_file]]]
#        property LEFview true
#        property GDS_FILE [string map {" " ""} $gds_file]
#        property GDS_START 0
#	}
#}
#if {  [info exist ::env(EXTRA_GDS_FILES)] } {
#	set gds_files_in $::env(EXTRA_GDS_FILES)
#	foreach gds_file $gds_files_in {
#		puts "> load $gds_file"
#        load [file rootname [file rootname [file tail $gds_file]]]
#        property LEFview true
#        property GDS_FILE [string map {" " ""} $gds_file]
#        property GDS_START 0
#	}
#}

load [file rootname [file tail $::env(CURRENT_MAG)]] -dereference
puts "> load [file rootname [file tail $::env(CURRENT_MAG)]] -dereference"
