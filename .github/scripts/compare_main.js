#!/usr/bin/env node
// Copyright 2023 Efabless Corporation
//
// Licensed under the Apache License, Version 2.0(the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
//     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
/**
 * 
 * @param {string} token
 * @returns {string}
 */
function get(token = "") {
    const { spawnSync } = require("child_process");

    let child;
    // Must fit in the body of a comment, try being less verbose
    for (const verbosity of ["CHANGED", "WORSE", "CRITICAL", "NONE"]) {
        child = spawnSync("python3", ["-m", "openlane.common.metrics", "compare-main", "current", "--table-format", verbosity, "--token", token], { encoding: "utf8" });
        if (child.stdout.length < 60000) {
            break;
        }
    }

    let result = "";
    if (child.status != 0) {
        result = "Failed to create report: \n\n```\n" + child.stderr + "\n```";
    } else {
        result = "> To create this report yourself, grab the metrics artifact from the CI run, extract them, and invoke `python3 -m openlane.common.metrics compare-main <path to directory>`.\n\n" + child.stdout;
    }

    return result;
};

module.exports = get;

if (require.main === module) {
    console.log(get(process.argv[2]));
}