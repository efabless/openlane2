namespace eval yosys_ol {
    set abc_rs_K    "resub,-K,"
    set abc_rs      "resub"
    set abc_rsz     "resub,-z"
    set abc_rf      "drf,-l"
    set abc_rfz     "drf,-l,-z"
    set abc_rw      "drw,-l"
    set abc_rwz     "drw,-l,-z"
    set abc_rw_K    "drw,-l,-K"
    if { $::env(SYNTH_ABC_LEGACY_REFACTOR) == "1" } {
        set abc_rf      "refactor"
        set abc_rfz     "refactor,-z"
    }
    if { $::env(SYNTH_ABC_LEGACY_REWRITE) == "1" } {
        set abc_rw      "rewrite"
        set abc_rwz     "rewrite,-z"
        set abc_rw_K    "rewrite,-K"
    }
    set abc_b       "balance"

    set abc_resyn2        "${abc_b}; ${abc_rw}; ${abc_rf}; ${abc_b}; ${abc_rw}; ${abc_rwz}; ${abc_b}; ${abc_rfz}; ${abc_rwz}; ${abc_b}"
    set abc_share         "strash; multi,-m; ${abc_resyn2}"
    set abc_resyn2a       "${abc_b};${abc_rw};${abc_b};${abc_rw};${abc_rwz};${abc_b};${abc_rwz};${abc_b}"
    set abc_resyn3        "balance;resub;resub,-K,6;balance;resub,-z;resub,-z,-K,6;balance;resub,-z,-K,5;balance"
    set abc_resyn2rs      "${abc_b};${abc_rs_K},6;${abc_rw};${abc_rs_K},6,-N,2;${abc_rf};${abc_rs_K},8;${abc_rw};${abc_rs_K},10;${abc_rwz};${abc_rs_K},10,-N,2;${abc_b},${abc_rs_K},12;${abc_rfz};${abc_rs_K},12,-N,2;${abc_rwz};${abc_b}"

    set abc_choice        "fraig_store; ${abc_resyn2}; fraig_store; ${abc_resyn2}; fraig_store; fraig_restore"
    set abc_choice2      "fraig_store; balance; fraig_store; ${abc_resyn2}; fraig_store; ${abc_resyn2}; fraig_store; ${abc_resyn2}; fraig_store; fraig_restore"

    set abc_map_old_cnt			"map,-p,-a,-B,0.2,-A,0.9,-M,0"
    set abc_map_old_dly         "map,-p,-B,0.2,-A,0.9,-M,0"
    set abc_retime_area         "retime,-D,{D},-M,5"
    set abc_retime_dly          "retime,-D,{D},-M,6"
    set abc_map_new_area        "amap,-m,-Q,0.1,-F,20,-A,20,-C,5000"

    set abc_area_recovery_1       "${abc_choice}; map;"
    set abc_area_recovery_2       "${abc_choice2}; map;"

    set map_old_cnt			    "map,-p,-a,-B,0.2,-A,0.9,-M,0"
    set map_old_dly			    "map,-p,-B,0.2,-A,0.9,-M,0"
    set abc_retime_area   	"retime,-D,{D},-M,5"
    set abc_retime_dly    	"retime,-D,{D},-M,6"
    set abc_map_new_area  	"amap,-m,-Q,0.1,-F,20,-A,20,-C,5000"

    if { $::env(SYNTH_ABC_BUFFERING) } {
        set max_tr_arg ""
        if { $max_TR != 0 } {
            set max_tr_arg ",-S,${max_TR}"
        }
        set abc_fine_tune		"buffer,-N,${max_FO}${max_tr_arg};upsize,{D};dnsize,{D}"
    } elseif {$::env(SYNTH_SIZING)} {
        set abc_fine_tune       "upsize,{D};dnsize,{D}"
    } else {
        set abc_fine_tune       ""
    }

    set area_scripts [list \
        "+read_constr,${sdc_file};fx;mfs;strash;${abc_rf};${abc_resyn2};${abc_retime_area};scleanup;${abc_choice2};${abc_map_new_area};retime,-D,{D};&get,-n;&st;&dch;&nf;&put;${abc_fine_tune};stime,-p;print_stats -m" \
        \
        "+read_constr,${sdc_file};fx;mfs;strash;${abc_rf};${abc_resyn2};${abc_retime_area};scleanup;${abc_choice2};${abc_map_new_area};${abc_choice2};${abc_map_new_area};retime,-D,{D};&get,-n;&st;&dch;&nf;&put;${abc_fine_tune};stime,-p;print_stats -m" \
        \
        "+read_constr,${sdc_file};fx;mfs;strash;${abc_rf};${abc_choice2};${abc_retime_area};scleanup;${abc_choice2};${abc_map_new_area};${abc_choice2};${abc_map_new_area};retime,-D,{D};&get,-n;&st;&dch;&nf;&put;${abc_fine_tune};stime,-p;print_stats -m" \
        \
        "+read_constr,${sdc_file};strash;dch;map -B 0.9;topo;stime -c;buffer -c -N ${max_FO};upsize -c;dnsize -c;stime,-p;print_stats -m"]

    set delay_scripts [list \
        "+read_constr,${sdc_file};fx;mfs;strash;${abc_rf};${abc_resyn2};${abc_retime_dly}; scleanup;${abc_map_old_dly};retime,-D,{D};&get,-n;&st;&dch;&nf;&put;${abc_fine_tune};stime,-p;print_stats -m" \
        \
        "+read_constr,${sdc_file};fx;mfs;strash;${abc_rf};${abc_resyn2};${abc_retime_dly}; scleanup;${abc_choice2};${abc_map_old_dly};${abc_area_recovery_2}; retime,-D,{D};&get,-n;&st;&dch;&nf;&put;${abc_fine_tune};stime,-p;print_stats -m" \
        \
        "+read_constr,${sdc_file};fx;mfs;strash;${abc_rf};${abc_resyn2};${abc_retime_dly}; scleanup;${abc_choice};${abc_map_old_dly};${abc_area_recovery_1}; retime,-D,{D};&get,-n;&st;&dch;&nf;&put;${abc_fine_tune};stime,-p;print_stats -m" \
        \
        "+read_constr,${sdc_file};fx;mfs;strash;${abc_rf};${abc_resyn2};${abc_retime_area};scleanup;${abc_choice2};${abc_map_new_area};${abc_choice2};${abc_map_old_dly};retime,-D,{D};&get,-n;&st;&dch;&nf;&put;${abc_fine_tune};stime,-p;print_stats -m" \
        \
        "+read_constr,${sdc_file};&get -n;&st;&dch;&nf;&put;&get -n;&st;&syn2;&if -g -K 6;&synch2;&nf;&put;&get -n;&st;&syn2;&if -g -K 6;&synch2;&nf;&put;&get -n;&st;&syn2;&if -g -K 6;&synch2;&nf;&put;&get -n;&st;&syn2;&if -g -K 6;&synch2;&nf;&put;&get -n;&st;&syn2;&if -g -K 6;&synch2;&nf;&put;buffer -c -N ${max_FO};topo;stime -c;upsize -c;dnsize -c;;stime,-p;print_stats -m"]

    proc get_abc_script {strategy} {
        set strategy_parts [split $strategy]

        proc malformed_strategy {strategy} {
            log -stderr "\[ERROR\] Misformatted SYNTH_STRATEGY (\"$strategy\")."
            log -stderr "\[ERROR\] Correct format is \"DELAY 0-[expr [llength $yosys_ol::delay_scripts]-1]|AREA 0-[expr [llength $yosys_ol::area_scripts]-1]\"."
            exit 1
        }

        if { [llength $strategy_parts] != 2 } {
            malformed_strategy $strategy
        }

        set strategy_type [lindex $strategy_parts 0]
        set strategy_type_idx [lindex $strategy_parts 1]

        if { $strategy_type != "AREA" && $strategy_type != "DELAY" } {
            log -stderr "\[ERROR\] AREA|DELAY tokens not found. ($strategy_type)"
            malformed_strategy $strategy
        }

        if { $strategy_type == "DELAY" && $strategy_type_idx >= [llength $yosys_ol::delay_scripts] } {
            log -stderr "\[ERROR\] strategy index ($strategy_type_idx) is too high."
            malformed_strategy $strategy
        }

        if { $strategy_type == "AREA" && $strategy_type_idx >= [llength $yosys_ol::area_scripts] } {
            log -stderr "\[ERROR\] strategy index ($strategy_type_idx) is too high."
            malformed_strategy $strategy
        }

        if { $strategy_type == "DELAY" } {
            set strategy_script [lindex $yosys_ol::delay_scripts $strategy_type_idx]
        } else {
            set strategy_script [lindex $yosys_ol::area_scripts $strategy_type_idx]
        }
        return $strategy_script
    }

}
