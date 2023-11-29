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
 * @param {string} verbosity
 * @param {string} token
 * @returns {string}
 */
function get(verbosity, table_out = null, token = "") {
    const { spawnSync } = require("child_process");

    let tableOutOpts = table_out ? ["--table-out", table_out] : [];

    let child = spawnSync("python3", ["-m", "openlane.common.metrics", "compare-main", "current", "--table-verbosity", verbosity, "--token", token].concat(tableOutOpts), { encoding: "utf8" });

    let result = "";
    if (child.status != 0) {
        throw new Error("Failed to create report: \n\n```\n" + child.stderr + "\n```");
    } else {
        result = "> To create this report yourself, grab the metrics artifact from the CI run, extract them, and invoke `python3 -m openlane.common.metrics compare-main <path to directory>`.\n\n" + child.stdout;
    }

    return result.trim();
};

module.exports = get;

if (require.main === module) {
    console.log(get("ALL", null, process.argv[2]));
}